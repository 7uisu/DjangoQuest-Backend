# users/admin_views.py
import csv
from io import StringIO

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser
from django.contrib.auth import get_user_model
from django.db.models import Q, Avg, Count
from django.http import HttpResponse
from datetime import datetime
from .models import Classroom, Profile, AuditLog, EducatorAccessCode
from feedback.models import Feedback
from feedback.serializers import FeedbackListSerializer
from announcements.models import Announcement
from announcements.serializers import AnnouncementReadSerializer

User = get_user_model()


def log_action(admin_user, action, target_type, target_id=None, details=''):
    """Helper to create an audit log entry."""
    AuditLog.objects.create(
        admin=admin_user,
        action=action,
        target_type=target_type,
        target_id=target_id,
        details=details,
    )


# ─── User serialisation helper ───────────────────────────────────────────────
def _user_dict(u):
    return {
        'id': u.id, 'email': u.email, 'username': u.username,
        'first_name': u.first_name, 'last_name': u.last_name,
        'is_student': u.is_student, 'is_teacher': u.is_teacher,
        'is_staff': u.is_staff, 'is_active': u.is_active,
        'date_joined': u.date_joined,
    }


# ═══════════════════════════════════════════════════════════════════════════════
#  STATS
# ═══════════════════════════════════════════════════════════════════════════════
class AdminStatsView(APIView):
    """GET /api/admin/stats/ — Platform-wide statistics."""
    permission_classes = [IsAdminUser]

    def get(self, request):
        total_students = User.objects.filter(is_student=True).count()
        total_teachers = User.objects.filter(is_teacher=True).count()
        total_classrooms = Classroom.objects.count()
        total_feedback = Feedback.objects.count()
        total_announcements = Announcement.objects.count()

        type_counts = Feedback.objects.values('feedback_type').annotate(count=Count('id'))
        feedback_by_type = {item['feedback_type']: item['count'] for item in type_counts}

        role_counts = Feedback.objects.values('role_snapshot').annotate(count=Count('id'))
        feedback_by_role = {item['role_snapshot']: item['count'] for item in role_counts}

        avg_ratings = Feedback.objects.values('feedback_type').annotate(avg_rating=Avg('rating'))
        avg_map = {item['feedback_type']: round(item['avg_rating'] or 0, 1) for item in avg_ratings}

        return Response({
            'total_students': total_students,
            'total_teachers': total_teachers,
            'total_classrooms': total_classrooms,
            'total_feedback': total_feedback,
            'total_announcements': total_announcements,
            'feedback_by_type': {
                'game': feedback_by_type.get('game', 0),
                'website': feedback_by_type.get('website', 0),
                'classroom': feedback_by_type.get('classroom', 0),
            },
            'feedback_by_role': {
                'student': feedback_by_role.get('student', 0),
                'teacher': feedback_by_role.get('teacher', 0),
            },
            'avg_game_rating': avg_map.get('game', 0),
            'avg_website_rating': avg_map.get('website', 0),
            'avg_classroom_rating': avg_map.get('classroom', 0),
        })


# ═══════════════════════════════════════════════════════════════════════════════
#  USERS
# ═══════════════════════════════════════════════════════════════════════════════
class AdminUserListView(APIView):
    """
    GET  /api/admin/users/            — List all users (with ?search=).
    POST /api/admin/users/            — Create a new user.
    """
    permission_classes = [IsAdminUser]

    def get(self, request):
        search = request.query_params.get('search', '').strip()
        qs = User.objects.all().order_by('-date_joined')
        if search:
            qs = qs.filter(
                Q(email__icontains=search) |
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search) |
                Q(username__icontains=search)
            )
        users = qs.values(
            'id', 'email', 'username', 'first_name', 'last_name',
            'is_student', 'is_teacher', 'is_staff', 'is_active', 'date_joined'
        )
        return Response(list(users))

    def post(self, request):
        email = request.data.get('email', '').strip()
        username = request.data.get('username', '').strip()
        password = request.data.get('password', '')
        first_name = request.data.get('first_name', '').strip()
        last_name = request.data.get('last_name', '').strip()
        role = request.data.get('role', 'student')

        if not email or not username or not password:
            return Response({'detail': 'email, username, and password are required.'},
                            status=status.HTTP_400_BAD_REQUEST)

        if User.objects.filter(email=email).exists():
            return Response({'detail': 'A user with this email already exists.'},
                            status=status.HTTP_400_BAD_REQUEST)
        if User.objects.filter(username=username).exists():
            return Response({'detail': 'A user with this username already exists.'},
                            status=status.HTTP_400_BAD_REQUEST)

        user = User.objects.create_user(
            email=email, username=username, password=password,
            first_name=first_name, last_name=last_name,
            is_student=(role == 'student'),
            is_teacher=(role in ('teacher', 'admin')),
            is_staff=(role == 'admin'),
        )
        # Create profile for student/teacher
        if not hasattr(user, 'profile'):
            Profile.objects.create(user=user)

        log_action(request.user, f'Created {role} account: {email}', 'user', user.id)
        return Response(_user_dict(user), status=status.HTTP_201_CREATED)


class AdminUserDetailView(APIView):
    """
    PATCH  /api/admin/users/<id>/  — Edit name, role, active status.
    DELETE /api/admin/users/<id>/  — Hard delete a user.
    """
    permission_classes = [IsAdminUser]

    def patch(self, request, user_id):
        try:
            user = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return Response({'detail': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)

        if user == request.user:
            return Response({'detail': 'You cannot modify your own account.'},
                            status=status.HTTP_400_BAD_REQUEST)

        changes = []
        if 'first_name' in request.data:
            user.first_name = request.data['first_name']
            changes.append('first_name')
        if 'last_name' in request.data:
            user.last_name = request.data['last_name']
            changes.append('last_name')
        if 'is_active' in request.data:
            user.is_active = request.data['is_active']
            changes.append(f"is_active={request.data['is_active']}")
        if 'role' in request.data:
            role = request.data['role']
            user.is_student = (role == 'student')
            user.is_teacher = (role in ('teacher', 'admin'))
            user.is_staff = (role == 'admin')
            changes.append(f"role→{role}")

        user.save()
        log_action(request.user, f'Edited user {user.email}', 'user', user.id,
                   details=', '.join(changes))
        return Response(_user_dict(user))

    def delete(self, request, user_id):
        try:
            user = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return Response({'detail': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)

        if user == request.user:
            return Response({'detail': 'You cannot delete your own account.'},
                            status=status.HTTP_400_BAD_REQUEST)

        email = user.email
        user.delete()
        log_action(request.user, f'Deleted user {email}', 'user', user_id)
        return Response(status=status.HTTP_204_NO_CONTENT)


class AdminResetPasswordView(APIView):
    """POST /api/admin/users/<id>/reset-password/ — Reset user password."""
    permission_classes = [IsAdminUser]

    def post(self, request, user_id):
        try:
            user = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return Response({'detail': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)

        new_password = request.data.get('new_password', '')
        if len(new_password) < 3:
            return Response({'detail': 'Password must be at least 3 characters.'},
                            status=status.HTTP_400_BAD_REQUEST)

        user.set_password(new_password)
        user.save(update_fields=['password'])
        log_action(request.user, f'Reset password for {user.email}', 'user', user.id)
        return Response({'detail': 'Password reset successfully.'})


class AdminUserExportView(APIView):
    """GET /api/admin/users/export/ — CSV export of all users."""
    permission_classes = [IsAdminUser]

    def get(self, request):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="users_export.csv"'
        writer = csv.writer(response)
        writer.writerow(['ID', 'Email', 'Username', 'First Name', 'Last Name', 'Role', 'Active', 'Date Joined'])
        for u in User.objects.all().order_by('-date_joined'):
            role = 'Admin' if u.is_staff else ('Teacher' if u.is_teacher else 'Student')
            writer.writerow([u.id, u.email, u.username, u.first_name, u.last_name, role, u.is_active, u.date_joined.strftime('%Y-%m-%d')])
        log_action(request.user, 'Exported users CSV', 'user')
        return response


# ═══════════════════════════════════════════════════════════════════════════════
#  CLASSROOMS
# ═══════════════════════════════════════════════════════════════════════════════
class AdminClassroomListView(APIView):
    """GET /api/admin/classrooms/ — List all classrooms."""
    permission_classes = [IsAdminUser]

    def get(self, request):
        classrooms = Classroom.objects.select_related('teacher').annotate(
            feedback_count=Count('feedbacks'),
            announcement_count=Count('announcements'),
        ).all()
        data = [
            {
                'id': c.id,
                'name': c.name,
                'enrollment_code': c.enrollment_code,
                'teacher_email': c.teacher.email,
                'teacher_name': f"{c.teacher.first_name} {c.teacher.last_name}".strip() or c.teacher.username,
                'teacher_id': c.teacher.id,
                'student_count': c.students.count(),
                'feedback_count': c.feedback_count,
                'announcement_count': c.announcement_count,
            }
            for c in classrooms
        ]
        return Response(data)


class AdminClassroomDetailView(APIView):
    """
    GET    /api/admin/classrooms/<id>/ — Detailed classroom with students.
    PATCH  /api/admin/classrooms/<id>/ — Rename / reassign teacher.
    DELETE /api/admin/classrooms/<id>/ — Delete classroom.
    """
    permission_classes = [IsAdminUser]

    def get(self, request, classroom_id):
        try:
            classroom = Classroom.objects.select_related('teacher').get(pk=classroom_id)
        except Classroom.DoesNotExist:
            return Response({'detail': 'Classroom not found.'}, status=status.HTTP_404_NOT_FOUND)

        students = User.objects.filter(profile__classroom=classroom).values(
            'id', 'email', 'first_name', 'last_name', 'is_active'
        )
        feedback_count = Feedback.objects.filter(classroom=classroom).count()
        announcement_count = classroom.announcements.count()
        avg_rating = Feedback.objects.filter(classroom=classroom).aggregate(avg=Avg('rating'))['avg']

        # All teachers for the reassign dropdown
        teachers = list(User.objects.filter(is_teacher=True).values('id', 'email', 'first_name', 'last_name'))

        return Response({
            'id': classroom.id,
            'name': classroom.name,
            'enrollment_code': classroom.enrollment_code,
            'teacher': {
                'id': classroom.teacher.id,
                'email': classroom.teacher.email,
                'first_name': classroom.teacher.first_name,
                'last_name': classroom.teacher.last_name,
            },
            'students': list(students),
            'student_count': len(students),
            'feedback_count': feedback_count,
            'announcement_count': announcement_count,
            'avg_classroom_rating': round(avg_rating, 1) if avg_rating else None,
            'teachers': teachers,
        })

    def patch(self, request, classroom_id):
        try:
            classroom = Classroom.objects.get(pk=classroom_id)
        except Classroom.DoesNotExist:
            return Response({'detail': 'Classroom not found.'}, status=status.HTTP_404_NOT_FOUND)

        changes = []
        if 'name' in request.data:
            classroom.name = request.data['name']
            changes.append(f"name→{request.data['name']}")
        if 'teacher_id' in request.data:
            try:
                new_teacher = User.objects.get(pk=request.data['teacher_id'], is_teacher=True)
                classroom.teacher = new_teacher
                changes.append(f"teacher→{new_teacher.email}")
            except User.DoesNotExist:
                return Response({'detail': 'Teacher not found.'}, status=status.HTTP_400_BAD_REQUEST)

        classroom.save()
        log_action(request.user, f'Edited classroom "{classroom.name}"', 'classroom',
                   classroom.id, details=', '.join(changes))
        return Response({'detail': 'Classroom updated.'})

    def delete(self, request, classroom_id):
        try:
            classroom = Classroom.objects.get(pk=classroom_id)
        except Classroom.DoesNotExist:
            return Response({'detail': 'Classroom not found.'}, status=status.HTTP_404_NOT_FOUND)

        name = classroom.name
        classroom.delete()
        log_action(request.user, f'Deleted classroom "{name}"', 'classroom', classroom_id)
        return Response(status=status.HTTP_204_NO_CONTENT)


class AdminClassroomEnrollView(APIView):
    """POST /api/admin/classrooms/<id>/enroll/ — Add a student."""
    permission_classes = [IsAdminUser]

    def post(self, request, classroom_id):
        try:
            classroom = Classroom.objects.get(pk=classroom_id)
        except Classroom.DoesNotExist:
            return Response({'detail': 'Classroom not found.'}, status=status.HTTP_404_NOT_FOUND)

        user_id = request.data.get('user_id')
        try:
            student = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return Response({'detail': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)

        profile, _ = Profile.objects.get_or_create(user=student)
        profile.classroom = classroom
        profile.save()
        log_action(request.user, f'Enrolled {student.email} in "{classroom.name}"',
                   'classroom', classroom.id)
        return Response({'detail': f'{student.email} enrolled successfully.'})


class AdminClassroomUnenrollView(APIView):
    """POST /api/admin/classrooms/<id>/unenroll/ — Remove a student."""
    permission_classes = [IsAdminUser]

    def post(self, request, classroom_id):
        try:
            classroom = Classroom.objects.get(pk=classroom_id)
        except Classroom.DoesNotExist:
            return Response({'detail': 'Classroom not found.'}, status=status.HTTP_404_NOT_FOUND)

        user_id = request.data.get('user_id')
        try:
            student = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return Response({'detail': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)

        profile = getattr(student, 'profile', None)
        if profile and profile.classroom == classroom:
            profile.classroom = None
            profile.save()
            log_action(request.user, f'Unenrolled {student.email} from "{classroom.name}"',
                       'classroom', classroom.id)
            return Response({'detail': f'{student.email} removed.'})
        return Response({'detail': 'Student is not in this classroom.'},
                        status=status.HTTP_400_BAD_REQUEST)


class AdminClassroomExportView(APIView):
    """GET /api/admin/classrooms/export/ — CSV export of all classrooms."""
    permission_classes = [IsAdminUser]

    def get(self, request):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="classrooms_export.csv"'
        writer = csv.writer(response)
        writer.writerow(['ID', 'Name', 'Enrollment Code', 'Teacher Email', 'Student Count', 'Created At'])
        for c in Classroom.objects.select_related('teacher').all():
            writer.writerow([c.id, c.name, c.enrollment_code, c.teacher.email,
                             c.students.count(), c.created_at.strftime('%Y-%m-%d')])
        log_action(request.user, 'Exported classrooms CSV', 'classroom')
        return response


# ═══════════════════════════════════════════════════════════════════════════════
#  FEEDBACK
# ═══════════════════════════════════════════════════════════════════════════════
class AdminFeedbackListView(APIView):
    """GET /api/admin/feedback/ — List all feedback with filters."""
    permission_classes = [IsAdminUser]

    def get(self, request):
        qs = Feedback.objects.select_related('user', 'classroom').all()

        feedback_type = request.query_params.get('type')
        if feedback_type:
            qs = qs.filter(feedback_type=feedback_type)

        role = request.query_params.get('role')
        if role:
            qs = qs.filter(role_snapshot=role)

        date_from = request.query_params.get('date_from')
        if date_from:
            try:
                qs = qs.filter(created_at__date__gte=datetime.strptime(date_from, '%Y-%m-%d').date())
            except ValueError:
                pass

        date_to = request.query_params.get('date_to')
        if date_to:
            try:
                qs = qs.filter(created_at__date__lte=datetime.strptime(date_to, '%Y-%m-%d').date())
            except ValueError:
                pass

        serializer = FeedbackListSerializer(qs, many=True)
        return Response(serializer.data)


class AdminFeedbackDeleteView(APIView):
    """DELETE /api/admin/feedback/<id>/ — Delete a single feedback entry."""
    permission_classes = [IsAdminUser]

    def delete(self, request, feedback_id):
        try:
            fb = Feedback.objects.get(pk=feedback_id)
        except Feedback.DoesNotExist:
            return Response({'detail': 'Feedback not found.'}, status=status.HTTP_404_NOT_FOUND)

        log_action(request.user, f'Deleted feedback #{fb.id} ({fb.feedback_type})',
                   'feedback', fb.id, details=f'User: {fb.user.email}')
        fb.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class AdminFeedbackExportView(APIView):
    """GET /api/admin/feedback/export/ — CSV export of all feedback."""
    permission_classes = [IsAdminUser]

    def get(self, request):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="feedback_export.csv"'
        writer = csv.writer(response)
        writer.writerow(['ID', 'User Email', 'Role', 'Type', 'Rating', 'Comments', 'Classroom', 'Date'])
        for fb in Feedback.objects.select_related('user', 'classroom').all().order_by('-created_at'):
            writer.writerow([
                fb.id, fb.user.email, fb.role_snapshot, fb.feedback_type,
                fb.rating, fb.comments,
                fb.classroom.name if fb.classroom else '',
                fb.created_at.strftime('%Y-%m-%d'),
            ])
        log_action(request.user, 'Exported feedback CSV', 'feedback')
        return response


# ═══════════════════════════════════════════════════════════════════════════════
#  ANNOUNCEMENTS
# ═══════════════════════════════════════════════════════════════════════════════
class AdminAnnouncementListView(APIView):
    """GET /api/admin/announcements/ — List all announcements."""
    permission_classes = [IsAdminUser]

    def get(self, request):
        qs = Announcement.objects.prefetch_related('target_classrooms').select_related('author').all()
        serializer = AnnouncementReadSerializer(qs, many=True)
        return Response(serializer.data)


class AdminAnnouncementDetailView(APIView):
    """
    PATCH  /api/admin/announcements/<id>/ — Edit any announcement.
    DELETE /api/admin/announcements/<id>/ — Delete any announcement.
    """
    permission_classes = [IsAdminUser]

    def patch(self, request, pk):
        try:
            ann = Announcement.objects.get(pk=pk)
        except Announcement.DoesNotExist:
            return Response({'detail': 'Announcement not found.'}, status=status.HTTP_404_NOT_FOUND)

        if 'title' in request.data:
            ann.title = request.data['title']
        if 'body' in request.data:
            ann.body = request.data['body']
        ann.save()
        log_action(request.user, f'Edited announcement "{ann.title}"', 'announcement', ann.id)
        return Response({'detail': 'Announcement updated.'})

    def delete(self, request, pk):
        try:
            ann = Announcement.objects.get(pk=pk)
        except Announcement.DoesNotExist:
            return Response({'detail': 'Announcement not found.'}, status=status.HTTP_404_NOT_FOUND)

        title = ann.title
        ann.delete()
        log_action(request.user, f'Deleted announcement "{title}"', 'announcement', pk)
        return Response(status=status.HTTP_204_NO_CONTENT)


# ═══════════════════════════════════════════════════════════════════════════════
#  AUDIT LOG
# ═══════════════════════════════════════════════════════════════════════════════
class AdminAuditLogView(APIView):
    """GET /api/admin/audit-log/ — Recent admin actions."""
    permission_classes = [IsAdminUser]

    def get(self, request):
        logs = AuditLog.objects.select_related('admin').all()[:200]
        data = [
            {
                'id': l.id,
                'admin_email': l.admin.email if l.admin else 'deleted',
                'action': l.action,
                'target_type': l.target_type,
                'target_id': l.target_id,
                'details': l.details,
                'timestamp': l.timestamp,
            }
            for l in logs
        ]
        return Response(data)


# ─── Invite Code Settings ─────────────────────────────────────────
class AdminInviteCodeView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        codes = EducatorAccessCode.objects.all().order_by('-created_at')
        data = [
            {'id': c.id, 'code': c.code, 'is_active': c.is_active, 'created_at': c.created_at}
            for c in codes
        ]
        return Response(data)

    def post(self, request):
        """Create a new invite code."""
        code = request.data.get('code', '').strip().upper()
        if not code:
            return Response({'detail': 'Code cannot be empty.'}, status=status.HTTP_400_BAD_REQUEST)
        if EducatorAccessCode.objects.filter(code=code).exists():
            return Response({'detail': 'This code already exists.'}, status=status.HTTP_400_BAD_REQUEST)
        obj = EducatorAccessCode.objects.create(code=code, is_active=True)
        log_action(request.user, 'create', 'invite_code', obj.id, f'Created invite code {code}')
        return Response({'id': obj.id, 'code': obj.code, 'is_active': obj.is_active}, status=status.HTTP_201_CREATED)

    def patch(self, request):
        """Toggle active state or update code."""
        code_id = request.data.get('id')
        try:
            obj = EducatorAccessCode.objects.get(id=code_id)
        except EducatorAccessCode.DoesNotExist:
            return Response({'detail': 'Code not found.'}, status=status.HTTP_404_NOT_FOUND)
        if 'is_active' in request.data:
            obj.is_active = request.data['is_active']
        if 'code' in request.data:
            new_code = request.data['code'].strip().upper()
            if new_code and new_code != obj.code:
                if EducatorAccessCode.objects.filter(code=new_code).exclude(id=obj.id).exists():
                    return Response({'detail': 'This code already exists.'}, status=status.HTTP_400_BAD_REQUEST)
                obj.code = new_code
        obj.save()
        log_action(request.user, 'edit', 'invite_code', obj.id, f'Updated invite code to {obj.code}, active={obj.is_active}')
        return Response({'id': obj.id, 'code': obj.code, 'is_active': obj.is_active})

    def delete(self, request):
        code_id = request.query_params.get('id')
        try:
            obj = EducatorAccessCode.objects.get(id=code_id)
        except EducatorAccessCode.DoesNotExist:
            return Response({'detail': 'Code not found.'}, status=status.HTTP_404_NOT_FOUND)
        log_action(request.user, 'delete', 'invite_code', obj.id, f'Deleted invite code {obj.code}')
        obj.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
