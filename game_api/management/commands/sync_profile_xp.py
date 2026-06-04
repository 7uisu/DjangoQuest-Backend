from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from game_api.achievement_engine import check_achievements, sync_profile_xp
from users.models import Achievement


class Command(BaseCommand):
    help = "Resync profile XP from earned achievements for users with game saves."

    def handle(self, *args, **options):
        if not Achievement.objects.exists():
            self.stdout.write(
                self.style.WARNING(
                    "No achievements found. Run seed_achievements before syncing XP."
                )
            )
            return

        User = get_user_model()
        users = (
            User.objects
            .filter(game_save__isnull=False, profile__isnull=False)
            .select_related("game_save", "profile")
        )

        checked = 0
        unlocked_count = 0
        for user in users:
            save_data = user.game_save.save_data
            newly_unlocked = check_achievements(user, save_data)
            total_xp = sync_profile_xp(user)
            checked += 1
            unlocked_count += len(newly_unlocked)
            self.stdout.write(
                f"{user.username}: {total_xp} XP"
                + (f" ({len(newly_unlocked)} new achievements)" if newly_unlocked else "")
            )

        self.stdout.write(
            self.style.SUCCESS(
                f"Synced XP for {checked} users; unlocked {unlocked_count} achievements."
            )
        )
