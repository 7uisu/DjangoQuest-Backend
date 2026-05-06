# dashboard/leaderboard_views.py
"""
Leaderboard API — ranked list of students by XP.
GET /api/dashboard/leaderboard/?scope=classroom|global
GET /api/dashboard/classroom-rankings/  (teacher only)
"""
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models import Count
from django.contrib.auth import get_user_model
from users.models import Classroom

User = get_user_model()


class LeaderboardView(APIView):
    """
    Returns a ranked list of students sorted by total_xp descending.
    Query params:
      - scope: 'classroom' (default) or 'global'
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        scope = request.query_params.get('scope', 'classroom')

        qs = User.objects.filter(
            is_student=True,
            profile__isnull=False,
            game_save__isnull=False,
        ).select_related('profile', 'game_save').annotate(
            achievements_count=Count('achievements')
        )

        if scope == 'classroom':
            classroom = getattr(request.user.profile, 'classroom', None) if hasattr(request.user, 'profile') else None
            if classroom:
                qs = qs.filter(profile__classroom=classroom)
            else:
                # Not enrolled — return empty
                return Response({'scope': 'classroom', 'entries': []})

        qs = qs.order_by('-profile__total_xp')[:50]

        entries = []
        for rank, user in enumerate(qs, start=1):
            entries.append({
                'rank': rank,
                'username': user.username,
                'total_xp': user.profile.total_xp,
                'story_progress': user.game_save.story_progress_percent,
                'challenges_completed': user.game_save.challenges_completed,
                'achievements_count': user.achievements_count,
                'story_mode_gwa': self._calc_gwa(user),
                'is_self': user.pk == request.user.pk,
            })

        return Response({
            'scope': scope,
            'entries': entries,
        })

    def _calc_gwa(self, user) -> float:
        """Quick GWA from save_data."""
        sd = user.game_save.save_data
        if not isinstance(sd, dict):
            return 0.0
        prefixes = ["y1s1", "y1s2", "y2s1", "y2s2", "y3s1", "y3s2", "y3mid"]
        grades = []
        for p in prefixes:
            if sd.get(f"ch2_{p}_teaching_done", False):
                g = float(sd.get(f"ch2_{p}_final_grade", 0.0))
                if g > 0:
                    grades.append(g)
        return round(sum(grades) / len(grades), 2) if grades else 0.0


class ClassroomRankingsView(APIView):
    """
    Returns aggregate stats per classroom for the teacher's dashboard.
    Only accessible by teachers — returns classrooms they own.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        if not getattr(request.user, 'is_teacher', False):
            return Response({'detail': 'Teachers only.'}, status=status.HTTP_403_FORBIDDEN)

        classrooms = Classroom.objects.filter(teacher=request.user)
        rankings = []

        for classroom in classrooms:
            profiles = classroom.students.select_related('user').all()
            users = [p.user for p in profiles]
            student_count = len(users)

            if student_count == 0:
                rankings.append({
                    'id': classroom.id,
                    'name': classroom.name,
                    'student_count': 0,
                    'avg_xp': 0,
                    'avg_progress': 0,
                    'total_achievements': 0,
                })
                continue

            total_xp = sum(getattr(p, 'total_xp', 0) for p in profiles)
            total_progress = 0
            total_achievements = 0

            for u in users:
                gs = getattr(u, 'game_save', None)
                if gs:
                    total_progress += gs.story_progress_percent
                total_achievements += u.achievements.count()

            rankings.append({
                'id': classroom.id,
                'name': classroom.name,
                'student_count': student_count,
                'avg_xp': round(total_xp / student_count, 1),
                'avg_progress': round(total_progress / student_count, 1),
                'total_achievements': total_achievements,
            })

        rankings.sort(key=lambda x: x['avg_xp'], reverse=True)
        return Response({'rankings': rankings})
