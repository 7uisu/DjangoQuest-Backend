# feedback/serializers.py
from rest_framework import serializers
from .models import Feedback
from users.models import Classroom


class FeedbackCreateSerializer(serializers.ModelSerializer):
    """Role-aware feedback serializer with auto-set fields."""
    classroom_id = serializers.IntegerField(required=False, write_only=True)

    class Meta:
        model = Feedback
        fields = [
            'feedback_type', 'rating', 'comments',
            'classroom_id',
            'game_level', 'curriculum_relevance_rating', 'website_usability_notes',
        ]

    def validate_rating(self, value):
        if value < 1 or value > 5:
            raise serializers.ValidationError("Rating must be between 1 and 5.")
        return value

    def validate(self, attrs):
        user = self.context['request'].user
        is_teacher = getattr(user, 'is_teacher', False)
        feedback_type = attrs.get('feedback_type')
        teacher_fields = ['game_level', 'curriculum_relevance_rating', 'website_usability_notes']

        if not is_teacher:
            # Student validation
            if feedback_type not in ('game', 'website', 'classroom'):
                raise serializers.ValidationError({"feedback_type": "Students can only submit game, website, or classroom feedback."})
            for field in teacher_fields:
                if attrs.get(field):
                    raise serializers.ValidationError({field: "This field is only available for teachers."})
            if 'classroom_id' in attrs:
                raise serializers.ValidationError({"classroom_id": "Students cannot specify a classroom."})
        else:
            # Teacher validation
            if feedback_type not in ('game', 'website'):
                raise serializers.ValidationError({"feedback_type": "Teachers can only submit game or website feedback."})

        return attrs

    def create(self, validated_data):
        user = self.context['request'].user
        is_teacher = getattr(user, 'is_teacher', False)
        classroom_id = validated_data.pop('classroom_id', None)

        # Set role snapshot
        validated_data['role_snapshot'] = 'teacher' if is_teacher else 'student'
        validated_data['user'] = user

        # Handle classroom attachment
        if not is_teacher:
            # Student: auto-attach from their enrolled classroom
            profile = getattr(user, 'profile', None)
            if profile and profile.classroom:
                validated_data['classroom'] = profile.classroom
        else:
            # Teacher: handle classroom
            teacher_classrooms = Classroom.objects.filter(teacher=user)
            if classroom_id:
                try:
                    classroom = teacher_classrooms.get(pk=classroom_id)
                    validated_data['classroom'] = classroom
                except Classroom.DoesNotExist:
                    raise serializers.ValidationError({"classroom_id": "This classroom does not belong to you."})
            elif teacher_classrooms.count() == 1:
                validated_data['classroom'] = teacher_classrooms.first()

        return super().create(validated_data)


class FeedbackListSerializer(serializers.ModelSerializer):
    """Admin-facing serializer with expanded fields."""
    user_email = serializers.SerializerMethodField()
    classroom_name = serializers.SerializerMethodField()

    class Meta:
        model = Feedback
        fields = [
            'id', 'user_email', 'role_snapshot', 'feedback_type',
            'rating', 'comments', 'created_at', 'classroom_name',
            'game_level', 'curriculum_relevance_rating', 'website_usability_notes',
        ]

    def get_user_email(self, obj):
        return obj.user.email if obj.user else 'Deleted User'

    def get_classroom_name(self, obj):
        return obj.classroom.name if obj.classroom else None
