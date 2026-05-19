import json
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from app.models import VideoStep, VideoTutorial


class Command(BaseCommand):
    help = "Upserts video tutorials and video steps from app/fixtures/video_tutorials.json."

    def add_arguments(self, parser):
        parser.add_argument(
            "--fixture",
            default="app/fixtures/video_tutorials.json",
            help="Path to the video tutorial fixture JSON file.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        fixture_path = Path(options["fixture"])
        if not fixture_path.exists():
            raise CommandError(f"Fixture not found: {fixture_path}")

        with fixture_path.open("r", encoding="utf-8") as fixture_file:
            records = json.load(fixture_file)

        tutorial_pk_map = {}
        tutorials_created = 0
        tutorials_updated = 0
        steps_created = 0
        steps_updated = 0

        for record in records:
            if record.get("model") != "app.videotutorial":
                continue

            fields = record["fields"]
            tutorial, created = VideoTutorial.objects.update_or_create(
                title=fields["title"],
                defaults={
                    "description": fields["description"],
                    "video_url": fields["video_url"],
                    "topic": fields.get("topic", ""),
                    "order": fields["order"],
                    "is_active": fields["is_active"],
                },
            )
            tutorial_pk_map[record["pk"]] = tutorial
            if created:
                tutorials_created += 1
            else:
                tutorials_updated += 1

        for record in records:
            if record.get("model") != "app.videostep":
                continue

            fields = record["fields"]
            local_tutorial_pk = fields["tutorial"]
            tutorial = tutorial_pk_map.get(local_tutorial_pk)
            if tutorial is None:
                raise CommandError(
                    f"Step '{fields['title']}' references missing tutorial pk {local_tutorial_pk}."
                )

            _step, created = VideoStep.objects.update_or_create(
                tutorial=tutorial,
                order=fields["order"],
                defaults={
                    "title": fields["title"],
                    "content": fields["content"],
                },
            )
            if created:
                steps_created += 1
            else:
                steps_updated += 1

        self.stdout.write(
            self.style.SUCCESS(
                "Video tutorials seeded: "
                f"{tutorials_created} tutorials created, {tutorials_updated} updated; "
                f"{steps_created} steps created, {steps_updated} updated."
            )
        )
