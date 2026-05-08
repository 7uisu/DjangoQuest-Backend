# patchnotes/serializers.py
from rest_framework import serializers
from .models import PatchNote, DownloadLink


class PatchNoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = PatchNote
        fields = ['id', 'version', 'title', 'body', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class DownloadLinkSerializer(serializers.ModelSerializer):
    class Meta:
        model = DownloadLink
        fields = ['id', 'platform', 'url', 'updated_at']
        read_only_fields = ['id', 'updated_at']
