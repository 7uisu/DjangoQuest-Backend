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

    def test_teacher_login_allowed(self):
        """Teachers can now log into the game to play it."""
        resp = self.client.post(self.url, {
            'email': 'teacher@test.com',
            'password': 'TestPass123!',
        })
        self.assertEqual(resp.status_code, 200)
        self.assertIn('access', resp.json())

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


class GameSaveTest(TestCase):
    """Tests for PUT / GET / DELETE  /api/game/save/"""

    def setUp(self):
        self.client = APIClient()
        self.url = '/api/game/save/'

        self.student = User.objects.create_user(
            email='saver@test.com', username='saver', password='TestPass123!'
        )
        self.student.is_student = True
        self.student.is_teacher = False
        self.student.save()
        Profile.objects.create(user=self.student)

    def _login(self):
        resp = self.client.post('/api/game/login/', {
            'email': 'saver@test.com',
            'password': 'TestPass123!',
        })
        token = resp.json()['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')

    # ── PUT ──────────────────────────────────────────────────────────

    def test_save_game_success(self):
        self._login()
        resp = self.client.put(self.url, {
            'save_data': {
                'player_name': 'Hero',
                'selected_gender': 'male',
                'ch1_teaching_done': True,
                'ch1_quiz_done': True,
                'challenges_completed': 5,
            },
        }, format='json')
        self.assertEqual(resp.status_code, 200)
        self.assertIn('updated_at', resp.json())

    def test_save_unauthenticated(self):
        resp = self.client.put(self.url, {'save_data': {}}, format='json')
        self.assertEqual(resp.status_code, 401)

    def test_save_missing_data(self):
        self._login()
        resp = self.client.put(self.url, {}, format='json')
        self.assertEqual(resp.status_code, 400)

    def test_save_overwrites(self):
        """Second PUT should update, not duplicate."""
        self._login()
        self.client.put(self.url, {'save_data': {'player_name': 'A'}}, format='json')
        self.client.put(self.url, {'save_data': {'player_name': 'B'}}, format='json')
        resp = self.client.get(self.url)
        self.assertEqual(resp.json()['save_data']['player_name'], 'B')

    # ── GET ──────────────────────────────────────────────────────────

    def test_load_game_success(self):
        self._login()
        self.client.put(self.url, {
            'save_data': {'player_name': 'Hero'},
        }, format='json')
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()['save_data']['player_name'], 'Hero')

    def test_load_no_save(self):
        self._login()
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 404)

    # ── DELETE ───────────────────────────────────────────────────────

    def test_delete_save(self):
        self._login()
        self.client.put(self.url, {'save_data': {'player_name': 'X'}}, format='json')
        resp = self.client.delete(self.url)
        self.assertEqual(resp.status_code, 200)
        # Verify it's gone
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 404)

    def test_delete_no_save(self):
        self._login()
        resp = self.client.delete(self.url)
        self.assertEqual(resp.status_code, 404)

    # ── Progress computation ─────────────────────────────────────────

    def test_progress_computed(self):
        """Progress fields should be computed from save_data flags."""
        self._login()
        self.client.put(self.url, {
            'save_data': {
                'ch1_teaching_done': True,
                'ch1_quiz_done': True,
                'ch1_post_quiz_dialogue_done': True,
                'ch1_convenience_store_cutscene_done': True,
                'ch1_spaghetti_guy_cutscene_done': True,
                'ch2_y1s1_teaching_done': True,
                'ch2_y1s2_teaching_done': True,
                # rest are False/missing
                'challenges_completed': 12,
            },
        }, format='json')
        resp = self.client.get(self.url)
        data = resp.json()
        # 7 of 12 flags true → 58.3%
        self.assertAlmostEqual(data['story_progress_percent'], 58.3, places=1)
        self.assertEqual(data['challenges_completed'], 12)
        self.assertEqual(data['learning_modules_completed'], 2)
