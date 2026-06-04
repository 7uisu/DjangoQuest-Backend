# djangoquestbackend/urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import redirect
from django.views.static import serve
from .views import health_check

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/health/', health_check, name='health_check'),
    path('api/tutorials/', include('app.urls')),
    path('api/users/', include('users.urls')),
    path('api/game/', include('game_api.urls')),
    path('api/dashboard/', include('dashboard.api_urls')),
    path('api/admin/', include('users.admin_urls')),
    path('api/feedback/', include('feedback.urls')),
    path('api/announcements/', include('announcements.urls')),
    path('api/patchnotes/', include('patchnotes.urls')),
    path('avatars/<path:path>', serve, {'document_root': settings.AVATAR_ROOT}),
    path('', include('dashboard.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.AVATAR_URL, document_root=settings.AVATAR_ROOT)
