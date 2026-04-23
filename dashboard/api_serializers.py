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
    detailed_grades = serializers.SerializerMethodField()
    story_mode_gwa = serializers.SerializerMethodField()
    learning_mode_gwa = serializers.SerializerMethodField()
    learning_mode_detailed_grades = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'date_joined',
                  'story_progress', 'challenges_completed', 'learning_modules_completed',
                  'ch1_quiz_score', 'ch1_did_remedial', 'ch1_remedial_score', 'detailed_grades', 'story_mode_gwa', 'learning_mode_gwa', 'learning_mode_detailed_grades']
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
        
        try:
            sd = obj.game_save.save_data
            if not isinstance(sd, dict): sd = {}
            
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
        except GameSave.DoesNotExist:
            payload = []
            for prof_name, _ in professors:
                payload.append({
                    "professor": prof_name,
                    "grade": "Not Attempted",
                    "retakes": "Not Attempted",
                    "removal_exam": "Not Attempted"
                })
            return payload

    def get_story_mode_gwa(self, obj) -> float:
        professors = ["ch2_y1s1", "ch2_y1s2", "ch2_y2s1", "ch2_y2s2", "ch2_y3s1", "ch2_y3s2", "ch2_y3mid"]
        try:
            sd = obj.game_save.save_data
            if not isinstance(sd, dict): return 0.0
            
            total = 0.0
            count = 0
            for prefix in professors:
                grade = sd.get(f"{prefix}_final_grade", 0.0)
                if isinstance(grade, (int, float)) and float(grade) > 0.0:
                    total += float(grade)
                    count += 1
            return round(total / count, 2) if count > 0 else 0.0
        except GameSave.DoesNotExist:
            return 0.0

    def get_learning_mode_gwa(self, obj) -> float:
        try:
            sd = obj.game_save.save_data
            if not isinstance(sd, dict): return 0.0
            lmg = sd.get('learning_mode_grades', {})
            if not isinstance(lmg, dict) or not lmg: return 0.0
            
            total = 0.0
            count = 0
            for k, v in lmg.items():
                try:
                    f_val = float(v)
                    if f_val > 0.0:
                        total += f_val
                        count += 1
                except (ValueError, TypeError):
                    continue
            return round(total / count, 2) if count > 0 else 0.0
        except GameSave.DoesNotExist:
            return 0.0

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
        try:
            sd = obj.game_save.save_data
            if not isinstance(sd, dict): return []
            lmg = sd.get('learning_mode_grades', {})
            if not isinstance(lmg, dict) or not lmg: return []
            payload = []
            for prof_name, key in professors:
                if key in lmg:
                    payload.append({
                        "professor": prof_name,
                        "grade": round(float(lmg[key]), 2),
                    })
            return payload
        except GameSave.DoesNotExist:
            return []


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

