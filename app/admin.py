# app/admin.py
from django.contrib import admin
from .models import (
    VideoTutorial, VideoStep, UserVideoEnrollment, UserVideoStepView
)

class VideoStepInline(admin.TabularInline):
    model = VideoStep
    extra = 1
    fields = ('order', 'title')

@admin.register(VideoTutorial)
class VideoTutorialAdmin(admin.ModelAdmin):
    list_display = ('title', 'order', 'is_active', 'created_at')
    list_filter = ('is_active',)
    search_fields = ('title', 'description')
    ordering = ('order',)
    inlines = [VideoStepInline]

@admin.register(VideoStep)
class VideoStepAdmin(admin.ModelAdmin):
    list_display = ('tutorial', 'order', 'title')
    list_filter = ('tutorial',)
    search_fields = ('title', 'content')
    ordering = ('tutorial', 'order')

@admin.register(UserVideoEnrollment)
class UserVideoEnrollmentAdmin(admin.ModelAdmin):
    list_display = ('user', 'tutorial', 'is_completed', 'started_at')
    list_filter = ('is_completed', 'tutorial')
    search_fields = ('user__username',)

@admin.register(UserVideoStepView)
class UserVideoStepViewAdmin(admin.ModelAdmin):
    list_display = ('enrollment', 'step', 'viewed_at')
    search_fields = ('enrollment__user__username',)
