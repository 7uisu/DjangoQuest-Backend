# game_api/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate, get_user_model
from users.models import Classroom, Profile
from .models import GameSave
from decouple import config
import requests as http_requests
import json
import time
import re

User = get_user_model()

# ─── Configuration ───────────────────────────────────────────────────────────
JUDGE0_API_URL = config('JUDGE0_API_URL', default='http://localhost:2358')
JUDGE0_AUTH_TOKEN = config('JUDGE0_AUTH_TOKEN', default='')
GEMINI_API_KEY = config('GEMINI_API_KEY', default='')

# Judge0 Language IDs
JUDGE0_LANGUAGES = {
    'python': 71,     # Python 3.8.1
    'html': None,     # Not executed — validated via string matching
    'css': None,
    'django': 71,     # Django templates validated, Python parts executed
}


class GameLoginView(APIView):
    """
    POST /api/game/login/
    Accepts email + password from the Godot game client.
    Only students may log in through the game.
    Returns JWT access/refresh tokens AND the username.
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        email = request.data.get('email', '').strip()
        password = request.data.get('password', '')

        if not email or not password:
            return Response(
                {'detail': 'Email and password are required.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = authenticate(request, email=email, password=password)

        if user is None:
            return Response(
                {'detail': 'Invalid email or password.'},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        # Both students and teachers can log into the game
        refresh = RefreshToken.for_user(user)

        return Response({
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'username': user.username,
        }, status=status.HTTP_200_OK)


class GameEnrollView(APIView):
    """
    POST /api/game/enroll/
    Accepts an enrollment_code from the Godot game client.
    Links the authenticated student to the matching Classroom.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        enrollment_code = request.data.get('enrollment_code', '').strip().upper()

        if not enrollment_code:
            return Response(
                {'detail': 'Enrollment code is required.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            classroom = Classroom.objects.get(enrollment_code=enrollment_code)
        except Classroom.DoesNotExist:
            return Response(
                {'detail': 'Invalid enrollment code.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        profile, _ = Profile.objects.get_or_create(user=request.user)
        profile.classroom = classroom
        profile.save()

        return Response({
            'detail': 'Successfully enrolled!',
            'classroom_name': classroom.name,
            'teacher': classroom.teacher.username,
        }, status=status.HTTP_200_OK)


class GameUnenrollView(APIView):
    """
    POST /api/game/unenroll/
    Removes the authenticated student from their current classroom.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        if not hasattr(request.user, 'profile') or not request.user.profile.classroom:
            return Response(
                {"detail": "You are not enrolled in any classroom."},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        classroom_name = request.user.profile.classroom.name
        request.user.profile.classroom = None
        request.user.profile.save()
        
        return Response({"detail": f"Successfully unenrolled from {classroom_name}."}, status=status.HTTP_200_OK)


class GameSaveView(APIView):
    """
    PUT    /api/game/save/   — Upload / update the authenticated user's save.
    GET    /api/game/save/   — Download the authenticated user's save.
    DELETE /api/game/save/   — Delete the authenticated user's save.
    """
    permission_classes = [permissions.IsAuthenticated]

    def put(self, request):
        save_data = request.data.get('save_data')
        if save_data is None or not isinstance(save_data, dict):
            return Response(
                {'detail': 'save_data (JSON object) is required.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        progress = GameSave.compute_progress(save_data)

        game_save, _created = GameSave.objects.update_or_create(
            user=request.user,
            defaults={
                'save_data': save_data,
                **progress,
            },
        )

        return Response({
            'detail': 'Save uploaded successfully.',
            'updated_at': game_save.updated_at.isoformat(),
        }, status=status.HTTP_200_OK)

    def get(self, request):
        try:
            game_save = GameSave.objects.get(user=request.user)
        except GameSave.DoesNotExist:
            return Response(
                {'detail': 'No save found for this account.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response({
            'save_data': game_save.save_data,
            'updated_at': game_save.updated_at.isoformat(),
            'story_progress_percent': game_save.story_progress_percent,
            'challenges_completed': game_save.challenges_completed,
            'learning_modules_completed': game_save.learning_modules_completed,
        }, status=status.HTTP_200_OK)

    def delete(self, request):
        deleted, _ = GameSave.objects.filter(user=request.user).delete()
        if deleted:
            return Response({'detail': 'Save deleted.'}, status=status.HTTP_200_OK)
        return Response({'detail': 'No save to delete.'}, status=status.HTTP_404_NOT_FOUND)


# ═════════════════════════════════════════════════════════════════════════════
# GameCheckCodeView — The brain of the Fake IDE
# ═════════════════════════════════════════════════════════════════════════════

class GameCheckCodeView(APIView):
    """
    POST /api/game/check-code/
    
    Godot sends:
    {
        "code": "python -m venv venv",
        "language": "python",
        "challenge_id": "ch1_venv",
        "expected_answers": ["python -m venv venv"],
        "expected_output": "Virtual environment created!"
    }
    
    Response:
    {
        "success": true/false,
        "output": "✅ Correct! ...",
        "ai_hint": "It looks like you misspelled..."
    }
    """
    permission_classes = [permissions.AllowAny]  # Allow offline/anonymous play

    def post(self, request):
        print(f"\n[check-code] ========== REQUEST RECEIVED ==========")
        code = request.data.get('code', '').strip()
        language = request.data.get('language', 'python').lower()
        challenge_id = request.data.get('challenge_id', '')
        expected_answers = request.data.get('expected_answers', [])
        expected_output = request.data.get('expected_output', '')
        print(f"[check-code] code='{code[:50]}...', language={language}, challenge_id={challenge_id}")

        if not code:
            return Response({
                'success': False,
                'output': '❌ No code submitted.',
            }, status=status.HTTP_400_BAD_REQUEST)

        # ── Tier 1: Quick local validation (free, instant) ──
        is_correct, local_message = self._local_validate(
            code, language, expected_answers
        )

        if is_correct:
            return Response({
                'success': True,
                'output': expected_output or '✅ Correct! Great job!',
            })

        # ── Tier 2: Judge0 execution for Python (if Docker is running) ──
        judge0_output = None
        if language == 'python' and JUDGE0_LANGUAGES.get(language):
            print(f"[check-code] Starting Judge0 execution...")
            judge0_output = self._execute_judge0(code, language)
            print(f"[check-code] Judge0 done: {str(judge0_output)[:80]}")

        # ── Tier 3: Gemini AI hint (if API key is set) ──
        ai_hint = None
        if GEMINI_API_KEY:
            print(f"[check-code] Starting Gemini hint generation...")
            ai_hint = self._generate_gemini_hint(
                code, language, expected_answers, 
                local_message, judge0_output
            )
            print(f"[check-code] Gemini done: {str(ai_hint)[:80]}")

        # Build the response
        output = local_message
        if judge0_output and 'error' in judge0_output.lower():
            output = judge0_output  # Show the real Python error

        print(f"[check-code] ========== SENDING RESPONSE ==========")

        return Response({
            'success': False,
            'output': output,
            'ai_hint': ai_hint or '',
            'judge0_output': judge0_output or '',
        })

    def _local_validate(self, code, language, expected_answers):
        """
        Tier 1: Fast local validation without any API calls.
        Checks expected answer matching FIRST, then syntax.
        """
        import ast as python_ast

        # Check against expected answers first (multi-pass, same logic as Godot)
        if expected_answers:
            code_stripped = code.strip()
            for answer in expected_answers:
                ans = answer.strip()
                # Exact match
                if code_stripped == ans:
                    return True, "Correct!"
                # Answer contained in code
                if ans in code:
                    return True, "Correct!"
                # Normalized whitespace
                norm_code = re.sub(r'\s+', ' ', code_stripped)
                norm_ans = re.sub(r'\s+', ' ', ans)
                if norm_code == norm_ans or norm_ans in norm_code:
                    return True, "Correct!"

        # Only check Python syntax if the answer didn't match
        # (avoids false positives on terminal commands like 'python -m venv venv')
        if language == 'python':
            try:
                python_ast.parse(code)
            except SyntaxError as e:
                return False, f"SyntaxError on line {e.lineno}: {e.msg}"

        return False, "❌ Not quite right. Check your code and try again."

    def _execute_judge0(self, code, language):
        """
        Tier 2: Send code to Judge0 Docker container for safe execution.
        Returns the stdout/stderr output.
        """
        import base64

        lang_id = JUDGE0_LANGUAGES.get(language)
        if not lang_id:
            return None

        try:
            headers = {'Content-Type': 'application/json'}
            if JUDGE0_AUTH_TOKEN:
                headers['X-Auth-Token'] = JUDGE0_AUTH_TOKEN

            # Submit the code
            payload = {
                'source_code': base64.b64encode(code.encode()).decode(),
                'language_id': lang_id,
                'stdin': '',
                'cpu_time_limit': 5,
                'memory_limit': 128000,
            }
            submit_resp = http_requests.post(
                f'{JUDGE0_API_URL}/submissions/?base64_encoded=true&wait=false',
                json=payload, headers=headers, timeout=10
            )
            token = submit_resp.json().get('token')
            if not token:
                return None

            # Poll for result (max 10 seconds)
            for _ in range(20):
                time.sleep(0.5)
                result_resp = http_requests.get(
                    f'{JUDGE0_API_URL}/submissions/{token}?base64_encoded=true',
                    headers=headers, timeout=10
                )
                result = result_resp.json()
                status_id = result.get('status', {}).get('id', 0)

                # Status 1-2 = In Queue/Processing, 3+ = Done
                if status_id >= 3:
                    stdout = result.get('stdout', '') or ''
                    stderr = result.get('stderr', '') or ''
                    compile_output = result.get('compile_output', '') or ''

                    # Decode base64
                    if stdout:
                        stdout = base64.b64decode(stdout).decode('utf-8', errors='replace')
                    if stderr:
                        stderr = base64.b64decode(stderr).decode('utf-8', errors='replace')
                    if compile_output:
                        compile_output = base64.b64decode(compile_output).decode('utf-8', errors='replace')

                    if stderr:
                        return f"Error:\n{stderr}"
                    if compile_output:
                        return f"Compile Error:\n{compile_output}"
                    return stdout.strip() if stdout else "Code executed with no output."

            return "⏳ Execution timed out."

        except http_requests.RequestException as e:
            return f"Judge0 unavailable: {str(e)}"

    def _generate_gemini_hint(self, code, language, expected_answers, 
                               local_error, judge0_output):
        """
        Tier 3: Ask Gemini AI to generate a helpful, friendly hint.
        Only called when Tier 1 fails, keeping API usage minimal.
        """
        if not GEMINI_API_KEY:
            return None

        try:
            # Build a diff-style comparison for the AI
            closest_answer = expected_answers[0] if expected_answers else ""
            
            prompt = f"""You are a sharp-eyed coding tutor in a game called DjangoQuest.
Your job is to compare the student's code to the correct answer and find the EXACT mistake.

STUDENT WROTE:
"{code}"

CORRECT ANSWER (one of these):
{json.dumps(expected_answers[:3])}

RULES:
1. Compare the student's text against each correct answer CHARACTER BY CHARACTER.
2. Identify the EXACT difference: misspelled word, missing letter, extra letter, wrong letter, missing tag, wrong capitalization, missing space, wrong indentation, etc.
3. Tell them SPECIFICALLY what is wrong. Examples of good hints:
   - "You wrote 'HTP' but it should be 'HTTP' — you're missing the second 'T'!"
   - "You wrote 'prnt' instead of 'print' — looks like the 'i' is missing!"
   - "You forgot the closing </p> tag at the end."
   - "The indentation needs 4 spaces before 'name'."
4. Keep it to 1-2 sentences MAX, friendly and encouraging.
5. Do NOT just say the full answer. Point out the specific mistake so they can fix it themselves.

{f'Error message: {local_error}' if local_error else ''}
{f'Runtime output: {judge0_output}' if judge0_output else ''}

Your hint:"""

            resp = http_requests.post(
                'https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-latest:generateContent',
                headers={
                    'Content-Type': 'application/json',
                    'X-goog-api-key': GEMINI_API_KEY,
                },
                json={
                    'contents': [{'parts': [{'text': prompt}]}],
                    'generationConfig': {
                        'temperature': 0.7,
                        'maxOutputTokens': 500,
                    }
                },
                timeout=8
            )

            if resp.status_code == 200:
                data = resp.json()
                candidates = data.get('candidates', [])
                if candidates:
                    parts = candidates[0].get('content', {}).get('parts', [])
                    if parts:
                        hint = parts[0].get('text', '').strip()
                        print(f"[Gemini] ✅ Generated hint: {hint[:80]}...")
                        return hint
            else:
                print(f"[Gemini] ❌ API returned {resp.status_code}: {resp.text[:200]}")

            return None

        except Exception as e:
            print(f"[Gemini] ❌ Exception: {e}")
            return None
