# app/views.py
from django.http import JsonResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Tutorial, TutorialStep, UserTutorialEnrollment
from django.core.exceptions import ObjectDoesNotExist
from rest_framework.permissions import IsAuthenticated

class TutorialListView(APIView):
    permission_classes = [IsAuthenticated]  # Public access
    def get(self, request):
        tutorials = Tutorial.objects.filter(is_active=True)
        data = [
            {
                'id': t.id,
                'title': t.title,
                'description': t.description,
                'steps': [
                    {
                        'id': s.id,
                        'title': s.title,
                        'content': s.content,
                        'initialCode': s.initial_code,
                        'solutionCode': s.solution_code,
                        'expectedElements': s.get_expected_elements(),
                        'fileType': s.file_type,
                        'order': s.order,
                    } for s in t.steps.all()
                ]
            } for t in tutorials
        ]
        return Response(data)

class UserProgressView(APIView):
    permission_classes = [IsAuthenticated]  # Require login

    def get(self, request):
        enrollments = UserTutorialEnrollment.objects.filter(user=request.user)
        progress_data = {
            enrollment.tutorial.id: {
                'currentTutorial': enrollment.tutorial.id,
                'currentStep': enrollment.current_step.order if enrollment.current_step else 1,
                'isCompleted': enrollment.is_completed,
            } for enrollment in enrollments
        }
        return Response(progress_data)

    def post(self, request):
        data = request.data
        tutorial_id = data.get('tutorialId')
        step_order = data.get('stepIndex')  # Changed to step_order for clarity
        code = data.get('code')

        try:
            tutorial = Tutorial.objects.get(id=tutorial_id)
            step = TutorialStep.objects.get(tutorial=tutorial, order=step_order)
            enrollment, created = UserTutorialEnrollment.objects.get_or_create(
                user=request.user,
                tutorial=tutorial,
                defaults={'current_step': step}
            )
            if not enrollment.is_completed:
                submission, _ = UserStepSubmission.objects.update_or_create(
                    enrollment=enrollment,
                    step=step,
                    defaults={'user_code': code}
                )
                enrollment.current_step = step
                enrollment.save()
            return Response({'status': 'Progress saved'}, status=status.HTTP_200_OK)
        except ObjectDoesNotExist:
            return Response({'error': 'Invalid tutorial or step'}, status=status.HTTP_404_NOT_FOUND)

class CheckCodeView(APIView):
    def post(self, request):
        data = request.data
        tutorial_id = data.get('tutorialId')
        step_index = data.get('stepIndex')
        user_code = data.get('code')
        
        try:
            tutorial = Tutorial.objects.get(id=tutorial_id)
            step = tutorial.steps.get(order=step_index)
            expected = step.get_expected_elements()
            success = all(elem in user_code for elem in expected) if expected else True
            output = "Code matches expectations!" if success else "Code doesn't match expected elements."
            return Response({'success': success, 'output': output})
        except ObjectDoesNotExist:
            return Response({'error': 'Invalid tutorial or step'}, status=status.HTTP_404_NOT_FOUND)

class TutorialCompleteView(APIView):
    def post(self, request, tutorial_id):
        try:
            tutorial = Tutorial.objects.get(id=tutorial_id)
            next_tutorial = Tutorial.objects.filter(order__gt=tutorial.order, is_active=True).first()
            return Response({
                'nextTutorial': next_tutorial.id if next_tutorial else None
            })
        except ObjectDoesNotExist:
            return Response({'error': 'Tutorial not found'}, status=status.HTTP_404_NOT_FOUND)