# users/serializers.py
from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework.validators import UniqueValidator
from .models import Profile, Achievement, UserAchievement, EducatorAccessCode
from django.db import transaction

User = get_user_model()

class ProfileSerializer(serializers.ModelSerializer):
    """Serializer for user profile data"""
    classroom_name = serializers.SerializerMethodField()
    teacher_name = serializers.SerializerMethodField()

    class Meta:
        model = Profile
        fields = ['avatar', 'bio', 'total_xp', 'classroom_name', 'teacher_name']
        read_only_fields = ['total_xp', 'classroom_name', 'teacher_name']

    def get_classroom_name(self, obj):
        return obj.classroom.name if obj.classroom else None
        
    def get_teacher_name(self, obj):
        return obj.classroom.teacher.username if obj.classroom else None

class AchievementSerializer(serializers.ModelSerializer):
    """Serializer for achievements"""
    class Meta:
        model = Achievement
        fields = ['id', 'name', 'description', 'xp_reward']
        read_only_fields = ['id']

class UserAchievementSerializer(serializers.ModelSerializer):
    """Serializer for user achievements"""
    achievement = AchievementSerializer(read_only=True)
    
    class Meta:
        model = UserAchievement
        fields = ['achievement', 'date_unlocked']
        read_only_fields = ['date_unlocked']

class UserSerializer(serializers.ModelSerializer):
    """Serializer for user data"""
    profile = ProfileSerializer(read_only=True)
    achievements = UserAchievementSerializer(many=True, read_only=True)
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'is_verified', 'is_teacher', 'is_student', 'date_joined', 'profile', 'achievements']
        read_only_fields = ['id', 'is_verified', 'is_teacher', 'is_student', 'date_joined']

class UserProfileUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating user profile"""
    profile = ProfileSerializer()
    
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'profile']
    
    def update(self, instance, validated_data):
        profile_data = validated_data.pop('profile', None)
        
        # Update User fields
        instance.first_name = validated_data.get('first_name', instance.first_name)
        instance.last_name = validated_data.get('last_name', instance.last_name)
        instance.save()
        
        # Update Profile fields if provided
        if profile_data:
            profile = instance.profile
            for attr, value in profile_data.items():
                if attr != 'total_xp':  # Don't allow updating XP directly
                    setattr(profile, attr, value)
            profile.save()
            
        return instance

class RegisterSerializer(serializers.ModelSerializer):
    """Serializer for creating new users with optional role selection"""
    email = serializers.EmailField(
        required=True,
        validators=[UniqueValidator(queryset=User.objects.all())]
    )
    password = serializers.CharField(
        write_only=True, 
        required=True, 
        validators=[validate_password]
    )
    password2 = serializers.CharField(write_only=True, required=True)
    role = serializers.ChoiceField(
        choices=['student', 'teacher'],
        default='student',
        write_only=True,
        required=False,
    )
    educator_code = serializers.CharField(
        write_only=True,
        required=False,
        allow_blank=True,
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'password2', 'first_name', 'last_name', 'role', 'educator_code']

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Password fields didn't match."})

        role = attrs.get('role', 'student')
        if role == 'teacher':
            educator_code = attrs.get('educator_code', '').strip()
            if not educator_code:
                raise serializers.ValidationError({"educator_code": "Educator Access Code is required for teacher registration."})
            if not EducatorAccessCode.objects.filter(code=educator_code, is_active=True).exists():
                raise serializers.ValidationError({"educator_code": "Invalid Educator Access Code."})
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        validated_data.pop('password2')
        role = validated_data.pop('role', 'student')
        validated_data.pop('educator_code', None)
        
        user = User.objects.create(
            username=validated_data['username'],
            email=validated_data['email'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
            is_teacher=(role == 'teacher'),
            is_student=(role == 'student'),
        )
        user.set_password(validated_data['password'])
        user.save()
        
        Profile.objects.create(user=user)
        
        return user
    
class PasswordResetSerializer(serializers.Serializer):
    email = serializers.EmailField()

class PasswordResetConfirmSerializer(serializers.Serializer):
    uid = serializers.CharField()
    token = serializers.CharField()
    new_password = serializers.CharField(write_only=True)