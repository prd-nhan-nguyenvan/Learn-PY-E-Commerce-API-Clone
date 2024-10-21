from django.core.cache import cache
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Cart, CartItem
from .serializers import AddToCartSerializer, CartItemSerializer, CartSerializer


class AddToCartView(APIView):
    @swagger_auto_schema(tags=["Cart"], request_body=AddToCartSerializer)
    def post(self, request, *args, **kwargs):
        serializer = AddToCartSerializer(
            data=request.data, context={"request": request}
        )
        if serializer.is_valid():
            cart_item = serializer.save()
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


class GetCartView(APIView):
    @swagger_auto_schema(
        tags=["Cart"],
        operation_description="Retrieve the cart for the logged-in user",
        responses={
            200: openapi.Response(
                description="A successful response with the user's cart",
                schema=CartSerializer,  # Describes the response structure
            ),
            404: openapi.Response(
                description="Cart is empty or does not exist",
            ),
        },
    )
    def get(self, request, *args, **kwargs):
        cache_key = f"user_cart_{request.user.id}"
        cart = cache.get(cache_key)

        if cart is None:
            cart = Cart.objects.filter(user=request.user).first()
            cache.set(cache_key, cart, timeout=60 * 5)

        if not cart:
            return Response(
                {"detail": "Cart is empty or does not exist."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = CartSerializer(cart)
        return Response(serializer.data, status=status.HTTP_200_OK)


class RemoveFromCartView(APIView):
    @swagger_auto_schema(tags=["Cart"])
    def delete(self, request, product_id, *args, **kwargs):
        cart_item = CartItem.objects.filter(
            cart__user=request.user, product_id=product_id
        ).first()

        if not cart_item:
            return Response(
                {"detail": "Item not found in cart."}, status=status.HTTP_404_NOT_FOUND
            )

        cart_item.delete()

        return Response(
            {"detail": "Item removed from cart successfully."},
            status=status.HTTP_204_NO_CONTENT,
        )
