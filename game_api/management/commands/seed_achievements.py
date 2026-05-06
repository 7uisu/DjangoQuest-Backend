# game_api/management/commands/seed_achievements.py
"""
Seed the 15 built-in achievements.
Usage: python manage.py seed_achievements
"""
from django.core.management.base import BaseCommand
from users.models import Achievement


ACHIEVEMENTS = [
    {
        "key": "ch1_complete",
        "name": "📜 Origin Story",
        "description": "Completed Chapter 1 — Python History",
        "xp_reward": 50,
    },
    {
        "key": "ch1_perfect",
        "name": "🧠 History Buff",
        "description": "Got a perfect score on the Chapter 1 quiz without remedial",
        "xp_reward": 100,
    },
    {
        "key": "first_professor",
        "name": "🎓 Freshman Year",
        "description": "Defeated your first college professor",
        "xp_reward": 75,
    },
    {
        "key": "all_professors",
        "name": "👨‍🎓 Dean's Lister",
        "description": "Conquered all 7 college professors",
        "xp_reward": 200,
    },
    {
        "key": "honor_roll",
        "name": "🏅 Honor Roll",
        "description": "Achieved a Story Mode GWA of 1.75 or below",
        "xp_reward": 200,
    },
    {
        "key": "no_retakes",
        "name": "⚡ First Try",
        "description": "Beat a professor with zero retakes on the first attempt",
        "xp_reward": 100,
    },
    {
        "key": "comeback_kid",
        "name": "💪 Comeback Kid",
        "description": "Passed a removal exam after failing a professor",
        "xp_reward": 100,
    },
    {
        "key": "thesis_started",
        "name": "📋 Panel Ready",
        "description": "Defeated your first thesis panelist",
        "xp_reward": 75,
    },
    {
        "key": "thesis_defended",
        "name": "🎓 Thesis Defended",
        "description": "Successfully defended your thesis before all 3 panelists",
        "xp_reward": 250,
    },
    {
        "key": "thesis_magna",
        "name": "🌟 Magna Cum Laude",
        "description": "Achieved a Thesis GWA of 1.5 or below",
        "xp_reward": 200,
    },
    {
        "key": "item_shopper",
        "name": "🛒 Shopaholic",
        "description": "Used an item from the campus shop during College",
        "xp_reward": 50,
    },
    {
        "key": "challenge_10",
        "name": "🔥 Code Warrior",
        "description": "Completed 10 or more coding challenges",
        "xp_reward": 100,
    },
    {
        "key": "challenge_25",
        "name": "💎 Code Legend",
        "description": "Completed 25 or more coding challenges",
        "xp_reward": 150,
    },
    {
        "key": "community_helper",
        "name": "🤝 Community Helper",
        "description": "Helped 15 or more student NPCs across campus",
        "xp_reward": 100,
    },
    {
        "key": "full_clear",
        "name": "🏆 100% Complete",
        "description": "Reached 100% story progress — you've done everything!",
        "xp_reward": 300,
    },
]


class Command(BaseCommand):
    help = "Seed or update the 15 built-in achievements"

    def handle(self, *args, **options):
        created_count = 0
        updated_count = 0
        for data in ACHIEVEMENTS:
            obj, created = Achievement.objects.update_or_create(
                key=data["key"],
                defaults={
                    "name": data["name"],
                    "description": data["description"],
                    "xp_reward": data["xp_reward"],
                },
            )
            if created:
                created_count += 1
            else:
                updated_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Done! Created {created_count}, updated {updated_count} achievements. "
                f"Total: {Achievement.objects.count()}"
            )
        )
