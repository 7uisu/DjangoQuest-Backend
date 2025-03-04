# users/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from .views import (
    RegisterView, UserProfileView, LogoutView,
    AchievementViewSet, UserAchievementView,
    PasswordResetView, PasswordResetConfirmView  # Import the new views
)

# Set up router for viewsets
router = DefaultRouter()
router.register(r'achievements', AchievementViewSet)

urlpatterns = [
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('register/', RegisterView.as_view(), name='register'),
    path('profile/', UserProfileView.as_view(), name='user_profile'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('password-reset/', PasswordResetView.as_view(), name='password_reset'),  # Add this
    path('password-reset-confirm/', PasswordResetConfirmView.as_view(), name='password_reset_confirm'),  # Add this
    path('user-achievements/', UserAchievementView.as_view(), name='user_achievements'),
    path('', include(router.urls)),
]