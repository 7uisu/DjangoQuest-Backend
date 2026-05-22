from django.db import migrations, models


def copy_primary_classroom_to_memberships(apps, _schema_editor):
    Profile = apps.get_model('users', 'Profile')
    for profile in Profile.objects.exclude(classroom__isnull=True):
        profile.classrooms.add(profile.classroom)


def remove_copied_memberships(apps, _schema_editor):
    Profile = apps.get_model('users', 'Profile')
    for profile in Profile.objects.exclude(classroom__isnull=True):
        profile.classrooms.remove(profile.classroom)


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0006_alter_user_is_student_alter_user_is_teacher'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='classrooms',
            field=models.ManyToManyField(blank=True, help_text='All classrooms this student is enrolled in.', related_name='enrolled_profiles', to='users.classroom'),
        ),
        migrations.RunPython(copy_primary_classroom_to_memberships, remove_copied_memberships),
    ]
