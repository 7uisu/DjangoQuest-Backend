# game_api/achievement_engine.py
"""
Server-side achievement engine.
Called every time a game save is uploaded (PUT /api/game/save/).
Evaluates 15 achievement conditions against save_data and awards new ones.
"""
from users.models import Achievement, UserAchievement


# ── Achievement definitions ───────────────────────────────────────────────────
# Each entry: (key, condition_fn(save_data) -> bool)

PROFESSOR_PREFIXES = ["y1s1", "y1s2", "y2s1", "y2s2", "y3s1", "y3s2", "y3mid"]


def _all_profs_done(sd: dict) -> bool:
    return all(sd.get(f"ch2_{p}_teaching_done", False) for p in PROFESSOR_PREFIXES)


def _story_gwa(sd: dict) -> float:
    """Calculate the average final grade across all completed professors."""
    grades = []
    for p in PROFESSOR_PREFIXES:
        if sd.get(f"ch2_{p}_teaching_done", False):
            g = float(sd.get(f"ch2_{p}_final_grade", 0.0))
            if g > 0:
                grades.append(g)
    return sum(grades) / len(grades) if grades else 0.0


def _thesis_gwa(sd: dict) -> float:
    """Average of the 3 panelist grades."""
    grades = []
    for i in range(1, 4):
        g = float(sd.get(f"thesis_panelist_{i}_grade", 0.0))
        if g > 0:
            grades.append(g)
    return sum(grades) / len(grades) if grades else 0.0


def _student_help_total(sd: dict) -> int:
    seq = sd.get("student_seq_progress", {})
    if not isinstance(seq, dict):
        return 0
    return sum(int(v) for v in seq.values())


ACHIEVEMENT_CONDITIONS = [
    # Ch1
    ("ch1_complete", lambda sd: bool(sd.get("ch1_quiz_done", False))),
    ("ch1_perfect", lambda sd: sd.get("ch1_quiz_score", 0) == 5 and not sd.get("ch1_did_remedial", False)),

    # College professors
    ("first_professor", lambda sd: any(sd.get(f"ch2_{p}_teaching_done", False) for p in PROFESSOR_PREFIXES)),
    ("all_professors", lambda sd: _all_profs_done(sd)),
    ("honor_roll", lambda sd: _all_profs_done(sd) and 0 < _story_gwa(sd) <= 1.75),
    ("no_retakes", lambda sd: any(
        sd.get(f"ch2_{p}_teaching_done", False) and int(sd.get(f"ch2_{p}_retake_count", 1)) == 0
        for p in PROFESSOR_PREFIXES
    )),
    ("comeback_kid", lambda sd: any(
        sd.get(f"ch2_{p}_removal_passed", False) for p in PROFESSOR_PREFIXES
    )),

    # Thesis
    ("thesis_started", lambda sd: int(sd.get("thesis_panelist_progress", 0)) >= 1),
    ("thesis_defended", lambda sd: bool(sd.get("thesis_completed", False))),
    ("thesis_magna", lambda sd: sd.get("thesis_completed", False) and 0 < _thesis_gwa(sd) <= 1.5),

    # Misc
    ("item_shopper", lambda sd: bool(sd.get("used_item_in_college", False))),
    ("challenge_10", lambda sd: int(sd.get("challenges_completed", 0)) >= 10),
    ("challenge_25", lambda sd: int(sd.get("challenges_completed", 0)) >= 25),
    ("community_helper", lambda sd: _student_help_total(sd) >= 15),

    # Completion
    ("full_clear", lambda sd: _compute_story_pct(sd) >= 100.0),
]


def _compute_story_pct(sd: dict) -> float:
    """Same 13-flag logic as GameSave.compute_progress()."""
    flags = [
        sd.get("ch1_quiz_done", False),
        sd.get("ch2_y1s1_teaching_done", False),
        sd.get("ch2_y1s2_teaching_done", False),
        sd.get("ch2_y2s1_teaching_done", False),
        sd.get("ch2_y2s2_teaching_done", False),
        sd.get("ch2_y3s1_teaching_done", False),
        sd.get("ch2_y3s2_teaching_done", False),
        sd.get("ch2_y3mid_teaching_done", False),
        sd.get("ch1_teaching_done", False),
        sd.get("ch1_post_quiz_dialogue_done", False),
        sd.get("ch1_convenience_store_cutscene_done", False),
        sd.get("ch1_spaghetti_guy_cutscene_done", False),
        sd.get("thesis_completed", False),
    ]
    done = sum(1 for f in flags if f)
    return round(done / 13 * 100, 2)


# ── Main entry point ─────────────────────────────────────────────────────────

def check_achievements(user, save_data: dict) -> list[str]:
    """
    Evaluate all achievement conditions against save_data.
    Creates UserAchievement records for newly earned ones.
    Returns list of newly unlocked achievement keys.
    """
    if not isinstance(save_data, dict):
        return []

    # Load all achievement definitions from DB
    all_achievements = {a.key: a for a in Achievement.objects.all()}
    if not all_achievements:
        return []

    # Already-unlocked keys for this user
    unlocked_keys = set(
        UserAchievement.objects.filter(user=user)
        .values_list('achievement__key', flat=True)
    )

    newly_unlocked = []

    for key, condition_fn in ACHIEVEMENT_CONDITIONS:
        if key in unlocked_keys:
            continue  # Already earned

        achievement = all_achievements.get(key)
        if not achievement:
            continue  # Not seeded in DB

        try:
            if condition_fn(save_data):
                UserAchievement.objects.get_or_create(
                    user=user,
                    achievement=achievement,
                )
                # Award XP
                if hasattr(user, 'profile'):
                    user.profile.total_xp += achievement.xp_reward
                    user.profile.save(update_fields=['total_xp'])

                newly_unlocked.append(key)
        except Exception:
            continue  # Don't crash save on bad achievement data

    return newly_unlocked
