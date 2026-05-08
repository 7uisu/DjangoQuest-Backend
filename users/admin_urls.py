# users/admin_urls.py
from django.urls import path
from .admin_views import (
    AdminStatsView,
    AdminUserListView,
    AdminUserDetailView,
    AdminResetPasswordView,
    AdminUserExportView,
    AdminClassroomListView,
    AdminClassroomDetailView,
    AdminClassroomEnrollView,
    AdminClassroomUnenrollView,
    AdminClassroomExportView,
    AdminFeedbackListView,
    AdminFeedbackDeleteView,
    AdminFeedbackExportView,
    AdminAnnouncementListView,
    AdminAnnouncementDetailView,
    AdminAuditLogView,
    AdminInviteCodeView,
    AdminPatchNoteListView,
    AdminPatchNoteDetailView,
    AdminDownloadLinkView,
)

from app.admin_views import (
    AdminVideoTutorialListView,
    AdminVideoTutorialDetailView,
    AdminVideoStepListView,
    AdminVideoStepDetailView
)

urlpatterns = [
    path('stats/', AdminStatsView.as_view(), name='admin_stats'),

    # Users
    path('users/', AdminUserListView.as_view(), name='admin_users'),
    path('users/export/', AdminUserExportView.as_view(), name='admin_users_export'),
    path('users/<int:user_id>/', AdminUserDetailView.as_view(), name='admin_user_detail'),
    path('users/<int:user_id>/reset-password/', AdminResetPasswordView.as_view(), name='admin_reset_password'),

    # Classrooms
    path('classrooms/', AdminClassroomListView.as_view(), name='admin_classrooms'),
    path('classrooms/export/', AdminClassroomExportView.as_view(), name='admin_classrooms_export'),
    path('classrooms/<int:classroom_id>/', AdminClassroomDetailView.as_view(), name='admin_classroom_detail'),
    path('classrooms/<int:classroom_id>/enroll/', AdminClassroomEnrollView.as_view(), name='admin_classroom_enroll'),
    path('classrooms/<int:classroom_id>/unenroll/', AdminClassroomUnenrollView.as_view(), name='admin_classroom_unenroll'),

    # Feedback
    path('feedback/', AdminFeedbackListView.as_view(), name='admin_feedback'),
    path('feedback/export/', AdminFeedbackExportView.as_view(), name='admin_feedback_export'),
    path('feedback/<int:feedback_id>/', AdminFeedbackDeleteView.as_view(), name='admin_feedback_delete'),

    # Announcements
    path('announcements/', AdminAnnouncementListView.as_view(), name='admin_announcements'),
    path('announcements/<int:pk>/', AdminAnnouncementDetailView.as_view(), name='admin_announcement_detail'),

    # Audit Log
    path('audit-log/', AdminAuditLogView.as_view(), name='admin_audit_log'),

    # Settings
    path('invite-codes/', AdminInviteCodeView.as_view(), name='admin_invite_codes'),

    # Patch Notes
    path('patchnotes/', AdminPatchNoteListView.as_view(), name='admin_patchnotes'),
    path('patchnotes/<int:pk>/', AdminPatchNoteDetailView.as_view(), name='admin_patchnote_detail'),

    # Download Links
    path('download-links/', AdminDownloadLinkView.as_view(), name='admin_download_links'),

    # Video Tutorials
    path('video-tutorials/', AdminVideoTutorialListView.as_view()),
    path('video-tutorials/<int:pk>/', AdminVideoTutorialDetailView.as_view()),
    path('video-tutorials/<int:tutorial_id>/steps/', AdminVideoStepListView.as_view()),
    path('video-tutorials/steps/<int:pk>/', AdminVideoStepDetailView.as_view()),
]
