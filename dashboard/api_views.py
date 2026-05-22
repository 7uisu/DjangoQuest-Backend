# dashboard/api_views.py
from rest_framework import generics, status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from django.db import models
from django.shortcuts import get_object_or_404
from users.models import Classroom, Profile
from .api_serializers import ClassroomSerializer, ClassroomDetailSerializer

User = get_user_model()


class IsTeacher(permissions.BasePermission):
    """Only allow authenticated teachers."""
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_teacher


class ClassroomListCreateView(generics.ListCreateAPIView):
    """
    GET  /api/dashboard/classrooms/     — list this teacher's classrooms
    POST /api/dashboard/classrooms/     — create a new classroom
    """
    serializer_class = ClassroomSerializer
    permission_classes = [IsTeacher]

    def get_queryset(self):
        return Classroom.objects.filter(teacher=self.request.user).order_by('-created_at')

    def perform_create(self, serializer):
        serializer.save(teacher=self.request.user)


class ClassroomDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET    /api/dashboard/classrooms/<pk>/ — classroom detail with students
    PATCH  /api/dashboard/classrooms/<pk>/ — rename classroom
    DELETE /api/dashboard/classrooms/<pk>/ — delete classroom
    """
    serializer_class = ClassroomDetailSerializer
    permission_classes = [IsTeacher]

    def get_queryset(self):
        return Classroom.objects.filter(teacher=self.request.user)


def _classroom_students_queryset(classroom):
    return Profile.objects.filter(
        models.Q(classroom=classroom) | models.Q(classrooms=classroom)
    ).select_related('user').distinct()


def _profile_is_in_classroom(profile, classroom) -> bool:
    if profile is None or classroom is None:
        return False
    return Profile.objects.filter(user=profile.user).filter(
        models.Q(classroom=classroom) | models.Q(classrooms=classroom)
    ).exists()


class StudentClassroomListView(APIView):
    """
    GET /api/dashboard/my-classrooms/ — all classrooms for the current student.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        profile = getattr(request.user, 'profile', None)
        if not request.user.is_student or profile is None:
            return Response(
                {"detail": "You are not enrolled in any classroom."},
                status=status.HTTP_404_NOT_FOUND,
            )

        classrooms = list(profile.classrooms.select_related('teacher').all())
        if profile.classroom and profile.classroom not in classrooms:
            classrooms.append(profile.classroom)
        classrooms = sorted(classrooms, key=lambda c: c.name.lower())

        return Response([
            {
                "id": classroom.id,
                "name": classroom.name,
                "teacher": classroom.teacher.username,
                "teacher_name": f"{classroom.teacher.first_name} {classroom.teacher.last_name}".strip() or classroom.teacher.username,
                "student_count": _classroom_students_queryset(classroom).count(),
            }
            for classroom in classrooms
        ])


class StudentCurrentClassroomView(APIView):
    """
    GET /api/dashboard/my-classroom/<pk>/ — read-only classroom view for enrolled students.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk=None):
        profile = getattr(request.user, 'profile', None)
        if not request.user.is_student or profile is None:
            return Response(
                {"detail": "You are not enrolled in any classroom."},
                status=status.HTTP_404_NOT_FOUND,
            )

        classroom = profile.classroom or profile.classrooms.first() if pk is None else Classroom.objects.filter(pk=pk).first()
        if not _profile_is_in_classroom(profile, classroom):
            return Response(
                {"detail": "You are not enrolled in this classroom."},
                status=status.HTTP_404_NOT_FOUND,
            )

        classmates = _classroom_students_queryset(classroom).order_by('user__username')
        return Response({
            "id": classroom.id,
            "name": classroom.name,
            "teacher": classroom.teacher.username,
            "teacher_name": f"{classroom.teacher.first_name} {classroom.teacher.last_name}".strip() or classroom.teacher.username,
            "student_count": classmates.count(),
            "classmates": [
                {
                    "id": profile.user_id,
                    "username": profile.user.username,
                    "is_self": profile.user_id == request.user.id,
                    "total_xp": getattr(profile, "total_xp", 0),
                }
                for profile in classmates
            ],
        })


class StudentPasswordResetView(APIView):
    """
    POST /api/dashboard/students/<pk>/reset-password/
    Teacher resets a student's password to a default value.
    """
    permission_classes = [IsTeacher]

    def post(self, request, pk):
        student = get_object_or_404(User, pk=pk, is_student=True)

        # Verify student is in one of this teacher's classrooms
        teacher_classrooms = Classroom.objects.filter(teacher=request.user)
        is_enrolled = (
            hasattr(student, 'profile')
            and Profile.objects.filter(user=student).filter(
                models.Q(classroom__in=teacher_classrooms) | models.Q(classrooms__in=teacher_classrooms)
            ).exists()
        )

        if not is_enrolled:
            return Response(
                {"detail": "This student is not in any of your classrooms."},
                status=status.HTTP_403_FORBIDDEN,
            )

        new_password = "DjangoQuest2026!"
        student.set_password(new_password)
        student.save()

        return Response({
            "detail": f"Password for {student.username} has been reset.",
            "new_password": new_password,
        })

class RemoveStudentFromClassroomView(APIView):
    """
    POST /api/dashboard/classrooms/<pk>/remove-student/<student_id>/
    Teacher removes a student from a specific classroom.
    """
    permission_classes = [IsTeacher]

    def post(self, request, pk, student_id):
        classroom = get_object_or_404(Classroom, pk=pk, teacher=request.user)
        student = get_object_or_404(User, pk=student_id, is_student=True)
        
        if hasattr(student, 'profile') and _profile_is_in_classroom(student.profile, classroom):
            student.profile.classrooms.remove(classroom)
            if student.profile.classroom == classroom:
                student.profile.classroom = student.profile.classrooms.first()
            student.profile.save()
            return Response({"detail": f"Removed {student.username} from {classroom.name}."})
            
        return Response(
            {"detail": "This student is not in this classroom."},
            status=status.HTTP_400_BAD_REQUEST
        )
