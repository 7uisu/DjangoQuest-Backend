# patchnotes/admin.py
from django.contrib import admin
from .models import PatchNote, DownloadLink

admin.site.register(PatchNote)
admin.site.register(DownloadLink)
