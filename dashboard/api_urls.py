# dashboard/api_urls.py
from django.urls import path
from .api_views import ClassroomListCreateView, ClassroomDetailView, StudentPasswordResetView, RemoveStudentFromClassroomView
from .leaderboard_views import LeaderboardView, ClassroomRankingsView

urlpatterns = [
    path('classrooms/', ClassroomListCreateView.as_view(), name='api-classroom-list'),
    path('classrooms/<int:pk>/', ClassroomDetailView.as_view(), name='api-classroom-detail'),
    path('classrooms/<int:pk>/remove-student/<int:student_id>/', RemoveStudentFromClassroomView.as_view(), name='api-remove-student'),
    path('students/<int:pk>/reset-password/', StudentPasswordResetView.as_view(), name='api-student-reset'),
    path('leaderboard/', LeaderboardView.as_view(), name='api-leaderboard'),
    path('classroom-rankings/', ClassroomRankingsView.as_view(), name='api-classroom-rankings'),
]

