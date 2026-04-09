from django.contrib import admin
from .models import User, Profile, EducatorAccessCode, Classroom, Achievement, UserAchievement


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('email', 'username', 'is_teacher', 'is_student', 'is_active')
    list_filter = ('is_teacher', 'is_student', 'is_active')
    search_fields = ('email', 'username')


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'total_xp', 'classroom')
    list_filter = ('classroom',)


@admin.register(EducatorAccessCode)
class EducatorAccessCodeAdmin(admin.ModelAdmin):
    list_display = ('code', 'is_active', 'created_at')
    list_filter = ('is_active',)


@admin.register(Classroom)
class ClassroomAdmin(admin.ModelAdmin):
    list_display = ('name', 'teacher', 'enrollment_code', 'created_at')
    readonly_fields = ('enrollment_code',)


@admin.register(Achievement)
class AchievementAdmin(admin.ModelAdmin):
    list_display = ('name', 'xp_reward', 'created_at')


@admin.register(UserAchievement)
class UserAchievementAdmin(admin.ModelAdmin):
    list_display = ('user', 'achievement', 'date_unlocked')
