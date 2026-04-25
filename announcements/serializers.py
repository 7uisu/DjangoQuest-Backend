# announcements/serializers.py
from rest_framework import serializers
from .models import Announcement
from users.models import Classroom


class ClassroomMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model = Classroom
        fields = ['id', 'name']


class AnnouncementReadSerializer(serializers.ModelSerializer):
    author_name = serializers.SerializerMethodField()
    author_email = serializers.CharField(source='author.email', default='')
    target_classrooms = ClassroomMiniSerializer(many=True, read_only=True)

    class Meta:
        model = Announcement
        fields = [
            'id', 'author_name', 'author_email', 'announcement_type',
            'title', 'body', 'target_classrooms', 'created_at', 'updated_at',
        ]

    def get_author_name(self, obj):
        if not obj.author:
            return 'Deleted User'
        name = f"{obj.author.first_name} {obj.author.last_name}".strip()
        return name or obj.author.username


class AnnouncementWriteSerializer(serializers.ModelSerializer):
    target_classrooms = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Classroom.objects.all(),
        required=False,
    )

    class Meta:
        model = Announcement
        fields = ['announcement_type', 'title', 'body', 'target_classrooms']

    def validate(self, data):
        user = self.context['request'].user
        ann_type = data.get('announcement_type')

        # Determine type based on role if creating
        if not self.instance:
            if user.is_staff and not ann_type:
                data['announcement_type'] = 'platform'
                ann_type = 'platform'
            elif user.is_teacher and not ann_type:
                data['announcement_type'] = 'classroom'
                ann_type = 'classroom'

        if ann_type == 'platform':
            if not user.is_staff:
                raise serializers.ValidationError('Only admins can create platform announcements.')
            data['target_classrooms'] = []

        elif ann_type == 'classroom':
            if not user.is_teacher:
                raise serializers.ValidationError('Only teachers can create classroom announcements.')
            classrooms = data.get('target_classrooms', [])
            if not classrooms:
                raise serializers.ValidationError('Classroom announcements must target at least one classroom.')
            # Verify ownership
            for c in classrooms:
                if c.teacher_id != user.id:
                    raise serializers.ValidationError(
                        f'You do not own classroom "{c.name}".'
                    )
        return data

    def create(self, validated_data):
        classrooms = validated_data.pop('target_classrooms', [])
        validated_data['author'] = self.context['request'].user
        announcement = Announcement.objects.create(**validated_data)
        if classrooms:
            announcement.target_classrooms.set(classrooms)
        return announcement

    def update(self, instance, validated_data):
        classrooms = validated_data.pop('target_classrooms', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if classrooms is not None:
            instance.target_classrooms.set(classrooms)
        return instance
