# announcements/views.py
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db.models import Q
from .models import Announcement
from .serializers import AnnouncementReadSerializer, AnnouncementWriteSerializer


class AnnouncementListCreateView(generics.ListCreateAPIView):
    """
    GET  /api/announcements/ — role-filtered list
    POST /api/announcements/ — create (admin: platform, teacher: classroom, student: 403)
    """
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return AnnouncementWriteSerializer
        return AnnouncementReadSerializer

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return Announcement.objects.prefetch_related('target_classrooms').select_related('author').all()

        q = Q(announcement_type='platform')

        if user.is_teacher:
            q |= Q(announcement_type='classroom', author=user)
        elif user.is_student:
            # Students see classroom announcements for their enrolled classroom
            profile = getattr(user, 'profile', None)
            if profile and profile.classroom:
                q |= Q(announcement_type='classroom', target_classrooms=profile.classroom)

        return Announcement.objects.filter(q).prefetch_related('target_classrooms').select_related('author').distinct()

    def create(self, request, *args, **kwargs):
        if not request.user.is_staff and not request.user.is_teacher:
            return Response(
                {'detail': 'Students cannot create announcements.'},
                status=status.HTTP_403_FORBIDDEN,
            )
        return super().create(request, *args, **kwargs)


class AnnouncementDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET/PUT/PATCH/DELETE /api/announcements/<id>/
    Only the author (or admin) can modify/delete.
    """
    permission_classes = [IsAuthenticated]
    queryset = Announcement.objects.prefetch_related('target_classrooms').select_related('author').all()

    def get_serializer_class(self):
        if self.request.method in ('PUT', 'PATCH'):
            return AnnouncementWriteSerializer
        return AnnouncementReadSerializer

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.author != request.user and not request.user.is_staff:
            return Response({'detail': 'You can only edit your own announcements.'}, status=status.HTTP_403_FORBIDDEN)
        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.author != request.user and not request.user.is_staff:
            return Response({'detail': 'You can only delete your own announcements.'}, status=status.HTTP_403_FORBIDDEN)
        return super().destroy(request, *args, **kwargs)
