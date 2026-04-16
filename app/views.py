# app/views.py
from bs4 import BeautifulSoup
import cssutils
import ast
from django.http import JsonResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Tutorial, TutorialStep, UserTutorialEnrollment, UserStepSubmission
from django.core.exceptions import ObjectDoesNotExist
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
import re

# Default base.html shown to students in the read-only tab and used for rendering
DEFAULT_BASE_TEMPLATE = (
    '<!DOCTYPE html>\n'
    '<html lang="en">\n'
    '<head>\n'
    '    <meta charset="UTF-8">\n'
    '    <meta name="viewport" content="width=device-width, initial-scale=1.0">\n'
    '    <title>{% block title %}DjangoQuest{% endblock %}</title>\n'
    '    <style>\n'
    '        * { box-sizing: border-box; margin: 0; padding: 0; }\n'
    '        body { font-family: Arial, sans-serif; padding: 20px; background: #f9f9f9; color: #222; }\n'
    '        h1 { font-size: 1.8rem; margin-bottom: 12px; color: #1a1a2e; }\n'
    '        h2 { font-size: 1.3rem; margin: 10px 0 6px; color: #333; }\n'
    '        p  { margin-bottom: 10px; line-height: 1.5; }\n'
    '        a  { color: #0077cc; }\n'
    '        nav { background: #1a1a2e; padding: 12px 20px; margin: -20px -20px 20px; }\n'
    '        nav a { color: white; margin-right: 16px; text-decoration: none; font-weight: bold; }\n'
    '        article { background: white; border: 1px solid #ddd; border-radius: 6px; padding: 16px; margin-bottom: 12px; }\n'
    '        .container { max-width: 800px; margin: 0 auto; }\n'
    '    </style>\n'
    '</head>\n'
    '<body>\n'
    '    {% block content %}{% endblock %}\n'
    '</body>\n'
    '</html>'
)

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
                        'baseTemplate': s.base_template or DEFAULT_BASE_TEMPLATE,
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

        try:
            tutorial = Tutorial.objects.get(id=tutorial_id)
            step = TutorialStep.objects.get(tutorial=tutorial, order=step_index)
        except ObjectDoesNotExist:
            return Response({'error': 'Tutorial or step not found'}, status=status.HTTP_404_NOT_FOUND)

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
        elif step.file_type == 'python':
            # Python code validation — check syntax first, then expected elements
            try:
                ast.parse(user_code)
            except SyntaxError as e:
                return Response({
                    'success': False,
                    'output': f"SyntaxError on line {e.lineno}: {e.msg}"
                })

            for element in expected_elements:
                if element not in user_code:
                    return Response({
                        'success': False,
                        'output': f"Missing expected code: {element}"
                    })

        elif step.file_type == 'django':
            # Django template validation — check for template tags and variables
            for element in expected_elements:
                if element not in user_code:
                    # Give a helpful hint based on what's missing
                    if '{%' in element:
                        return Response({
                            'success': False,
                            'output': f"Missing Django template tag: {element}"
                        })
                    elif '{{' in element:
                        return Response({
                            'success': False,
                            'output': f"Missing template variable: {element}"
                        })
                    else:
                        return Response({
                            'success': False,
                            'output': f"Missing expected code: {element}"
                        })

        else:
            # Fallback for any other file type — basic string matching
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
    permission_classes = [IsAuthenticated]

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
        # Delete submissions first (FK to enrollment), then enrollments
        UserStepSubmission.objects.filter(enrollment__user=user).delete()
        UserTutorialEnrollment.objects.filter(user=user).delete()
        # Reset XP
        user.profile.total_xp = 0
        user.profile.save()
        return Response({'success': True, 'message': 'Tutorial progress has been reset.'})


# Default base.html used when a step doesn't define its own
DEFAULT_BASE_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}DjangoQuest{% endblock %}</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { font-family: Arial, sans-serif; padding: 20px; background: #f9f9f9; color: #222; }
        h1 { font-size: 1.8rem; margin-bottom: 12px; color: #1a1a2e; }
        h2 { font-size: 1.3rem; margin: 10px 0 6px; color: #333; }
        p  { margin-bottom: 10px; line-height: 1.5; }
        a  { color: #0077cc; }
        nav { background: #1a1a2e; padding: 12px 20px; margin: -20px -20px 20px; }
        nav a { color: white; margin-right: 16px; text-decoration: none; font-weight: bold; }
        article { background: white; border: 1px solid #ddd; border-radius: 6px; padding: 16px; margin-bottom: 12px; }
        .container { max-width: 800px; margin: 0 auto; }
        ul { margin-left: 20px; }
        li { margin-bottom: 6px; }
        form label { display: block; margin-bottom: 4px; font-weight: bold; }
        form input, form textarea { width: 100%; padding: 8px; margin-bottom: 12px; border: 1px solid #ccc; border-radius: 4px; }
        form button { background: #0077cc; color: white; padding: 8px 20px; border: none; border-radius: 4px; cursor: pointer; }
    </style>
</head>
<body>
    {% block content %}{% endblock %}
</body>
</html>"""


class RenderDjangoTemplateView(APIView):
    """
    Renders the student's Django template server-side using Django's built-in
    locmem.Loader — making an in-memory base.html available without real files.
    Returns rendered HTML for the live preview iframe.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        import json as _json
        from django.template import Context, Origin
        from django.template.engine import Engine
        from django.template.exceptions import TemplateSyntaxError, TemplateDoesNotExist

        template_code = request.data.get('code', '')
        tutorial_id = request.data.get('tutorialId')
        step_index = request.data.get('stepIndex')

        # Fetch the step to get per-step base_template and preview_context
        base_html = DEFAULT_BASE_TEMPLATE
        context_data = {
            'title': 'My Blog',
            'posts': [
                {'title': 'Hello Django', 'body': 'This is my first post.', 'pk': 1},
                {'title': 'Generic Views', 'body': 'Class-based views are powerful.', 'pk': 2},
                {'title': 'ORM Queries', 'body': 'Django ORM makes database queries easy.', 'pk': 3},
            ],
            'post': {'title': 'Hello Django', 'body': 'This is my first post.', 'pk': 1},
            'user': {'username': 'student', 'is_authenticated': True},
            'STATIC_URL': '/static/',
        }

        if tutorial_id and step_index:
            try:
                tutorial = Tutorial.objects.get(id=tutorial_id)
                step = TutorialStep.objects.get(tutorial=tutorial, order=step_index)
                if step.base_template:
                    base_html = step.base_template
                if step.preview_context:
                    context_data.update(_json.loads(step.preview_context))
            except (ObjectDoesNotExist, _json.JSONDecodeError):
                pass  # Fall through to defaults

        try:
            # Create a custom in-memory Engine with locmem loader
            # This makes base.html available without a real file
            engine = Engine(
                dirs=[],
                loaders=[
                    ('django.template.loaders.locmem.Loader', {
                        'base.html': base_html,
                    }),
                ],
                libraries={
                    'static': 'django.templatetags.static',
                },
                builtins=['django.templatetags.static'],
            )

            template = engine.from_string(template_code)
            rendered_html = template.render(Context(context_data))
            return Response({'html': rendered_html, 'success': True})

        except TemplateSyntaxError as e:
            error_html = f"""<!DOCTYPE html><html><body style="font-family:monospace;padding:20px;background:#fef2f2;color:#991b1b;">
<h3 style="margin-bottom:10px;">⚠️ Template Syntax Error</h3>
<pre style="background:#fee2e2;padding:12px;border-radius:4px;overflow:auto;">{str(e)}</pre>
<p style="margin-top:12px;color:#666;">Check your template tags — make sure every <code>{{% block %}}</code> has a matching <code>{{% endblock %}}</code>.</p>
</body></html>"""
            return Response({'html': error_html, 'success': False})

        except Exception as e:
            error_html = f"""<!DOCTYPE html><html><body style="font-family:monospace;padding:20px;background:#fef2f2;color:#991b1b;">
<h3 style="margin-bottom:10px;">⚠️ Render Error</h3>
<pre style="background:#fee2e2;padding:12px;border-radius:4px;overflow:auto;">{str(e)}</pre>
</body></html>"""
            return Response({'html': error_html, 'success': False})