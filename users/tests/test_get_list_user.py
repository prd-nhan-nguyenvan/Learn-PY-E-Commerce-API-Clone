from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from authentication.models import CustomUser


class UserListTest(APITestCase):
    def setUp(self):
        self.admin_user = CustomUser.objects.create_superuser(
            email="admin@example.com",
            username="adminuser",
            password="adminpassword",
        )

        self.regular_user = CustomUser.objects.create_user(
            email="user@example.com",
            username="regularuser",
            password="userpassword",
        )
        self.client = self.client_class()

        self.url = reverse("user-list")

    def test_admin_can_list_users(self):
        """Test that an admin user can get the list of all users."""
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(len(response.data["results"]), 2)
        self.assertEqual(response.data["results"][0]["email"], self.regular_user.email)
        self.assertEqual(response.data["results"][1]["email"], self.admin_user.email)

    def test_non_admin_cannot_list_users(self):
        """Test that a non-admin user cannot access the list of users."""
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_unauthenticated_user_cannot_list_users(self):
        """Test that an unauthenticated user cannot access the list of users."""
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
