# app/admin_views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAdminUser
from .models import VideoTutorial, VideoStep


# ==========================================
# VIDEO TUTORIAL ADMIN APIs
# ==========================================

class AdminVideoTutorialListView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        tutorials = VideoTutorial.objects.all().order_by('order')
        data = [{
            'id': t.id,
            'title': t.title,
            'description': t.description,
            'video_url': t.video_url,
            'topic': t.topic,
            'order': t.order,
            'is_active': t.is_active,
            'step_count': t.steps.count()
        } for t in tutorials]
        return Response(data)

    def post(self, request):
        data = request.data
        if not data.get('title') or data.get('order') is None:
            return Response({'error': 'Title and order are required'}, status=status.HTTP_400_BAD_REQUEST)
        
        tutorial = VideoTutorial.objects.create(
            title=data['title'],
            description=data.get('description', ''),
            video_url=data.get('video_url', ''),
            topic=data.get('topic', ''),
            order=data['order'],
            is_active=data.get('is_active', True)
        )
        return Response({
            'id': tutorial.id,
            'title': tutorial.title,
            'order': tutorial.order
        }, status=status.HTTP_201_CREATED)

class AdminVideoTutorialDetailView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request, pk):
        t = get_object_or_404(VideoTutorial, pk=pk)
        data = {
            'id': t.id,
            'title': t.title,
            'description': t.description,
            'video_url': t.video_url,
            'topic': t.topic,
            'order': t.order,
            'is_active': t.is_active,
            'tutorial_type': 'video',
            'steps': [{
                'id': s.id,
                'title': s.title,
                'order': s.order
            } for s in t.steps.all().order_by('order')]
        }
        return Response(data)

    def put(self, request, pk):
        t = get_object_or_404(VideoTutorial, pk=pk)
        data = request.data
        t.title = data.get('title', t.title)
        t.description = data.get('description', t.description)
        t.video_url = data.get('video_url', t.video_url)
        t.topic = data.get('topic', t.topic)
        if data.get('order') is not None:
            t.order = data['order']
        if data.get('is_active') is not None:
            t.is_active = data['is_active']
        t.save()
        return Response({'message': 'Tutorial updated successfully'})

    def delete(self, request, pk):
        t = get_object_or_404(VideoTutorial, pk=pk)
        t.delete()
        return Response({'message': 'Tutorial deleted'}, status=status.HTTP_204_NO_CONTENT)

class AdminVideoStepListView(APIView):
    permission_classes = [IsAdminUser]

    def post(self, request, tutorial_id):
        t = get_object_or_404(VideoTutorial, pk=tutorial_id)
        data = request.data
        
        step = VideoStep.objects.create(
            tutorial=t,
            title=data.get('title', 'New Log'),
            content=data.get('content', ''),
            order=data.get('order', t.steps.count() + 1)
        )
        return Response({'id': step.id, 'title': step.title}, status=status.HTTP_201_CREATED)

class AdminVideoStepDetailView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request, pk):
        step = get_object_or_404(VideoStep, pk=pk)
        data = {
            'id': step.id,
            'tutorial_id': step.tutorial_id,
            'title': step.title,
            'content': step.content,
            'order': step.order
        }
        return Response(data)

    def put(self, request, pk):
        step = get_object_or_404(VideoStep, pk=pk)
        data = request.data
        
        step.title = data.get('title', step.title)
        step.content = data.get('content', step.content)
        if data.get('order') is not None:
            step.order = data['order']
        
        step.save()
        return Response({'message': 'Log updated successfully'})

    def delete(self, request, pk):
        step = get_object_or_404(VideoStep, pk=pk)
        step.delete()
        return Response({'message': 'Log deleted'}, status=status.HTTP_204_NO_CONTENT)
