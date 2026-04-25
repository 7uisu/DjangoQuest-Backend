# feedback/models.py
from django.db import models
from django.conf import settings


class Feedback(models.Model):
    FEEDBACK_TYPES = [
        ('game', 'Game'),
        ('website', 'Website'),
        ('classroom', 'Classroom'),
    ]
    ROLE_CHOICES = [
        ('student', 'Student'),
        ('teacher', 'Teacher'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='feedbacks'
    )
    role_snapshot = models.CharField(max_length=10, choices=ROLE_CHOICES)
    feedback_type = models.CharField(max_length=10, choices=FEEDBACK_TYPES)
    rating = models.PositiveSmallIntegerField()  # 1-5
    comments = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    # Classroom context
    classroom = models.ForeignKey(
        'users.Classroom',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='feedbacks'
    )

    # Teacher-only fields
    game_level = models.CharField(max_length=100, blank=True)
    curriculum_relevance_rating = models.PositiveSmallIntegerField(null=True, blank=True)
    website_usability_notes = models.TextField(blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.role_snapshot} | {self.feedback_type} | {self.rating}★"
