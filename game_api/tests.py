# game_api/tests.py
import json
from django.test import TestCase
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from users.models import Profile, Classroom

User = get_user_model()


class GameLoginTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.url = '/api/game/login/'
        self.student = User.objects.create_user(
            email='student@test.com', username='gamer1', password='TestPass123!'
        )
        self.student.is_student = True
        self.student.is_teacher = False
        self.student.save()
        Profile.objects.create(user=self.student)

        self.teacher = User.objects.create_user(
            email='teacher@test.com', username='teach1', password='TestPass123!'
        )
        self.teacher.is_teacher = True
        self.teacher.is_student = False
        self.teacher.save()
        Profile.objects.create(user=self.teacher)

    def test_student_login_success(self):
        resp = self.client.post(self.url, {
            'email': 'student@test.com',
            'password': 'TestPass123!',
        })
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn('access', data)
        self.assertIn('refresh', data)
        self.assertEqual(data['username'], 'gamer1')

    def test_teacher_login_rejected(self):
        resp = self.client.post(self.url, {
            'email': 'teacher@test.com',
            'password': 'TestPass123!',
        })
        self.assertEqual(resp.status_code, 403)
        self.assertIn('Only student', resp.json()['detail'])

    def test_invalid_credentials(self):
        resp = self.client.post(self.url, {
            'email': 'student@test.com',
            'password': 'wrongpass',
        })
        self.assertEqual(resp.status_code, 401)

    def test_missing_fields(self):
        resp = self.client.post(self.url, {})
        self.assertEqual(resp.status_code, 400)


class GameEnrollTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.url = '/api/game/enroll/'

        self.teacher = User.objects.create_user(
            email='teacher@test.com', username='teach1', password='TestPass123!'
        )
        self.teacher.is_teacher = True
        self.teacher.is_student = False
        self.teacher.save()
        Profile.objects.create(user=self.teacher)

        self.student = User.objects.create_user(
            email='student@test.com', username='gamer1', password='TestPass123!'
        )
        self.student.is_student = True
        self.student.is_teacher = False
        self.student.save()
        Profile.objects.create(user=self.student)

        self.classroom = Classroom.objects.create(
            teacher=self.teacher, name='CS101'
        )

    def _login(self):
        resp = self.client.post('/api/game/login/', {
            'email': 'student@test.com',
            'password': 'TestPass123!',
        })
        token = resp.json()['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')

    def test_enroll_success(self):
        self._login()
        resp = self.client.post(self.url, {
            'enrollment_code': self.classroom.enrollment_code,
        })
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data['classroom_name'], 'CS101')
        self.assertEqual(data['teacher'], 'teach1')
        # Verify profile was updated
        self.student.profile.refresh_from_db()
        self.assertEqual(self.student.profile.classroom, self.classroom)

    def test_enroll_invalid_code(self):
        self._login()
        resp = self.client.post(self.url, {
            'enrollment_code': 'BADCODE1',
        })
        self.assertEqual(resp.status_code, 404)

    def test_enroll_without_auth(self):
        resp = self.client.post(self.url, {
            'enrollment_code': self.classroom.enrollment_code,
        })
        self.assertEqual(resp.status_code, 401)

    def test_enroll_case_insensitive(self):
        """Enrollment codes are uppercased automatically."""
        self._login()
        resp = self.client.post(self.url, {
            'enrollment_code': self.classroom.enrollment_code.lower(),
        })
        self.assertEqual(resp.status_code, 200)
