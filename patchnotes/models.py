# patchnotes/models.py
from django.db import models


class PatchNote(models.Model):
    """A changelog entry documenting a game or platform update."""
    version = models.CharField(max_length=20, help_text="Semantic version, e.g. '1.2.0'")
    title = models.CharField(max_length=255)
    body = models.TextField(help_text="Markdown-formatted changelog body.")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"v{self.version} — {self.title}"


class DownloadLink(models.Model):
    """Stores the current download URL for each platform.
    Enforced unique per platform so there's only one active link."""
    PLATFORM_CHOICES = [
        ('windows', 'Windows'),
        ('macos', 'macOS'),
    ]
    platform = models.CharField(max_length=10, choices=PLATFORM_CHOICES, unique=True)
    url = models.URLField(max_length=500, help_text="Direct download link (Google Drive, GitHub Releases, etc.)")
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.get_platform_display()} — {self.url[:60]}"
