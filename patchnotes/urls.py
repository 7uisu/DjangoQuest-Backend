# patchnotes/urls.py
from django.urls import path
from .views import PatchNoteListView, DownloadLinkListView

urlpatterns = [
    path('', PatchNoteListView.as_view(), name='patchnotes-list'),
    path('downloads/', DownloadLinkListView.as_view(), name='download-links'),
]
