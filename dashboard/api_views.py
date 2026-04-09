# dashboard/api_views.py
from rest_framework import generics, status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from users.models import Classroom
from .api_serializers import ClassroomSerializer, ClassroomDetailSerializer

User = get_user_model()


class IsTeacher(permissions.BasePermission):
    """Only allow authenticated teachers."""
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_teacher


class ClassroomListCreateView(generics.ListCreateAPIView):
    """
    GET  /api/dashboard/classrooms/     — list this teacher's classrooms
    POST /api/dashboard/classrooms/     — create a new classroom
    """
    serializer_class = ClassroomSerializer
    permission_classes = [IsTeacher]

    def get_queryset(self):
        return Classroom.objects.filter(teacher=self.request.user).order_by('-created_at')

    def perform_create(self, serializer):
        serializer.save(teacher=self.request.user)


class ClassroomDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET    /api/dashboard/classrooms/<pk>/ — classroom detail with students
    PATCH  /api/dashboard/classrooms/<pk>/ — rename classroom
    DELETE /api/dashboard/classrooms/<pk>/ — delete classroom
    """
    serializer_class = ClassroomDetailSerializer
    permission_classes = [IsTeacher]

    def get_queryset(self):
        return Classroom.objects.filter(teacher=self.request.user)


class StudentPasswordResetView(APIView):
    """
    POST /api/dashboard/students/<pk>/reset-password/
    Teacher resets a student's password to a default value.
    """
    permission_classes = [IsTeacher]

    def post(self, request, pk):
        student = get_object_or_404(User, pk=pk, is_student=True)

        # Verify student is in one of this teacher's classrooms
        teacher_classrooms = Classroom.objects.filter(teacher=request.user)
        is_enrolled = student.profile.classroom in teacher_classrooms if hasattr(student, 'profile') else False

        if not is_enrolled:
            return Response(
                {"detail": "This student is not in any of your classrooms."},
                status=status.HTTP_403_FORBIDDEN,
            )

        new_password = "DjangoQuest2026!"
        student.set_password(new_password)
        student.save()

        return Response({
            "detail": f"Password for {student.username} has been reset.",
            "new_password": new_password,
        })

class RemoveStudentFromClassroomView(APIView):
    """
    POST /api/dashboard/classrooms/<pk>/remove-student/<student_id>/
    Teacher removes a student from a specific classroom.
    """
    permission_classes = [IsTeacher]

    def post(self, request, pk, student_id):
        classroom = get_object_or_404(Classroom, pk=pk, teacher=request.user)
        student = get_object_or_404(User, pk=student_id, is_student=True)
        
        # Verify student is actually in THIS classroom
        if hasattr(student, 'profile') and student.profile.classroom == classroom:
            student.profile.classroom = None
            student.profile.save()
            return Response({"detail": f"Removed {student.username} from {classroom.name}."})
            
        return Response(
            {"detail": "This student is not in this classroom."},
            status=status.HTTP_400_BAD_REQUEST
        )
