from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from carts.models import Cart, CartItem
from products.models import Product

User = get_user_model()


class AddToCartViewTest(APITestCase):
    def setUp(self):
        # Create a test user
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

        # Fetch the product as a Product instance from the database
        self.product = Product.objects.get(id=product_response.data["id"])

        # URL for adding to cart
        self.url = reverse("add-to-cart")

    def test_add_item_to_cart_success(self):
        """Test successful addition of an item to the cart."""
        self.client.force_authenticate(user=self.user)
        data = {"product_id": self.product.id, "quantity": 2}

        response = self.client.post(self.url, data, format="json")

        # Assert successful addition
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["message"], "Item added to cart successfully")
        self.assertEqual(response.data["cart_item"]["quantity"], 2)

        # Check that the item was added to the cart
        cart = Cart.objects.get(user=self.user)
        cart_item = CartItem.objects.get(cart=cart, product=self.product)
        self.assertEqual(cart_item.quantity, 2)

        # Ensure the cache was invalidated
        cache_key = f"user_cart_{self.user.id}"
        self.assertIsNone(cache.get(cache_key))

    def test_add_item_exceeds_stock(self):
        """Test adding an item to the cart with quantity exceeding stock."""
        self.client.force_authenticate(user=self.user)
        data = {
            "product_id": self.product.id,
            "quantity": 20,  # Exceeds available stock
        }

        response = self.client.post(self.url, data, format="json")

        # Assert failure due to stock issues
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn(
            f"Only {self.product.stock} items in stock.",
            response.data["non_field_errors"],
        )

    def test_unauthenticated_user_cannot_add_to_cart(self):
        self.client.logout()
        data = {"product_id": self.product.id, "quantity": 2}

        response = self.client.post(self.url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_update_existing_cart_item_quantity(self):
        self.client.force_authenticate(user=self.user)
        cart = Cart.objects.create(user=self.user)
        cart_item = CartItem.objects.create(cart=cart, product=self.product, quantity=3)

        # Add more quantity to the same item
        data = {
            "product_id": self.product.id,
            "quantity": 2,  # Adding 2 more to the existing 3
        }

        response = self.client.post(self.url, data, format="json")

        # Assert successful addition
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["cart_item"]["quantity"], 5)  # 3 + 2 = 5

        # Verify in the database
        cart_item.refresh_from_db()
        self.assertEqual(cart_item.quantity, 5)

        # Ensure the cache was invalidated
        cache_key = f"user_cart_{self.user.id}"
        self.assertIsNone(cache.get(cache_key))
