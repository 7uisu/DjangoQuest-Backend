# app/urls.py
from django.urls import path
from . import views

urlpatterns = [
    # Video URLs
    path('video/', views.VideoTutorialListView.as_view()),
    path('video/progress/', views.VideoProgressView.as_view()),
    path('video/<int:tutorial_id>/complete/', views.VideoCompleteView.as_view()),
    
    # Global Reset
    path('user/reset-progress/', views.ResetProgressView.as_view()),
]