from django.urls import path

from .views import (
    AddOrderItemView,
    OrderListCreateView,
    OrderRetrieveUpdateDestroyView,
    RemoveFromOrderView,
)

urlpatterns = [
    path("", OrderListCreateView.as_view(), name="order-list-create"),
    path("<int:pk>/", OrderRetrieveUpdateDestroyView.as_view(), name="order-detail"),
    path("<int:order_id>/add/", AddOrderItemView.as_view(), name="add-order-item"),
    path(
        "<int:order_id>/remove/<int:product_id>",
        RemoveFromOrderView.as_view(),
        name="add-order-item",
    ),
]
