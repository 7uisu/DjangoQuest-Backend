# dashboard/api_serializers.py
from rest_framework import serializers
from django.contrib.auth import get_user_model
from users.models import Classroom, Profile

User = get_user_model()


class StudentSerializer(serializers.ModelSerializer):
    """Serializer for students listed inside a classroom."""
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'date_joined']
        read_only_fields = fields


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
