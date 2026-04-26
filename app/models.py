from django.db import models
from django.core.exceptions import ValidationError
import json
from users.models import User





# ──────────────────────────────────────────────
# VIDEO TUTORIALS
# ──────────────────────────────────────────────

class VideoTutorial(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    video_url = models.URLField(help_text="YouTube URL for the tutorial video")
    topic = models.CharField(
        max_length=50,
        blank=True,
        default='',
        help_text="e.g., HTML, CSS, Django"
    )
    order = models.IntegerField(
        help_text="Display order among video tutorials"
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['order']


class VideoStep(models.Model):
    tutorial = models.ForeignKey(
        VideoTutorial,
        on_delete=models.CASCADE,
        related_name='steps'
    )
    title = models.CharField(max_length=255)
    content = models.TextField(
        help_text="Text log describing what is covered at this point in the video"
    )
    order = models.IntegerField()

    def __str__(self):
        return f"{self.tutorial.title} — Step {self.order}: {self.title}"

    class Meta:
        ordering = ['tutorial', 'order']
        unique_together = ['tutorial', 'order']


class UserVideoEnrollment(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='video_enrollments'
    )
    tutorial = models.ForeignKey(
        VideoTutorial,
        on_delete=models.CASCADE,
        related_name='enrollments'
    )
    is_completed = models.BooleanField(default=False)
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        status = "Completed" if self.is_completed else "In Progress"
        return f"{self.user.username} — {self.tutorial.title} ({status})"

    class Meta:
        unique_together = ['user', 'tutorial']


class UserVideoStepView(models.Model):
    enrollment = models.ForeignKey(
        UserVideoEnrollment,
        on_delete=models.CASCADE,
        related_name='step_views'
    )
    step = models.ForeignKey(
        VideoStep,
        on_delete=models.CASCADE
    )
    viewed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.enrollment.user.username} — {self.step.title}"

    class Meta:
        unique_together = ['enrollment', 'step']
