# game_api/urls.py
from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from . import views

app_name = 'game_api'

urlpatterns = [
    path('login/', views.GameLoginView.as_view(), name='game_login'),
    path('token/refresh/', TokenRefreshView.as_view(), name='game_token_refresh'),
    path('enroll/', views.GameEnrollView.as_view(), name='game_enroll'),
    path('unenroll/', views.GameUnenrollView.as_view(), name='game_unenroll'),
    path('save/', views.GameSaveView.as_view(), name='game_save'),
    path('check-code/', views.GameCheckCodeView.as_view(), name='game_check_code'),
    path('ai-evaluator/', views.GameAIEvaluatorView.as_view(), name='game_ai_evaluator'),
]
