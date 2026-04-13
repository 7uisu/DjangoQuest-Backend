# game_api/urls.py
from django.urls import path
from . import views

app_name = 'game_api'

urlpatterns = [
    path('login/', views.GameLoginView.as_view(), name='game_login'),
    path('enroll/', views.GameEnrollView.as_view(), name='game_enroll'),
    path('unenroll/', views.GameUnenrollView.as_view(), name='game_unenroll'),
    path('save/', views.GameSaveView.as_view(), name='game_save'),
]
