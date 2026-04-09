# dashboard/views.py
import string
import random

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponseForbidden

from users.models import Profile, Classroom
from .forms import (
    StudentRegistrationForm,
    TeacherRegistrationForm,
    UniversalLoginForm,
    ClassroomForm,
)

User = get_user_model()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def teacher_required(view_func):
    """Decorator that ensures the logged-in user is a teacher."""
    def _wrapped(request, *args, **kwargs):
        if not request.user.is_authenticated:
            from django.conf import settings
            login_url = getattr(settings, 'LOGIN_URL', '/login/')
            return redirect(f'{login_url}?next={request.path}')
        if not request.user.is_teacher:
            return HttpResponseForbidden("You do not have permission to access this page.")
        return view_func(request, *args, **kwargs)
    return _wrapped


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------

def student_register(request):
    if request.user.is_authenticated:
        return redirect('dashboard:login')

    if request.method == 'POST':
        form = StudentRegistrationForm(request.POST)
        if form.is_valid():
            user = User.objects.create_user(
                email=form.cleaned_data['email'],
                username=form.cleaned_data['username'],
                password=form.cleaned_data['password'],
            )
            user.is_student = True
            user.is_teacher = False
            user.save()
            Profile.objects.create(user=user)
            messages.success(request, 'Account created! You can now log in.')
            return redirect('dashboard:login')
    else:
        form = StudentRegistrationForm()

    return render(request, 'dashboard/register_student.html', {'form': form})


def teacher_register(request):
    if request.user.is_authenticated:
        return redirect('dashboard:login')

    if request.method == 'POST':
        form = TeacherRegistrationForm(request.POST)
        if form.is_valid():
            user = User.objects.create_user(
                email=form.cleaned_data['email'],
                username=form.cleaned_data['username'],
                password=form.cleaned_data['password'],
            )
            user.is_teacher = True
            user.is_student = False
            user.save()
            Profile.objects.create(user=user)
            messages.success(request, 'Teacher account created! You can now log in.')
            return redirect('dashboard:login')
    else:
        form = TeacherRegistrationForm()

    return render(request, 'dashboard/register_teacher.html', {'form': form})


# ---------------------------------------------------------------------------
# Login / Logout
# ---------------------------------------------------------------------------

def universal_login(request):
    if request.user.is_authenticated:
        if request.user.is_teacher:
            return redirect('dashboard:teacher_dashboard')
        return redirect('dashboard:student_profile')

    if request.method == 'POST':
        form = UniversalLoginForm(request.POST)
        if form.is_valid():
            user = authenticate(
                request,
                email=form.cleaned_data['email'],
                password=form.cleaned_data['password'],
            )
            if user is not None:
                login(request, user)
                if user.is_teacher:
                    return redirect('dashboard:teacher_dashboard')
                return redirect('dashboard:student_profile')
            else:
                messages.error(request, 'Invalid email or password.')
    else:
        form = UniversalLoginForm()

    return render(request, 'dashboard/login.html', {'form': form})


def user_logout(request):
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('dashboard:login')


# ---------------------------------------------------------------------------
# Student Profile
# ---------------------------------------------------------------------------

@login_required(login_url='/login/')
def student_profile(request):
    profile, _ = Profile.objects.get_or_create(user=request.user)
    return render(request, 'dashboard/student_profile.html', {'profile': profile})


# ---------------------------------------------------------------------------
# Teacher Dashboard
# ---------------------------------------------------------------------------

@teacher_required
def teacher_dashboard(request):
    if request.method == 'POST':
        form = ClassroomForm(request.POST)
        if form.is_valid():
            Classroom.objects.create(
                teacher=request.user,
                name=form.cleaned_data['name'],
            )
            messages.success(request, 'Classroom created successfully!')
            return redirect('dashboard:teacher_dashboard')
    else:
        form = ClassroomForm()

    classrooms = Classroom.objects.filter(teacher=request.user).order_by('-created_at')
    return render(request, 'dashboard/teacher_dashboard.html', {
        'form': form,
        'classrooms': classrooms,
    })


@teacher_required
def classroom_detail(request, classroom_id):
    classroom = get_object_or_404(Classroom, id=classroom_id, teacher=request.user)
    students = Profile.objects.filter(classroom=classroom).select_related('user')
    return render(request, 'dashboard/classroom_detail.html', {
        'classroom': classroom,
        'students': students,
    })


@teacher_required
def reset_student_password(request, classroom_id, student_id):
    classroom = get_object_or_404(Classroom, id=classroom_id, teacher=request.user)
    student = get_object_or_404(User, id=student_id, profile__classroom=classroom)

    # Generate a random temporary password
    chars = string.ascii_letters + string.digits
    temp_password = ''.join(random.choices(chars, k=10))
    student.set_password(temp_password)
    student.save()

    return render(request, 'dashboard/password_reset_done.html', {
        'student': student,
        'temp_password': temp_password,
        'classroom': classroom,
    })
