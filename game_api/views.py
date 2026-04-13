# game_api/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate, get_user_model
from users.models import Classroom, Profile
from .models import GameSave

User = get_user_model()


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
        # (Teachers can play the game too and track their own progress)

        # Generate JWT tokens
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

        # Get or create the student's profile
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
