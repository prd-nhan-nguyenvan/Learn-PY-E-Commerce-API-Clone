from rest_framework import serializers

from .models import Category, Product, Review


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = [
            "id",
            "name",
            "slug",
            "description",
        ]
        read_only_fields = ["id", "slug"]


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = [
            "id",
            "category",
            "name",
            "slug",
            "description",
            "price",
            "sell_price",
            "on_sell",
            "stock",
            "image",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]

    def validate(self, data):
        price = data.get("price")
        sell_price = data.get("sell_price")

        if price is not None and price < 0:
            raise serializers.ValidationError({"price": "Price cannot be negative."})

        if sell_price is not None and sell_price < 0:
            raise serializers.ValidationError(
                {"sell_price": "Sell price cannot be negative."}
            )

        # If updating, get the current instance's price
        if self.instance:
            current_price = self.instance.price
            current_sell_price = self.instance.sell_price
        else:
            current_price = None
            current_sell_price = None

        if price is not None and sell_price is not None:
            if price < sell_price:
                raise serializers.ValidationError(
                    {"price": "Price cannot be less than the sell price."}
                )
        # Ensure sell price is not greater than the price
        elif sell_price is not None and current_price is not None:
            if sell_price > current_price:
                raise serializers.ValidationError(
                    {
                        "sell_price": "Sell price cannot be greater than the regular price."
                    }
                )
        elif price is not None and current_sell_price is not None:
            if price < current_sell_price:
                raise serializers.ValidationError(
                    {"price": "Price cannot be less than the sell price."}
                )

        return data


class ReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = [
            "id",
            "product",
            "user",
            "rating",
            "comment",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["user", "created_at", "updated_at"]

    def validate_rating(self, value):
        if value < 1 or value > 5:
            raise serializers.ValidationError("Rating must be between 1 and 5.")
        return value


class ProductSearchResponseSerializer(serializers.Serializer):
    count = serializers.IntegerField()
    next = serializers.CharField(allow_null=True, required=False)
    previous = serializers.CharField(allow_null=True, required=False)
    results = ProductSerializer(many=True)
