# app/views.py
from bs4 import BeautifulSoup
import cssutils
import ast
from django.http import JsonResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import (
    VideoTutorial, VideoStep, UserVideoEnrollment, UserVideoStepView
)
from django.core.exceptions import ObjectDoesNotExist
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
import re

DEFAULT_BASE_TEMPLATE = (
    '<!DOCTYPE html>\n<html lang="en">\n<head>\n'
    '    <meta charset="UTF-8">\n    <meta name="viewport" content="width=device-width, initial-scale=1.0">\n'
    '    <title>{% block title %}DjangoQuest{% endblock %}</title>\n'
    '    <style>\n        * { box-sizing: border-box; margin: 0; padding: 0; }\n'
    '        body { font-family: Arial, sans-serif; padding: 20px; background: #f9f9f9; color: #222; }\n'
    '        h1 { font-size: 1.8rem; margin-bottom: 12px; color: #1a1a2e; }\n'
    '        h2 { font-size: 1.3rem; margin: 10px 0 6px; color: #333; }\n'
    '        p  { margin-bottom: 10px; line-height: 1.5; }\n'
    '        a  { color: #0077cc; }\n'
    '        nav { background: #1a1a2e; padding: 12px 20px; margin: -20px -20px 20px; }\n'
    '        nav a { color: white; margin-right: 16px; text-decoration: none; font-weight: bold; }\n'
    '        article { background: white; border: 1px solid #ddd; border-radius: 6px; padding: 16px; margin-bottom: 12px; }\n'
    '        .container { max-width: 800px; margin: 0 auto; }\n'
    '    </style>\n</head>\n<body>\n    {% block content %}{% endblock %}\n</body>\n</html>'
)

# ===============================================
# VIDEO VIEWS
# ===============================================

class VideoTutorialListView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        tutorials = VideoTutorial.objects.filter(is_active=True)
        data = [{
            'id': t.id,
            'title': t.title,
            'description': t.description,
            'videoUrl': t.video_url,
            'topic': t.topic,
            'tutorial_type': 'video',
            'order': t.order,
            'steps': [{
                'id': s.id,
                'title': s.title,
                'content': s.content,
                'order': s.order,
            } for s in t.steps.all()]
        } for t in tutorials]
        return Response(data)

class VideoProgressView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        enrollments = UserVideoEnrollment.objects.filter(user=request.user)
        progress_data = {
            enrollment.tutorial.id: {
                'currentTutorial': enrollment.tutorial.id,
                'isCompleted': enrollment.is_completed,
            } for enrollment in enrollments
        }
        return Response(progress_data)

    def post(self, request):
        data = request.data
        tutorial_id = data.get('tutorialId')
        step_order = data.get('stepIndex')
        try:
            tutorial = VideoTutorial.objects.get(id=tutorial_id)
            step = VideoStep.objects.get(tutorial=tutorial, order=step_order)
            enrollment, _ = UserVideoEnrollment.objects.get_or_create(user=request.user, tutorial=tutorial)
            UserVideoStepView.objects.get_or_create(enrollment=enrollment, step=step)

            if UserVideoStepView.objects.filter(enrollment=enrollment).count() == tutorial.steps.count():
                enrollment.is_completed = True
                enrollment.completed_at = timezone.now()
            enrollment.save()
            return Response({'status': 'Progress saved'}, status=status.HTTP_200_OK)
        except ObjectDoesNotExist:
            return Response({'error': 'Invalid tutorial or step'}, status=status.HTTP_404_NOT_FOUND)

class VideoCompleteView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request, tutorial_id):
        try:
            tutorial = VideoTutorial.objects.get(id=tutorial_id)
            next_tutorial = VideoTutorial.objects.filter(order__gt=tutorial.order, is_active=True).first()
            return Response({'nextTutorial': next_tutorial.id if next_tutorial else None})
        except ObjectDoesNotExist:
            return Response({'error': 'Tutorial not found'}, status=status.HTTP_404_NOT_FOUND)

class ResetProgressView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request):
        user = request.user
        UserVideoStepView.objects.filter(enrollment__user=user).delete()
        UserVideoEnrollment.objects.filter(user=user).delete()
        user.profile.total_xp = 0
        user.profile.save()
        return Response({'success': True, 'message': 'All tutorial progress has been reset.'})