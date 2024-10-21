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

        if product.stock < quantity:
            raise serializers.ValidationError(f"Only {product.stock} items in stock.")

        data["product"] = product
        return data
