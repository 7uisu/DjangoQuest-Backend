# dashboard/tests.py
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from game_api.models import GameSave
from users.models import EducatorAccessCode, Classroom, Profile

User = get_user_model()


class EducatorAccessCodeTest(TestCase):
    def test_seed_code_exists(self):
        """The CAPSTONE-2026 code should be seeded by data migration."""
        self.assertTrue(
            EducatorAccessCode.objects.filter(code='CAPSTONE-2026', is_active=True).exists()
        )


class StudentRegistrationTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.url = reverse('dashboard:student_register')

    def test_get_form(self):
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'In-Game Username')

    def test_successful_registration(self):
        resp = self.client.post(self.url, {
            'username': 'player1',
            'email': 'player1@test.com',
            'password': 'TestPass123!',
            'password_confirm': 'TestPass123!',
        })
        self.assertRedirects(resp, reverse('dashboard:login'))
        user = User.objects.get(username='player1')
        self.assertTrue(user.is_student)
        self.assertFalse(user.is_teacher)
        self.assertTrue(Profile.objects.filter(user=user).exists())

    def test_duplicate_username(self):
        User.objects.create_user(email='a@b.com', username='player1', password='x')
        resp = self.client.post(self.url, {
            'username': 'player1',
            'email': 'new@test.com',
            'password': 'TestPass123!',
            'password_confirm': 'TestPass123!',
        })
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'already taken')

    def test_password_mismatch(self):
        resp = self.client.post(self.url, {
            'username': 'player2',
            'email': 'p2@test.com',
            'password': 'TestPass123!',
            'password_confirm': 'WrongPass!',
        })
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'do not match')


class TeacherRegistrationTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.url = reverse('dashboard:teacher_register')
        EducatorAccessCode.objects.get_or_create(code='CAPSTONE-2026', defaults={'is_active': True})

    def test_valid_educator_code(self):
        resp = self.client.post(self.url, {
            'username': 'teacher1',
            'email': 'teacher1@test.com',
            'password': 'TeachPass123!',
            'password_confirm': 'TeachPass123!',
            'educator_access_code': 'CAPSTONE-2026',
        })
        self.assertRedirects(resp, reverse('dashboard:login'))
        user = User.objects.get(username='teacher1')
        self.assertTrue(user.is_teacher)
        self.assertFalse(user.is_student)

    def test_invalid_educator_code(self):
        resp = self.client.post(self.url, {
            'username': 'teacher2',
            'email': 'teacher2@test.com',
            'password': 'TeachPass123!',
            'password_confirm': 'TeachPass123!',
            'educator_access_code': 'WRONG-CODE',
        })
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'Invalid or expired')
        self.assertFalse(User.objects.filter(username='teacher2').exists())


class LoginRedirectTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.url = reverse('dashboard:login')
        self.teacher = User.objects.create_user(
            email='t@test.com', username='teach', password='TestPass123!'
        )
        self.teacher.is_teacher = True
        self.teacher.is_student = False
        self.teacher.save()
        Profile.objects.create(user=self.teacher)

        self.student = User.objects.create_user(
            email='s@test.com', username='stud', password='TestPass123!'
        )
        self.student.is_student = True
        self.student.is_teacher = False
        self.student.save()
        Profile.objects.create(user=self.student)

    def test_teacher_redirects_to_dashboard(self):
        resp = self.client.post(self.url, {
            'email': 't@test.com', 'password': 'TestPass123!'
        })
        self.assertRedirects(resp, reverse('dashboard:teacher_dashboard'))

    def test_student_redirects_to_profile(self):
        resp = self.client.post(self.url, {
            'email': 's@test.com', 'password': 'TestPass123!'
        })
        self.assertRedirects(resp, reverse('dashboard:student_profile'))

    def test_invalid_credentials(self):
        resp = self.client.post(self.url, {
            'email': 't@test.com', 'password': 'wrong'
        })
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'Invalid email or password')


class DashboardAccessTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.teacher = User.objects.create_user(
            email='t@test.com', username='teach', password='TestPass123!'
        )
        self.teacher.is_teacher = True
        self.teacher.is_student = False
        self.teacher.save()
        Profile.objects.create(user=self.teacher)

        self.student = User.objects.create_user(
            email='s@test.com', username='stud', password='TestPass123!'
        )
        Profile.objects.create(user=self.student)

    def test_teacher_can_access_dashboard(self):
        self.client.login(email='t@test.com', password='TestPass123!')
        resp = self.client.get(reverse('dashboard:teacher_dashboard'))
        self.assertEqual(resp.status_code, 200)

    def test_student_cannot_access_dashboard(self):
        self.client.login(email='s@test.com', password='TestPass123!')
        resp = self.client.get(reverse('dashboard:teacher_dashboard'))
        self.assertEqual(resp.status_code, 403)

    def test_unauthenticated_redirect(self):
        resp = self.client.get(reverse('dashboard:teacher_dashboard'))
        self.assertRedirects(resp, '/login/?next=/dashboard/')


class ClassroomTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.teacher = User.objects.create_user(
            email='t@test.com', username='teach', password='TestPass123!'
        )
        self.teacher.is_teacher = True
        self.teacher.is_student = False
        self.teacher.save()
        Profile.objects.create(user=self.teacher)
        self.client.login(email='t@test.com', password='TestPass123!')

    def test_create_classroom(self):
        resp = self.client.post(reverse('dashboard:teacher_dashboard'), {
            'name': 'CS101 - Spring 2026',
        })
        self.assertRedirects(resp, reverse('dashboard:teacher_dashboard'))
        classroom = Classroom.objects.get(name='CS101 - Spring 2026')
        self.assertEqual(classroom.teacher, self.teacher)
        self.assertEqual(len(classroom.enrollment_code), 8)

    def test_enrollment_code_unique(self):
        Classroom.objects.create(teacher=self.teacher, name='A')
        Classroom.objects.create(teacher=self.teacher, name='B')
        codes = list(Classroom.objects.values_list('enrollment_code', flat=True))
        self.assertEqual(len(codes), len(set(codes)))


class LeaderboardApiTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.teacher = User.objects.create_user(
            email='teacher@test.com', username='teacher', password='TestPass123!'
        )
        self.teacher.is_teacher = True
        self.teacher.is_student = False
        self.teacher.save()
        Profile.objects.create(user=self.teacher)
        self.classroom = Classroom.objects.create(teacher=self.teacher, name='CS101')

    def _student_with_score(self, username, xp, progress, achievements_count=0):
        user = User.objects.create_user(
            email=f'{username}@test.com', username=username, password='TestPass123!'
        )
        user.is_student = True
        user.save()
        profile = Profile.objects.create(user=user, total_xp=xp, classroom=self.classroom)
        profile.classrooms.add(self.classroom)
        GameSave.objects.create(
            user=user,
            save_data={},
            story_progress_percent=progress,
        )
        user.achievements_count = achievements_count
        return user

    def test_equal_scores_share_rank(self):
        first = self._student_with_score('first', 100, 100.0)
        second = self._student_with_score('second', 100, 100.0)
        third = self._student_with_score('third', 50, 80.0)

        self.client.force_authenticate(user=first)
        resp = self.client.get('/api/dashboard/leaderboard/?scope=classroom')

        self.assertEqual(resp.status_code, 200)
        ranks = {entry['username']: entry['rank'] for entry in resp.json()['entries']}
        self.assertEqual(ranks[first.username], 1)
        self.assertEqual(ranks[second.username], 1)
        self.assertEqual(ranks[third.username], 3)

    def test_xp_ranks_before_story_progress(self):
        high_xp = self._student_with_score('highxp', 120, 50.0)
        high_progress = self._student_with_score('highprogress', 80, 100.0)

        self.client.force_authenticate(user=high_xp)
        resp = self.client.get('/api/dashboard/leaderboard/?scope=classroom')

        self.assertEqual(resp.status_code, 200)
        entries = resp.json()['entries']
        self.assertEqual(entries[0]['username'], high_xp.username)
        self.assertEqual(entries[1]['username'], high_progress.username)


class ResetPasswordTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.teacher = User.objects.create_user(
            email='t@test.com', username='teach', password='TestPass123!'
        )
        self.teacher.is_teacher = True
        self.teacher.is_student = False
        self.teacher.save()
        Profile.objects.create(user=self.teacher)

        self.student = User.objects.create_user(
            email='s@test.com', username='stud', password='OldPass123!'
        )
        self.student_profile = Profile.objects.create(user=self.student)

        self.classroom = Classroom.objects.create(teacher=self.teacher, name='Test')
        self.student_profile.classroom = self.classroom
        self.student_profile.save()

        self.client.login(email='t@test.com', password='TestPass123!')

    def test_reset_student_password(self):
        url = reverse('dashboard:reset_student_password', args=[self.classroom.id, self.student.id])
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'Temporary Password')
        # Verify old password no longer works
        self.student.refresh_from_db()
        self.assertFalse(self.student.check_password('OldPass123!'))
