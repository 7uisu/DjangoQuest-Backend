from django.db import models
from django.core.exceptions import ValidationError
import json
from users.models import User

class Tutorial(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    order = models.IntegerField(unique=True)
    prerequisite = models.ForeignKey(
        'self', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='unlocks'
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.title
    
    class Meta:
        ordering = ['order']

class TutorialStep(models.Model):
    FILE_TYPE_CHOICES = (
        ('python', 'Python'),
        ('html', 'HTML'),
        ('css', 'CSS'),
        ('js', 'JavaScript'),
        ('django', 'Django Template'),
        ('html+css', 'HTML + CSS'),
    )
    
    tutorial = models.ForeignKey(Tutorial, on_delete=models.CASCADE, related_name="steps")
    title = models.CharField(max_length=255)
    content = models.TextField(help_text="HTML content with instructions")
    order = models.IntegerField()
    file_type = models.CharField(max_length=20, choices=FILE_TYPE_CHOICES, default='python')
    initial_code = models.TextField(blank=True, help_text="Starting code the user will see")
    solution_code = models.TextField(help_text="Complete solution code")
    trivia = models.TextField(blank=True, null=True, help_text="Trivia shown after completing this step"
    )
    expected_elements = models.TextField(
        blank=True, 
        help_text="JSON array of strings or patterns that should be in user's code"
    )
    checkpoint_xp = models.IntegerField(default=10, help_text="XP awarded for completing this step")
    
    def clean(self):
        # Validate that expected_elements is valid JSON
        if self.expected_elements:
            try:
                json.loads(self.expected_elements)
            except json.JSONDecodeError:
                raise ValidationError({'expected_elements': 'Must be valid JSON array'})
    
    def get_expected_elements(self):
        """Return expected elements as a Python list"""
        if not self.expected_elements:
            return []
        return json.loads(self.expected_elements)
    
    def __str__(self):
        return f"{self.tutorial.title} - Step {self.order}: {self.title}"
    
    class Meta:
        ordering = ['tutorial', 'order']
        unique_together = ['tutorial', 'order']

class UserTutorialEnrollment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="tutorial_enrollments")
    tutorial = models.ForeignKey(Tutorial, on_delete=models.CASCADE)
    is_completed = models.BooleanField(default=False)
    current_step = models.ForeignKey(
        TutorialStep, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name="+"
    )
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        status = "Completed" if self.is_completed else "In Progress"
        return f"{self.user.username} - {self.tutorial.title} ({status})"
    
    class Meta:
        unique_together = ['user', 'tutorial']

class UserStepSubmission(models.Model):
    enrollment = models.ForeignKey(
        UserTutorialEnrollment, 
        on_delete=models.CASCADE, 
        related_name="step_submissions"
    )
    step = models.ForeignKey(TutorialStep, on_delete=models.CASCADE)
    user_code = models.TextField()
    is_completed = models.BooleanField(default=False)
    attempt_count = models.IntegerField(default=1)
    last_attempt_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        status = "Completed" if self.is_completed else "In Progress"
        return f"{self.enrollment.user.username} - {self.step.title} ({status})"
    
    class Meta:
        unique_together = ['enrollment', 'step']
