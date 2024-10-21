from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from authentication.models import CustomUser


class ProductListTest(APITestCase):
    def setUp(self):
        self.admin_user = CustomUser.objects.create_superuser(
            email="admintest@gmail.com",
            username="adminuser",
            password="adminpassword",
        )

        self.client.force_authenticate(user=self.admin_user)

        self.url = reverse("product-list-create")

        self.category1 = self.client.post(
            reverse("category-list-create"),
            data={"name": "Category 1", "description": "Description 1"},
        )
        self.category2 = self.client.post(
            reverse("category-list-create"),
            data={"name": "Category 2", "description": "Description 2"},
        )
        self.client.post(
            reverse("product-list-create"),
            data={
                "category": self.category1.data["id"],
                "name": "Organic Extra Virgin Olive Oil",
                "description": "Cold-pressed, organic olive oil with a rich and fruity flavor.",
                "price": "15.99",
                "sell_price": "14.99",
                "on_sell": True,
                "stock": 300,
            },
        )
        self.client.post(
            reverse("product-list-create"),
            data={
                "category": self.category2.data["id"],
                "name": "Organic Coconut Oil",
                "description": "Cold-pressed, organic coconut oil with a subtle coconut flavor.",
                "price": "12.99",
                "sell_price": "11.99",
                "on_sell": False,
                "stock": 200,
            },
        )

        self.client = self.client_class()

    def test_admin_can_create_product(self):
        """Test that an admin user can create a product."""
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.post(
            self.url,
            data={
                "category": self.category1.data["id"],
                "name": "Test Product",
                "description": "Test Description",
                "price": "9.99",
                "sell_price": "8.99",
                "on_sell": True,
                "stock": 100,
            },
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["name"], "Test Product")

    def test_non_admin_cannot_create_product(self):
        """Test that a non-admin user cannot create a product."""
        regular_user = CustomUser.objects.create_user(
            email="noadmin@gmail.com",
            username="noadminuser",
            password="noadminpassword",
        )
        self.client.force_authenticate(user=regular_user)
        response = self.client.post(
            self.url,
            data={
                "category": self.category1.data["id"],
                "name": "Test Product",
                "description": "Test Description",
                "price": "9.99",
                "sell_price": "8.99",
                "on_sell": True,
                "stock": 100,
            },
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_get_all_products(self):
        """Test that an admin user can get the list of all products."""
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(response.data["count"], 2)
        self.assertEqual(response.data["results"][0]["name"], "Organic Coconut Oil")
        self.assertEqual(
            response.data["results"][1]["name"], "Organic Extra Virgin Olive Oil"
        )
