# app/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('tutorials/', views.TutorialListView.as_view(), name='tutorial_list'),
    path('user/progress/', views.UserProgressView.as_view(), name='user_progress'),
    path('check-code/', views.CheckCodeView.as_view(), name='check_code'),
    path('tutorials/<int:tutorial_id>/complete/', views.TutorialCompleteView.as_view(), name='tutorial_complete'),
    path('user/reset-progress/', views.ResetProgressView.as_view(), name='reset-progress'),
]