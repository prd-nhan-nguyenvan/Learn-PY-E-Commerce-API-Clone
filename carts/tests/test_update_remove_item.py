from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from products.models import Product

User = get_user_model()


class UpdateRemoveItemViewTest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="user@example.com", password="testpassword", username="user"
        )

        self.admin_user = User.objects.create_superuser(
            email="admintest@gmail.com",
            username="adminuser",
            password="adminpassword",
        )

        self.client.force_authenticate(user=self.admin_user)

        # Create categories
        category1_response = self.client.post(
            reverse("category-list-create"),
            data={"name": "Category 1", "description": "Description 1"},
        )

        # Create a product and fetch it as a Product instance from the database
        product_response = self.client.post(
            reverse("product-list-create"),
            data={
                "category": category1_response.data["id"],
                "name": "Organic Extra Virgin Olive Oil",
                "description": "Cold-pressed, organic olive oil with a rich and fruity flavor.",
                "price": "15.99",
                "sell_price": "14.99",
                "on_sell": True,
                "stock": 10,
            },
        )

        self.product = Product.objects.get(id=product_response.data["id"])
        self.client.force_authenticate(user=self.user)

        # Add the product to the cart
        data = {"product_id": self.product.id, "quantity": 2}
        self.client.post(reverse("add-to-cart"), data, format="json")

        self.url = reverse("update-remove-from-cart", args=[self.product.id])

    def test_update_item_from_cart_success(self):
        """Test successful removal of an item from the cart."""
        self.client.force_authenticate(user=self.user)
        data = {"quantity": 2}

        response = self.client.patch(self.url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_remove_item_from_cart_success(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.delete(
            self.url,
        )

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_remove_item_from_cart_failure(self):
        self.client.force_authenticate(user=self.user)

        self.url = reverse("update-remove-from-cart", args=[self.product.id + 1])

        response = self.client.delete(self.url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
