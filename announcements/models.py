# announcements/models.py
from django.db import models
from django.conf import settings


class Announcement(models.Model):
    ANNOUNCEMENT_TYPES = [
        ('platform', 'Platform'),
        ('classroom', 'Classroom'),
    ]

    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='announcements',
    )
    announcement_type = models.CharField(max_length=10, choices=ANNOUNCEMENT_TYPES)
    title = models.CharField(max_length=255)
    body = models.TextField()
    target_classrooms = models.ManyToManyField(
        'users.Classroom',
        blank=True,
        related_name='announcements',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"[{self.announcement_type}] {self.title}"
