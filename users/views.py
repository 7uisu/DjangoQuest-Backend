# users/views.py
from rest_framework import generics, status, permissions, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.contrib.auth.tokens import default_token_generator
from django.conf import settings

from .models import Profile, Achievement, UserAchievement
from .serializers import (
    UserSerializer, RegisterSerializer, UserProfileUpdateSerializer,
    AchievementSerializer, UserAchievementSerializer,
    PasswordResetSerializer, PasswordResetConfirmSerializer
)

User = get_user_model()

# ── Professor certificate mapping (same as serializer) ──
PROFESSOR_CERTS = [
    ("y1s1", "Professor Markup", "HTML Basics"),
    ("y1s2", "Professor Syntax", "Python Data Types"),
    ("y2s1", "Professor View", "Django Views & URL Routing"),
    ("y2s2", "Professor Query", "Django ORM & Relationships"),
    ("y3s1", "Professor Auth", "Authentication & Security"),
    ("y3s2", "Professor Token", "Token-Based Auth"),
    ("y3mid", "Professor REST", "RESTful API Design"),
]
PROFESSOR_MAP = {key: (name, topic) for key, name, topic in PROFESSOR_CERTS}


class CertificateVerifyView(APIView):
    """
    GET /api/certificates/verify/<cert_id>/
    Public endpoint — no auth required.
    Verifies a certificate ID like CERT-42-y1s1 or CERT-42-grand.
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request, cert_id):
        # Parse cert_id: CERT-{user_id}-{professor_key}
        parts = cert_id.split('-', 2)
        if len(parts) != 3 or parts[0] != 'CERT':
            return Response({'valid': False, 'detail': 'Invalid certificate ID format.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user_id = int(parts[1])
        except ValueError:
            return Response({'valid': False, 'detail': 'Invalid certificate ID format.'}, status=status.HTTP_400_BAD_REQUEST)

        prof_key = parts[2]

        try:
            user = User.objects.select_related('game_save').get(pk=user_id)
        except User.DoesNotExist:
            return Response({'valid': False, 'detail': 'Certificate not found.'}, status=status.HTTP_404_NOT_FOUND)

        game_save = getattr(user, 'game_save', None)
        sd = game_save.save_data if game_save and isinstance(game_save.save_data, dict) else {}

        if prof_key == 'grand':
            # Grand certificate: all 7 must be done
            all_done = all(bool(sd.get(f"ch2_{k}_teaching_done", False)) for k, _, _ in PROFESSOR_CERTS)
            if not all_done:
                return Response({'valid': False, 'detail': 'This certificate has not been earned yet.'}, status=status.HTTP_404_NOT_FOUND)
            # Find latest timestamp
            timestamps = [sd.get(f"ch2_{k}_teaching_done_at") for k, _, _ in PROFESSOR_CERTS]
            latest = max((t for t in timestamps if t), default=None)
            return Response({
                'valid': True,
                'certificate_id': cert_id,
                'student_name': f"{user.first_name} {user.last_name}".strip() or user.username,
                'professor': 'DjangoQuest',
                'topic': 'Full-Stack Django Development',
                'completed_at': latest,
            })

        if prof_key not in PROFESSOR_MAP:
            return Response({'valid': False, 'detail': 'Invalid professor key.'}, status=status.HTTP_400_BAD_REQUEST)

        done = bool(sd.get(f"ch2_{prof_key}_teaching_done", False))
        if not done:
            return Response({'valid': False, 'detail': 'This certificate has not been earned yet.'}, status=status.HTTP_404_NOT_FOUND)

        name, topic = PROFESSOR_MAP[prof_key]
        ts = sd.get(f"ch2_{prof_key}_teaching_done_at", None)

        return Response({
            'valid': True,
            'certificate_id': cert_id,
            'student_name': f"{user.first_name} {user.last_name}".strip() or user.username,
            'professor': name,
            'topic': topic,
            'completed_at': ts,
        })


class CertificateImageView(APIView):
    """
    GET /api/certificates/<professor_key>/image/
    Authenticated. Renders the user's certificate as a PNG via WeasyPrint.
    professor_key: y1s1, y1s2, y2s1, y2s2, y3s1, y3s2, y3mid, or grand
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, professor_key):
        from django.template.loader import render_to_string
        from django.http import HttpResponse
        import weasyprint
        import base64
        import os

        user = User.objects.select_related('game_save').get(pk=request.user.pk)
        game_save = getattr(user, 'game_save', None)
        sd = game_save.save_data if game_save and isinstance(game_save.save_data, dict) else {}

        student_name = f"{user.first_name} {user.last_name}".strip() or user.username

        # Format date as MM/DD/YYYY
        def format_date(raw):
            if not raw or not isinstance(raw, str) or len(raw) < 10:
                return raw or 'N/A'
            try:
                parts = raw[:10].split('-')
                return f"{parts[1]}/{parts[2]}/{parts[0]}"
            except (IndexError, ValueError):
                return raw[:10]

        # Encode logo as base64 data URI for WeasyPrint
        logo_data_uri = ''
        logo_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'templates', 'DQUESTLOGO.svg')
        if os.path.exists(logo_path):
            with open(logo_path, 'rb') as f:
                logo_b64 = base64.b64encode(f.read()).decode('utf-8')
                logo_data_uri = f'data:image/svg+xml;base64,{logo_b64}'

        if professor_key == 'grand':
            all_done = all(bool(sd.get(f"ch2_{k}_teaching_done", False)) for k, _, _ in PROFESSOR_CERTS)
            if not all_done:
                return Response({'detail': 'Grand certificate not earned yet.'}, status=status.HTTP_403_FORBIDDEN)
            timestamps = [sd.get(f"ch2_{k}_teaching_done_at") for k, _, _ in PROFESSOR_CERTS]
            latest = max((t for t in timestamps if t), default='N/A')
            context = {
                'title': 'Grand Certificate of Mastery',
                'subtitle': 'Full-Stack Django Development',
                'student_name': student_name,
                'topic': 'Full-Stack Django Development',
                'completed_at': format_date(latest),
                'cert_id': f'DQ-{user.id}-Grand-Mastery',
                'border_color': '#b8860b',
                'accent_color': '#8b6914',
                'title_color': '#6b4f12',
                'logo_data_uri': logo_data_uri,
            }
        elif professor_key in PROFESSOR_MAP:
            done = bool(sd.get(f"ch2_{professor_key}_teaching_done", False))
            if not done:
                return Response({'detail': 'Certificate not earned yet.'}, status=status.HTTP_403_FORBIDDEN)
            name, topic = PROFESSOR_MAP[professor_key]
            ts = sd.get(f"ch2_{professor_key}_teaching_done_at", 'N/A')
            # Create a human-readable cert ID from the topic
            readable_id = topic.replace(' ', '-').replace('&', 'and')
            context = {
                'title': 'Certificate of Completion',
                'subtitle': 'DjangoQuest Educational Platform',
                'student_name': student_name,
                'topic': topic,
                'completed_at': format_date(ts),
                'cert_id': f'DQ-{user.id}-{readable_id}',
                'border_color': '#1a5276',
                'accent_color': '#1a73e8',
                'title_color': '#154360',
                'logo_data_uri': logo_data_uri,
            }
        else:
            return Response({'detail': 'Invalid professor key.'}, status=status.HTTP_400_BAD_REQUEST)

        html_string = render_to_string('certificate.html', context)
        pdf_bytes = weasyprint.HTML(string=html_string).write_pdf()

        # Convert first page of PDF to PNG using Pillow + pdf2image-like approach
        # WeasyPrint v68 doesn't have write_png, so we serve the PDF directly
        # and let the frontend handle display. For PNG, we'd need poppler.
        # Serving as PDF is actually better — higher quality and smaller.
        response = HttpResponse(pdf_bytes, content_type='application/pdf')
        response['Content-Disposition'] = f'inline; filename="certificate-{professor_key}.pdf"'
        return response


class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = [permissions.AllowAny]
    serializer_class = RegisterSerializer

class UserProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        return User.objects.select_related(
            'profile', 'game_save'
        ).prefetch_related(
            'achievements__achievement'
        ).get(pk=self.request.user.pk)
    
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = UserProfileUpdateSerializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        
        # Return the full user data using UserSerializer
        return Response(UserSerializer(instance).data)

# users/views.py
class LogoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        refresh_token = request.data.get("refresh")
        if not refresh_token:
            return Response({"detail": "Refresh token is required."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({"detail": "Successfully logged out."}, status=status.HTTP_205_RESET_CONTENT)
        except Exception as e:
            return Response({"detail": f"Invalid refresh token: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)

class AchievementViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing achievements
    """
    queryset = Achievement.objects.all()
    serializer_class = AchievementSerializer
    permission_classes = [permissions.IsAuthenticated]

class UserAchievementView(APIView):
    """
    API view for user achievements
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        user_achievements = UserAchievement.objects.filter(user=request.user)
        serializer = UserAchievementSerializer(user_achievements, many=True)
        return Response(serializer.data)
    
class PasswordResetView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        try:
            email = request.data.get('email')
            if not email:
                return Response({'email': 'This field is required.'}, status=status.HTTP_400_BAD_REQUEST)
            
            user = User.objects.filter(email=email).first()
            if user:
                token = default_token_generator.make_token(user)
                uid = urlsafe_base64_encode(force_bytes(user.pk))
                reset_link = f"{settings.FRONTEND_URL}/password-reset-confirm/{uid}/{token}/"
                send_mail(
                    'Password Reset Request',
                    f'Click the link to reset your password: {reset_link}',
                    settings.DEFAULT_FROM_EMAIL,
                    [email],
                    fail_silently=False,
                    html_message=f'<p>Click the link to reset your password: <a href="{reset_link}">{reset_link}</a></p>',
                )
            # Always return success to avoid leaking email existence
            return Response({'detail': 'Password reset email sent if the email exists.'}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'detail': f'Failed to send password reset email: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class PasswordResetConfirmView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        uidb64 = request.data.get('uid')
        token = request.data.get('token')
        new_password = request.data.get('new_password')
        
        if not all([uidb64, token, new_password]):
            return Response({'detail': 'Missing required fields.'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            user = None
        
        if user and default_token_generator.check_token(user, token):
            user.set_password(new_password)
            user.save()
            return Response({'detail': 'Password has been reset.'}, status=status.HTTP_200_OK)
        return Response({'detail': 'Invalid token or user.'}, status=status.HTTP_400_BAD_REQUEST)