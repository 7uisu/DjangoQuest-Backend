# app/views.py
from bs4 import BeautifulSoup
import cssutils
from django.http import JsonResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Tutorial, TutorialStep, UserTutorialEnrollment, UserStepSubmission
from django.core.exceptions import ObjectDoesNotExist
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
import re

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
                        'trivia': s.trivia,
                    } for s in t.steps.all()
                ]
            } for t in tutorials
        ]
        return Response(data)

class UserProgressView(APIView):
    permission_classes = [IsAuthenticated]

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
        step_order = data.get('stepIndex')  # Step order, not index
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
                # Check if all steps are completed
                total_steps = tutorial.steps.count()
                completed_steps = UserStepSubmission.objects.filter(enrollment=enrollment).count()
                if completed_steps == total_steps:
                    enrollment.is_completed = True
                enrollment.save()
            return Response({'status': 'Progress saved'}, status=status.HTTP_200_OK)
        except ObjectDoesNotExist:
            return Response({'error': 'Invalid tutorial or step'}, status=status.HTTP_404_NOT_FOUND)

class CheckCodeView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        tutorial_id = request.data.get('tutorialId')
        step_index = request.data.get('stepIndex')
        user_code = request.data.get('code')

        tutorial = Tutorial.objects.get(id=tutorial_id)
        step = TutorialStep.objects.get(tutorial=tutorial, order=step_index)
        expected_elements = step.get_expected_elements()

        # Ensure enrollment exists
        enrollment, created = UserTutorialEnrollment.objects.get_or_create(
            user=request.user,
            tutorial=tutorial,
            defaults={'current_step': step}
        )

        if step.file_type == 'html+css':
            # Existing HTML+CSS checking logic
            try:
                html_part, css_part = user_code.split('\nstyles.css:')
                html_code = html_part.replace('index.html:', '').strip()
                css_code = css_part.strip()
            except ValueError:
                return Response({'success': False, 'output': 'Code must include both index.html and styles.css sections separated by "\\nstyles.css:"'})

            soup = BeautifulSoup(html_code, 'html.parser')
            parser = cssutils.CSSParser()
            try:
                stylesheet = parser.parseString(css_code)
            except Exception:
                return Response({'success': False, 'output': 'Invalid CSS syntax'})

            def normalize_css(css):
                return re.sub(r'\s+', ' ', css.strip())

            for element in expected_elements:
                if '<link' in element:
                    if element not in html_code:
                        return Response({'success': False, 'output': f"Missing HTML element: {element}"})
                elif '{' in element:
                    normalized_css = normalize_css(css_code)
                    normalized_expected = normalize_css(element)
                    if not css_code or normalized_expected not in normalized_css:
                        return Response({'success': False, 'output': f"Missing CSS rule: {element}"})
                elif '.' in element and not element.startswith('.'):
                    tag, class_name = element.split('.', 1)
                    if not soup.find(tag, class_=class_name):
                        return Response({'success': False, 'output': f"Missing HTML element: {element}"})
                elif element.startswith('.') or element.startswith('#'):
                    if css_code and element not in css_code:
                        return Response({'success': False, 'output': f"Missing CSS selector: {element}"})
                else:
                    if element not in html_code:
                        return Response({'success': False, 'output': f"Missing HTML element: {element}"})
        else:
            soup = BeautifulSoup(user_code, 'html.parser')
            for element in expected_elements:
                if element not in user_code:
                    return Response({'success': False, 'output': f"Missing {element}"})

        submission, created = UserStepSubmission.objects.get_or_create(
            enrollment=enrollment,  # Use the enrollment we just ensured
            step=step
        )
        submission.user_code = user_code
        submission.attempt_count += 1
        if not submission.is_completed:
            submission.is_completed = True
            submission.completed_at = timezone.now()
            request.user.profile.total_xp += step.checkpoint_xp
            request.user.profile.save()
        submission.save()

        return Response({'success': True, 'output': 'Code is correct!'})

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
        
class ResetProgressView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        # Delete all tutorial enrollments and submissions
        UserTutorialEnrollment.objects.filter(user=user).delete()
        UserStepSubmission.objects.filter(enrollment__user=user).delete()
        # Reset XP
        user.profile.total_xp = 0
        user.profile.save()
        return Response({'success': True, 'message': 'Tutorial progress has been reset.'})