# app/admin.py
from django.contrib import admin
from .models import Tutorial, TutorialStep, UserTutorialEnrollment, UserStepSubmission


class TutorialStepInline(admin.TabularInline):
    model = TutorialStep
    extra = 1
    fields = ('order', 'title', 'file_type', 'initial_code', 'solution_code', 'expected_elements', 'checkpoint_xp', 'trivia')


@admin.register(Tutorial)
class TutorialAdmin(admin.ModelAdmin):
    list_display = ('title', 'order', 'is_active', 'created_at')
    list_filter = ('is_active',)
    search_fields = ('title', 'description')
    ordering = ('order',)
    inlines = [TutorialStepInline]


@admin.register(TutorialStep)
class TutorialStepAdmin(admin.ModelAdmin):
    list_display = ('tutorial', 'order', 'title', 'file_type', 'checkpoint_xp')
    list_filter = ('file_type', 'tutorial')
    search_fields = ('title', 'content')
    ordering = ('tutorial', 'order')


@admin.register(UserTutorialEnrollment)
class UserTutorialEnrollmentAdmin(admin.ModelAdmin):
    list_display = ('user', 'tutorial', 'is_completed', 'started_at')
    list_filter = ('is_completed', 'tutorial')
    search_fields = ('user__username',)


@admin.register(UserStepSubmission)
class UserStepSubmissionAdmin(admin.ModelAdmin):
    list_display = ('enrollment', 'step', 'is_completed', 'attempt_count', 'last_attempt_at')
    list_filter = ('is_completed',)
