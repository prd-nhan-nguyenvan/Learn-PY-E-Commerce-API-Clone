from django.core.cache import cache
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Cart, CartItem
from .serializers import AddToCartSerializer, CartItemSerializer, CartSerializer


class AddToCartView(APIView):
    @swagger_auto_schema(
        tags=["Cart"],
        request_body=AddToCartSerializer,
        responses={
            201: openapi.Response(
                description="Item added to cart successfully",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "message": openapi.Schema(
                            type=openapi.TYPE_STRING,
                            example="Item added to cart successfully",
                        ),
                        "cart_item": {
                            "id": openapi.Schema(type=openapi.TYPE_INTEGER, example=1),
                            "product_id": openapi.Schema(
                                type=openapi.TYPE_INTEGER, example=1
                            ),
                            "quantity": openapi.Schema(
                                type=openapi.TYPE_INTEGER, example=1
                            ),
                        },
                    },
                ),
            ),
            400: openapi.Response(
                description="Invalid input data",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "detail": openapi.Schema(
                            type=openapi.TYPE_OBJECT
                        ),  # Detailed validation errors
                    },
                ),
            ),
            401: openapi.Response(
                description="Unauthorized",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "detail": openapi.Schema(
                            type=openapi.TYPE_STRING,
                            example="Authentication credentials were not provided.",
                        ),
                    },
                ),
            ),
        },
        operation_description="Add an item to the cart",
    )
    def post(self, request, *args, **kwargs):
        serializer = AddToCartSerializer(
            data=request.data, context={"request": request}
        )

        if serializer.is_valid():
            cart_item = self.add_to_cart(request.user, serializer.validated_data)

            cache_key = f"user_cart_{request.user.id}"
            cache.delete(cache_key)

            return Response(
                {
                    "message": "Item added to cart successfully",
                    "cart_item": CartItemSerializer(cart_item).data,
                },
                status=status.HTTP_201_CREATED,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def add_to_cart(self, user, validated_data):
        product = validated_data["product"]
        quantity = validated_data["quantity"]

        cart, _ = Cart.objects.get_or_create(user=user)

        cart_item, created = CartItem.objects.get_or_create(
            cart=cart, product=product, defaults={"quantity": quantity}
        )
        if not created:
            cart_item.quantity += quantity
            cart_item.save()

        return cart_item


class GetCartView(APIView):
    @swagger_auto_schema(
        tags=["Cart"],
        operation_description="Retrieve the cart for the logged-in user",
        responses={
            200: openapi.Response(
                description="A successful response with the user's cart",
                schema=CartSerializer,  # Describes the response structure
            ),
            401: openapi.Response(
                description="Unauthorized",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "detail": openapi.Schema(
                            type=openapi.TYPE_STRING,
                            example="Authentication credentials were not provided.",
                        ),
                    },
                ),
            ),
        },
    )
    def get(self, request, *args, **kwargs):
        cache_key = f"user_cart_{request.user.id}"
        cart = cache.get(cache_key)

        if cart is None:
            cart = Cart.objects.get_or_create(user=request.user)
            cache.set(cache_key, cart, timeout=60 * 5)

        serializer = CartSerializer(cart)
        return Response(serializer.data, status=status.HTTP_200_OK)


class UpdateRemoveCartItemView(APIView):
    @swagger_auto_schema(
        tags=["Cart"],
        responses={
            204: openapi.Response(description="Item removed from cart successfully"),
            404: openapi.Response(
                description="Cart item not found",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "detail": openapi.Schema(
                            type=openapi.TYPE_STRING, example="Item not found in cart."
                        ),
                    },
                ),
            ),
        },
        operation_description="Remove an item from the cart",
    )
    def delete(self, request, product_id, *args, **kwargs):
        cart_item = get_object_or_404(
            CartItem.objects.filter(cart__user=request.user), product_id=product_id
        )

        cart_item.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @swagger_auto_schema(
        tags=["Cart"],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "quantity": openapi.Schema(
                    type=openapi.TYPE_INTEGER, minimum=1, example=1
                )
            },
        ),
        responses={
            200: openapi.Response(
                description="Cart item updated successfully",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "message": openapi.Schema(
                            type=openapi.TYPE_STRING,
                            example="Cart item updated successfully",
                        ),
                        "cart_item": {
                            "id": openapi.Schema(type=openapi.TYPE_INTEGER, example=1),
                            "product_id": openapi.Schema(
                                type=openapi.TYPE_INTEGER, example=1
                            ),
                            "quantity": openapi.Schema(
                                type=openapi.TYPE_INTEGER, example=1
                            ),
                        },
                    },
                ),
            ),
            204: openapi.Response(description="Item removed from cart successfully"),
            404: openapi.Response(
                description="Cart item not found",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "detail": openapi.Schema(
                            type=openapi.TYPE_STRING, example="Item not found in cart."
                        ),
                    },
                ),
            ),
        },
        operation_description="Update the quantity of an item in the cart",
    )
    def patch(self, request, product_id, *args, **kwargs):
        cart_item = get_object_or_404(
            CartItem.objects.filter(cart__user=request.user), product_id=product_id
        )

        quantity = request.data.get("quantity")

        if quantity is None or quantity <= 0:
            cart_item.delete()
            return Response(
                {"detail": "Item removed from cart successfully."},
                status=status.HTTP_204_NO_CONTENT,
            )

        if quantity != cart_item.quantity:
            cart_item.quantity = quantity
            cart_item.save()

        return Response(
            {
                "message": "Cart item updated successfully",
                "cart_item": CartItemSerializer(cart_item).data,
            },
            status=status.HTTP_200_OK,
        )
