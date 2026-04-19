# game_api/models.py
from django.db import models
from django.conf import settings


class GameSave(models.Model):
    """
    Stores one save per user. The save_data JSONField holds the full game state
    (same format as the Godot local JSON save). Denormalized progress fields
    allow fast teacher-dashboard queries without parsing JSON.
    """
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='game_save',
    )
    save_data = models.JSONField(default=dict)
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    # Denormalized progress for teacher dashboard
    story_progress_percent = models.FloatField(default=0.0)
    challenges_completed = models.IntegerField(default=0)
    learning_modules_completed = models.IntegerField(default=0)
    credits = models.IntegerField(default=0)
    defeated_npcs = models.IntegerField(default=0)
    ch1_quiz_score = models.IntegerField(default=0)
    ch1_did_remedial = models.BooleanField(default=False)
    ch1_remedial_score = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.user.username}'s Save ({self.updated_at:%Y-%m-%d %H:%M})"

    @staticmethod
    def compute_progress(save_data: dict) -> dict:
        """
        Compute denormalized progress fields from raw save_data.
        Returns a dict with story_progress_percent, challenges_completed,
        and learning_modules_completed.
        """
        # ── Story progress: count how many chapter flags are True ──
        # Chapter 1 milestones (5 flags)
        ch1_flags = [
            'ch1_teaching_done',
            'ch1_quiz_done',
            'ch1_post_quiz_dialogue_done',
            'ch1_convenience_store_cutscene_done',
            'ch1_spaghetti_guy_cutscene_done',
        ]
        # Chapter 2 milestones (7 semester flags)
        ch2_flags = [
            'ch2_y1s1_teaching_done',
            'ch2_y1s2_teaching_done',
            'ch2_y2s1_teaching_done',
            'ch2_y2s2_teaching_done',
            'ch2_y3s1_teaching_done',
            'ch2_y3s2_teaching_done',
            'ch2_y3mid_teaching_done',
        ]
        all_flags = ch1_flags + ch2_flags
        total = len(all_flags)
        done = sum(1 for f in all_flags if save_data.get(f, False))
        story_pct = round((done / total) * 100, 1) if total > 0 else 0.0

        # ── Learning modules: count ch2 semesters completed ──
        learning_done = sum(1 for f in ch2_flags if save_data.get(f, False))

        # ── Challenges completed: stored directly in save_data ──
        challenges = int(save_data.get('challenges_completed', 0))

        # ── Quiz scores ──
        ch1_quiz_score = int(save_data.get('ch1_quiz_score', 0))
        ch1_did_remedial = bool(save_data.get('ch1_did_remedial', False))
        ch1_remedial_score = int(save_data.get('ch1_remedial_score', 0))

        # ── Currency ──
        credits = int(save_data.get('credits', 0))
        defeated_npcs_list = save_data.get('defeated_challenge_npcs', [])
        defeated_npcs = len(defeated_npcs_list) if isinstance(defeated_npcs_list, list) else 0

        return {
            'story_progress_percent': story_pct,
            'challenges_completed': challenges,
            'learning_modules_completed': learning_done,
            'credits': credits,
            'defeated_npcs': defeated_npcs,
            'ch1_quiz_score': ch1_quiz_score,
            'ch1_did_remedial': ch1_did_remedial,
            'ch1_remedial_score': ch1_remedial_score,
        }
