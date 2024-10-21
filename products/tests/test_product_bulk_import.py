from io import BytesIO
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

User = get_user_model()


class BulkImportProductViewTest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_superuser(
            email="admin@gmail.com", username="admin", password="password"
        )
        self.client.force_authenticate(user=self.user)
        self.url = reverse("bulk-import-products")

    @patch("products.tasks.bulk_import_products.delay")  # Mock the Celery task
    def test_bulk_import_no_file_provided(self, mock_bulk_import):
        response = self.client.post(self.url, {})

        # Assert that the response is 400 when no file is provided
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["error"], "No file provided.")

    @patch("products.tasks.bulk_import_products.delay")
    def test_bulk_import_with_valid_file(self, mock_bulk_import):
        csv_file = BytesIO(
            b"name,description,price,sell_price,on_sell,stock,category_name,image_url\nProduct1,Description1,10,9,1,100,Category1,https://example.com/image1.jpg\nProduct2,Description2,20,18,0,200,Category2,https://example.com/image2.jpg"
        )
        csv_file.name = "products.csv"

        # Make the request with the file
        response = self.client.post(self.url, {"file": csv_file}, format="multipart")

        # Assert that the response is 202 (Accepted) and the Celery task was called
        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
        mock_bulk_import.assert_called_once()

    @patch("products.tasks.bulk_import_products.delay")
    def test_bulk_import_with_invalid_csv(self, mock_bulk_import):
        invalid_csv_file = BytesIO(
            b"name,description\nProduct1,Description1\nProduct2,Description2"
        )
        invalid_csv_file.name = "invalid_products.csv"

        response = self.client.post(
            self.url, {"file": invalid_csv_file}, format="multipart"
        )

        # Assert that the response is 400 (Bad Request) due to invalid data
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)
