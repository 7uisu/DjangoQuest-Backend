from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase


class LoginTokenTests(APITestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            email="StudentOne@Example.com",
            username="StudentOne",
            password="TestPass123!",
        )

    def test_login_accepts_exact_email(self):
        response = self.client.post(
            "/api/users/token/",
            {"email": "StudentOne@Example.com", "password": "TestPass123!"},
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("access", response.data)

    def test_login_accepts_email_case_insensitively(self):
        response = self.client.post(
            "/api/users/token/",
            {"email": "studentone@example.com", "password": "TestPass123!"},
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("access", response.data)

    def test_login_accepts_username_case_insensitively(self):
        response = self.client.post(
            "/api/users/token/",
            {"email": "studentone", "password": "TestPass123!"},
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("access", response.data)
