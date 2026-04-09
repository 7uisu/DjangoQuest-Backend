# dashboard/urls.py
from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    # Registration
    path('register/student/', views.student_register, name='student_register'),
    path('register/teacher/', views.teacher_register, name='teacher_register'),

    # Auth
    path('login/', views.universal_login, name='login'),
    path('logout/', views.user_logout, name='logout'),

    # Student
    path('student/profile/', views.student_profile, name='student_profile'),

    # Teacher Dashboard
    path('dashboard/', views.teacher_dashboard, name='teacher_dashboard'),
    path('classroom/<int:classroom_id>/', views.classroom_detail, name='classroom_detail'),
    path(
        'classroom/<int:classroom_id>/reset-password/<int:student_id>/',
        views.reset_student_password,
        name='reset_student_password',
    ),
]
