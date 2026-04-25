# feedback/views.py
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Feedback
from .serializers import FeedbackCreateSerializer


class FeedbackCreateView(APIView):
    """POST /api/feedback/ — Submit feedback (any authenticated user)."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = FeedbackCreateSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            feedback = serializer.save()
            return Response({
                'id': feedback.id,
                'feedback_type': feedback.feedback_type,
                'rating': feedback.rating,
                'message': 'Thank you for your feedback!'
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class FeedbackMineView(APIView):
    """GET /api/feedback/mine/ — Count of current user's feedback submissions."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        count = Feedback.objects.filter(user=request.user).count()
        return Response({'count': count})
