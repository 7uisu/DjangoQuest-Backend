# djangoquestbackend/urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import redirect

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/tutorials/', include('app.urls')),
    path('api/users/', include('users.urls')),
    path('api/game/', include('game_api.urls')),
    path('api/dashboard/', include('dashboard.api_urls')),
    path('', include('dashboard.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.AVATAR_URL, document_root=settings.AVATAR_ROOT)