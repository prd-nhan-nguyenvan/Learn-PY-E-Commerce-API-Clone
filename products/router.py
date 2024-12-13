# products/router.py
from django.urls import include, path
from rest_framework import routers

from products.views import CategoryViewSet, ProductViewSet

router = routers.SimpleRouter(trailing_slash=True)

# Register viewsets
router.register(r"categories", CategoryViewSet, basename="category")
router.register(r"products", ProductViewSet, basename="product")

urlpatterns = [
    path("", include(router.urls)),
]