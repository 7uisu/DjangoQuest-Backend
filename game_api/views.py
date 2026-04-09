# game_api/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate, get_user_model
from users.models import Classroom, Profile

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

        if not user.is_student:
            return Response(
                {'detail': 'Only student accounts can log into the game.'},
                status=status.HTTP_403_FORBIDDEN,
            )

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
