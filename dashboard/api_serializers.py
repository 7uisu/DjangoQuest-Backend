# dashboard/api_serializers.py
from rest_framework import serializers
from django.contrib.auth import get_user_model
from users.models import Classroom, Profile
from game_api.models import GameSave

User = get_user_model()


class StudentSerializer(serializers.ModelSerializer):
    """Serializer for students listed inside a classroom — includes game progress."""
    story_progress = serializers.SerializerMethodField()
    challenges_completed = serializers.SerializerMethodField()
    learning_modules_completed = serializers.SerializerMethodField()
    ch1_quiz_score = serializers.SerializerMethodField()
    ch1_did_remedial = serializers.SerializerMethodField()
    ch1_remedial_score = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'date_joined',
                  'story_progress', 'challenges_completed', 'learning_modules_completed',
                  'ch1_quiz_score', 'ch1_did_remedial', 'ch1_remedial_score']
        read_only_fields = fields

    def get_story_progress(self, obj) -> float:
        try:
            return obj.game_save.story_progress_percent
        except GameSave.DoesNotExist:
            return 0.0

    def get_challenges_completed(self, obj) -> int:
        try:
            return obj.game_save.challenges_completed
        except GameSave.DoesNotExist:
            return 0

    def get_learning_modules_completed(self, obj) -> int:
        try:
            return obj.game_save.learning_modules_completed
        except GameSave.DoesNotExist:
            return 0

    def get_ch1_quiz_score(self, obj) -> int:
        try:
            return obj.game_save.ch1_quiz_score
        except GameSave.DoesNotExist:
            return 0

    def get_ch1_did_remedial(self, obj) -> bool:
        try:
            return obj.game_save.ch1_did_remedial
        except GameSave.DoesNotExist:
            return False

    def get_ch1_remedial_score(self, obj) -> int:
        try:
            return obj.game_save.ch1_remedial_score
        except GameSave.DoesNotExist:
            return 0


class ClassroomSerializer(serializers.ModelSerializer):
    """List/create serializer — includes student count."""
    student_count = serializers.SerializerMethodField()

    class Meta:
        model = Classroom
        fields = ['id', 'name', 'enrollment_code', 'student_count', 'created_at']
        read_only_fields = ['id', 'enrollment_code', 'created_at']

    def get_student_count(self, obj) -> int:
        return obj.students.count()


class ClassroomDetailSerializer(serializers.ModelSerializer):
    """Detail serializer — includes full list of enrolled students."""
    students = serializers.SerializerMethodField()
    student_count = serializers.SerializerMethodField()

    class Meta:
        model = Classroom
        fields = ['id', 'name', 'enrollment_code', 'student_count', 'students', 'created_at']
        read_only_fields = fields

    def get_student_count(self, obj) -> int:
        return obj.students.count()

    def get_students(self, obj):
        profiles = obj.students.select_related('user').all()
        users = [p.user for p in profiles]
        return StudentSerializer(users, many=True).data

