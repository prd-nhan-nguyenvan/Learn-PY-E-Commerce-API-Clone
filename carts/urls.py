from django.urls import path

from carts.views import AddToCartView, GetCartView, RemoveFromCartView

urlpatterns = [
    path("", GetCartView.as_view(), name="get-cart"),
    path("items/", AddToCartView.as_view(), name="add-to-cart"),
    path(
        "items/<int:product_id>/", RemoveFromCartView.as_view(), name="remove-from-cart"
    ),
]
