# feedback/urls.py
from django.urls import path
from .views import FeedbackCreateView, FeedbackMineView

urlpatterns = [
    path('', FeedbackCreateView.as_view(), name='feedback-create'),
    path('mine/', FeedbackMineView.as_view(), name='feedback-mine'),
]
