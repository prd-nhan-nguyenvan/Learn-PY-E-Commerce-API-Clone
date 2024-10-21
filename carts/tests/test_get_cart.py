from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from carts.models import Cart
from carts.serializers import CartSerializer

User = get_user_model()


class GetCartViewTest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="testuser@gmail.com", username="testuser", password="testpass"
        )
        self.cart = Cart.objects.create(user=self.user)
        self.url = reverse("get-cart")

    @patch("django.core.cache.cache.get")
    @patch("django.core.cache.cache.set")
    def test_get_cart_from_cache(self, mock_cache_set, mock_cache_get):
        mock_cache_get.return_value = self.cart

        self.client.force_authenticate(user=self.user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        mock_cache_get.assert_called_with(f"user_cart_{self.user.id}")

        serializer = CartSerializer(self.cart)
        self.assertEqual(response.data, serializer.data)

    @patch("django.core.cache.cache.get")
    @patch("django.core.cache.cache.set")
    def test_get_cart_from_db_and_cache(self, mock_cache_set, mock_cache_get):
        mock_cache_get.return_value = None

        self.client.force_authenticate(user=self.user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        mock_cache_set.assert_called_with(
            f"user_cart_{self.user.id}", self.cart, timeout=60 * 5
        )

        serializer = CartSerializer(self.cart)
        self.assertEqual(response.data, serializer.data)

    @patch("django.core.cache.cache.get")
    def test_get_cart_does_not_exist(self, mock_cache_get):
        mock_cache_get.return_value = None

        self.client.force_authenticate(user=self.user)

        Cart.objects.filter(user=self.user).delete()

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data["detail"], "Cart is empty or does not exist.")

    def test_get_cart_unauthenticated(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
