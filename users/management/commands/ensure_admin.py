from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from decouple import config
from users.models import Profile


class Command(BaseCommand):
    help = 'Create or update a superuser from environment variables.'

    def handle(self, *args, **options):
        email = config('DJANGO_SUPERUSER_EMAIL', default='').strip()
        username = config('DJANGO_SUPERUSER_USERNAME', default='').strip()
        password = config('DJANGO_SUPERUSER_PASSWORD', default='')

        if not email or not username or not password:
            self.stdout.write('Admin env vars not set; skipping admin bootstrap.')
            return

        User = get_user_model()
        user, created = User.objects.get_or_create(
            email=email,
            defaults={
                'username': username,
                'is_staff': True,
                'is_superuser': True,
                'is_active': True,
                'is_teacher': True,
                'is_student': False,
            },
        )

        user.username = username
        user.is_staff = True
        user.is_superuser = True
        user.is_active = True
        user.is_teacher = True
        user.is_student = False
        user.set_password(password)
        user.save()
        Profile.objects.get_or_create(user=user)

        action = 'Created' if created else 'Updated'
        self.stdout.write(self.style.SUCCESS(f'{action} admin account for {email}.'))
