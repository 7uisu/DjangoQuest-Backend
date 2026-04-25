# users/serializers.py
from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework.validators import UniqueValidator
from .models import Profile, Achievement, UserAchievement, EducatorAccessCode
from django.db import transaction
from game_api.models import GameSave

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
    story_progress = serializers.SerializerMethodField()
    challenges_completed = serializers.SerializerMethodField()
    learning_modules_completed = serializers.SerializerMethodField()
    ch1_quiz_score = serializers.SerializerMethodField()
    ch1_did_remedial = serializers.SerializerMethodField()
    ch1_remedial_score = serializers.SerializerMethodField()
    detailed_grades = serializers.SerializerMethodField()
    story_mode_gwa = serializers.SerializerMethodField()
    learning_mode_gwa = serializers.SerializerMethodField()
    learning_mode_detailed_grades = serializers.SerializerMethodField()
    certificates = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'is_verified', 'is_teacher', 'is_student', 'is_staff', 'is_superuser', 'date_joined', 'profile', 'achievements',
                  'story_progress', 'challenges_completed', 'learning_modules_completed',
                  'ch1_quiz_score', 'ch1_did_remedial', 'ch1_remedial_score', 'detailed_grades', 'story_mode_gwa', 'learning_mode_gwa', 'learning_mode_detailed_grades',
                  'certificates']
        read_only_fields = ['id', 'is_verified', 'is_teacher', 'is_student', 'is_staff', 'is_superuser', 'date_joined']

    def get_story_progress(self, obj) -> float:
        game_save = getattr(obj, 'game_save', None)
        if not game_save:
            return 0.0
        return game_save.story_progress_percent

    def get_challenges_completed(self, obj) -> int:
        game_save = getattr(obj, 'game_save', None)
        return game_save.challenges_completed if game_save else 0

    def get_learning_modules_completed(self, obj) -> int:
        game_save = getattr(obj, 'game_save', None)
        return game_save.learning_modules_completed if game_save else 0

    def get_ch1_quiz_score(self, obj) -> int:
        game_save = getattr(obj, 'game_save', None)
        return game_save.ch1_quiz_score if game_save else 0

    def get_ch1_did_remedial(self, obj) -> bool:
        game_save = getattr(obj, 'game_save', None)
        return game_save.ch1_did_remedial if game_save else False

    def get_ch1_remedial_score(self, obj) -> int:
        game_save = getattr(obj, 'game_save', None)
        return game_save.ch1_remedial_score if game_save else 0

    def get_detailed_grades(self, obj) -> list:
        professors = [
            ("Professor Markup", "ch2_y1s1"),
            ("Professor Syntax", "ch2_y1s2"),
            ("Professor View", "ch2_y2s1"),
            ("Professor Query", "ch2_y2s2"),
            ("Professor Auth", "ch2_y3s1"),
            ("Professor Token", "ch2_y3s2"),
            ("Professor REST", "ch2_y3mid"),
        ]
        not_attempted = [
            {"professor": n, "grade": "Not Attempted",
            "retakes": "Not Attempted", "removal_exam": "Not Attempted"}
            for n, _ in professors
        ]

        game_save = getattr(obj, 'game_save', None)
        if not game_save:
            return not_attempted

        sd = game_save.save_data
        if not isinstance(sd, dict):
            return not_attempted

        payload = []
        for prof_name, prefix in professors:
            grade = sd.get(f"{prefix}_final_grade", "Not Attempted")
            try:
                if float(grade) <= 0.0:
                    grade = "Not Attempted"
            except (ValueError, TypeError):
                pass

            retakes = sd.get(f"{prefix}_retake_count", "Not Attempted") if grade != "Not Attempted" else "Not Attempted"
            removal = sd.get(f"{prefix}_removal_passed", "Not Attempted") if grade != "Not Attempted" else "Not Attempted"

            prof_data = {
                "professor": prof_name,
                "grade": grade,
                "retakes": retakes,
                "removal_exam": removal
            }

            if prefix == "ch2_y2s2":
                prof_data["ai_data"] = {
                    "ai_oto_skipped": sd.get("ch2_y2s2_ai_oto_skipped", False),
                    "ai_otm_skipped": sd.get("ch2_y2s2_ai_otm_skipped", False),
                    "ai_mtm_skipped": sd.get("ch2_y2s2_ai_mtm_skipped", False),
                    "ai_fully_offline": sd.get("ch2_y2s2_ai_fully_offline", False)
                }
            elif prefix == "ch2_y1s2":
                prof_data["ai_data"] = {
                    "ai_data_types_skipped": sd.get("ch2_y1s2_ai_data_types_skipped", False),
                    "ai_fully_offline": sd.get("ch2_y1s2_ai_fully_offline", False)
                }
            elif prefix == "ch2_y2s1":
                prof_data["ai_data"] = {
                    "ai_url_routing_skipped": sd.get("ch2_y2s1_ai_url_routing_skipped", False),
                    "ai_fully_offline": sd.get("ch2_y2s1_ai_fully_offline", False)
                }
            elif prefix == "ch2_y3s1":
                prof_data["ai_data"] = {
                    "ai_auth_checker_skipped": sd.get("ch2_y3s2_ai_auth_checker_skipped", False),
                    "ai_fully_offline": sd.get("ch2_y3s2_ai_fully_offline", False)
                }
            elif prefix == "ch2_y3mid":
                prof_data["ai_data"] = {
                    "ai_http_verbs_skipped": sd.get("ch2_y3mid_ai_http_verbs_skipped", False),
                    "ai_fully_offline": sd.get("ch2_y3mid_ai_fully_offline", False)
                }

            payload.append(prof_data)

        return payload

    def get_story_mode_gwa(self, obj) -> float:
        game_save = getattr(obj, 'game_save', None)
        if not game_save:
            return 0.0
        sd = game_save.save_data
        if not isinstance(sd, dict):
            return 0.0
        professors = ["ch2_y1s1", "ch2_y1s2", "ch2_y2s1", "ch2_y2s2", "ch2_y3s1", "ch2_y3s2", "ch2_y3mid"]
        total, count = 0.0, 0
        for prefix in professors:
            grade = sd.get(f"{prefix}_final_grade", 0.0)
            if isinstance(grade, (int, float)) and float(grade) > 0.0:
                total += float(grade)
                count += 1
        return round(total / count, 2) if count > 0 else 0.0

    def get_learning_mode_gwa(self, obj) -> float:
        game_save = getattr(obj, 'game_save', None)
        if not game_save:
            return 0.0
        sd = game_save.save_data
        if not isinstance(sd, dict):
            return 0.0
        lmg = sd.get('learning_mode_grades', {})
        if not isinstance(lmg, dict) or not lmg:
            return 0.0
        total, count = 0.0, 0
        for v in lmg.values():
            try:
                f_val = float(v)
                if f_val > 0.0:
                    total += f_val
                    count += 1
            except (ValueError, TypeError):
                continue
        return round(total / count, 2) if count > 0 else 0.0

    def get_learning_mode_detailed_grades(self, obj) -> list:
        professors = [
            ("Professor Markup", "markup"),
            ("Professor Syntax", "syntax"),
            ("Professor View", "view"),
            ("Professor Query", "query"),
            ("Professor Token", "token"),
            ("Professor Auth", "auth"),
            ("Professor REST", "rest"),
        ]
        game_save = getattr(obj, 'game_save', None)
        if not game_save:
            return []
        sd = game_save.save_data
        if not isinstance(sd, dict):
            return []
        lmg = sd.get('learning_mode_grades', {})
        if not isinstance(lmg, dict) or not lmg:
            return []
        payload = []
        for prof_name, key in professors:
            if key in lmg:
                payload.append({
                    "professor": prof_name,
                    "grade": round(float(lmg[key]), 2),
                    "label": self._grade_to_label(float(lmg[key]))
                })
        return payload

    PROFESSOR_CERTS = [
        ("y1s1", "Professor Markup", "HTML Basics"),
        ("y1s2", "Professor Syntax", "Python Data Types"),
        ("y2s1", "Professor View", "Django Views & URL Routing"),
        ("y2s2", "Professor Query", "Django ORM & Relationships"),
        ("y3s1", "Professor Auth", "Authentication & Security"),
        ("y3s2", "Professor Token", "Token-Based Auth"),
        ("y3mid", "Professor REST", "RESTful API Design"),
    ]

    def get_certificates(self, obj) -> list:
        game_save = getattr(obj, 'game_save', None)
        sd = game_save.save_data if game_save and isinstance(game_save.save_data, dict) else {}

        certs = []
        all_done = True
        latest_ts = None
        for key, name, topic in self.PROFESSOR_CERTS:
            done = bool(sd.get(f"ch2_{key}_teaching_done", False))
            ts = sd.get(f"ch2_{key}_teaching_done_at", None)
            if not done:
                all_done = False
            if ts and (latest_ts is None or ts > latest_ts):
                latest_ts = ts
            certs.append({
                "id": f"CERT-{obj.id}-{key}",
                "professor": name,
                "topic": topic,
                "professor_key": key,
                "completed": done,
                "completed_at": ts,
            })
        # Grand completion certificate
        certs.append({
            "id": f"CERT-{obj.id}-grand",
            "professor": "DjangoQuest",
            "topic": "Full-Stack Django Development",
            "professor_key": "grand",
            "completed": all_done,
            "completed_at": latest_ts if all_done else None,
        })
        return certs

    @staticmethod
    def _grade_to_label(grade: float) -> str:
        if grade <= 1.0: return "1.0 (Excellent)"
        elif grade <= 1.25: return "1.25 (Excellent)"
        elif grade <= 1.5: return "1.5 (Very Good)"
        elif grade <= 1.75: return "1.75 (Very Good)"
        elif grade <= 2.0: return "2.0 (Good)"
        elif grade <= 2.25: return "2.25 (Good)"
        elif grade <= 2.5: return "2.5 (Satisfactory)"
        elif grade <= 2.75: return "2.75 (Satisfactory)"
        elif grade <= 3.0: return "3.0 (Passing)"
        elif grade <= 4.0: return "4.0 (INC)"
        else: return "5.0 (Failed)"

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
    """Serializer for creating new users with mandatory name and role selection"""
    email = serializers.EmailField(
        required=True,
        validators=[UniqueValidator(
            queryset=User.objects.all(),
            message="This email is already registered. Try logging in instead."
        )],
        error_messages={
            'required': 'Please enter your email address.',
            'invalid': 'Please enter a valid email address (e.g. name@example.com).',
        }
    )
    password = serializers.CharField(
        write_only=True, 
        required=True, 
        validators=[validate_password],
        error_messages={
            'required': 'Please create a password.',
        }
    )
    password2 = serializers.CharField(
        write_only=True, required=True,
        error_messages={
            'required': 'Please confirm your password.',
        }
    )
    first_name = serializers.CharField(
        required=True, max_length=150,
        error_messages={
            'required': 'Please enter your first name.',
            'blank': 'First name cannot be blank.',
        }
    )
    last_name = serializers.CharField(
        required=True, max_length=150,
        error_messages={
            'required': 'Please enter your last name.',
            'blank': 'Last name cannot be blank.',
        }
    )
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
        extra_kwargs = {
            'username': {
                'error_messages': {
                    'required': 'Please choose a username.',
                    'unique': 'This username is already taken. Please choose a different one.',
                },
                'validators': [UniqueValidator(
                    queryset=User.objects.all(),
                    message="This username is already taken. Please choose a different one."
                )],
            }
        }

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password2": "Passwords do not match. Please try again."})

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