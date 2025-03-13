# Generated by Django 5.1.6 on 2025-03-13 02:35

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('app', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='usertutorialenrollment',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='tutorial_enrollments', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='userstepsubmission',
            name='enrollment',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='step_submissions', to='app.usertutorialenrollment'),
        ),
        migrations.AlterUniqueTogether(
            name='tutorialstep',
            unique_together={('tutorial', 'order')},
        ),
        migrations.AlterUniqueTogether(
            name='usertutorialenrollment',
            unique_together={('user', 'tutorial')},
        ),
        migrations.AlterUniqueTogether(
            name='userstepsubmission',
            unique_together={('enrollment', 'step')},
        ),
    ]
