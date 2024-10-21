from django.shortcuts import get_object_or_404
from rest_framework import serializers

from carts.models import Cart, CartItem
from products.models import Product


class CartItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = CartItem
        fields = ["id", "product", "quantity"]


class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)

    class Meta:
        model = Cart
        fields = ["items"]


class AddToCartSerializer(serializers.Serializer):
    product_id = serializers.IntegerField()
    quantity = serializers.IntegerField(min_value=1)

    def validate(self, data):
        product_id = data.get("product_id")
        quantity = data.get("quantity")

        # Check if the product exists
        product = get_object_or_404(Product, id=product_id)

        # Validate that the requested quantity is less than or equal to stock
        if product.stock < quantity:
            raise serializers.ValidationError(f"Only {product.stock} items in stock.")

        data["product"] = product
        return data

    def create(self, validated_data):
        user = self.context["request"].user
        product = validated_data["product"]
        quantity = validated_data["quantity"]

        # Get or create the user's cart
        cart, created = Cart.objects.get_or_create(user=user)

        # Check if the product is already in the cart
        cart_item, item_created = CartItem.objects.get_or_create(
            cart=cart, product=product, defaults={"quantity": quantity}
        )

        if not item_created:
            # If the item exists, update the quantity
            cart_item.quantity += quantity
            cart_item.save()

        return cart_item
