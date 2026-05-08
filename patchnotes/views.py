# patchnotes/views.py
from rest_framework import generics
from rest_framework.permissions import AllowAny
from .models import PatchNote, DownloadLink
from .serializers import PatchNoteSerializer, DownloadLinkSerializer


class PatchNoteListView(generics.ListAPIView):
    """Public: list all patch notes (newest first, no pagination)."""
    queryset = PatchNote.objects.all().order_by('-created_at')
    serializer_class = PatchNoteSerializer
    permission_classes = [AllowAny]
    pagination_class = None  # Return plain array, not {count, results}


class DownloadLinkListView(generics.ListAPIView):
    """Public: returns the current download link for each platform."""
    queryset = DownloadLink.objects.all()
    serializer_class = DownloadLinkSerializer
    permission_classes = [AllowAny]
    pagination_class = None  # Always return all (max 2 rows)
