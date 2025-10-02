from rest_framework import serializers
from drf_writable_nested.serializers import WritableNestedModelSerializer
from category.serializers import CategorySerializer
from product.models import Product, ProductAttribute, ProductAttributeValue, ProductVariant, ProductVariantAttribute


# Product Attribute Serializers
class ProductAttributeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductAttribute
        fields = ['id', 'name', 'display_name', 'is_required', 'created_at']
        read_only_fields = ['id', 'created_at']


class ProductAttributeValueSerializer(serializers.ModelSerializer):
    attribute = ProductAttributeSerializer(read_only=True)
    attribute_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = ProductAttributeValue
        fields = ['id', 'attribute', 'attribute_id',
                  'value', 'display_value', 'hex_color']
        read_only_fields = ['id']


# Product Variant Serializers
class ProductVariantAttributeSerializer(serializers.ModelSerializer):
    attribute_value = ProductAttributeValueSerializer(read_only=True)
    attribute_value_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = ProductVariantAttribute
        fields = ['id', 'attribute_value', 'attribute_value_id']
        read_only_fields = ['id']


class ProductVariantSerializer(serializers.ModelSerializer):
    attributes = ProductVariantAttributeSerializer(many=True, read_only=True)
    final_price = serializers.ReadOnlyField()

    class Meta:
        model = ProductVariant
        fields = ['id', 'sku', 'name', 'price_adjustment', 'images', 'is_active',
                  'final_price', 'attributes', 'created_at', 'modified_at']
        read_only_fields = ['id', 'final_price', 'created_at', 'modified_at']


class ProductVariantCreateSerializer(serializers.ModelSerializer):
    attributes = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False,
        help_text="List of ProductAttributeValue IDs"
    )

    class Meta:
        model = ProductVariant
        fields = ['id', 'product', 'sku', 'name', 'price_adjustment', 'images',
                  'is_active', 'attributes']
        read_only_fields = ['id']

    def create(self, validated_data):
        attributes_data = validated_data.pop('attributes', [])
        variant = ProductVariant.objects.create(**validated_data)

        # Create variant attributes
        for attr_value_id in attributes_data:
            ProductVariantAttribute.objects.create(
                variant=variant,
                attribute_value_id=attr_value_id
            )

        return variant


# Product Serializers
class ProductReadSerializer(WritableNestedModelSerializer):
    category = CategorySerializer(read_only=True)
    variants = ProductVariantSerializer(many=True, read_only=True)

    class Meta:
        model = Product
        fields = ['id', 'name', 'slug', 'description', 'category', 'price',
                  'created_at', 'modified_at', 'images', 'variants']
        read_only_fields = fields


class ProductWritableSerializer(WritableNestedModelSerializer):
    class Meta:
        model = Product
        fields = ['id', 'name', 'slug', 'description', 'category', 'price',
                  'created_at', 'modified_at', 'images']
        read_only_fields = ['id', 'created_at', 'modified_at', 'slug']


class ProductDetailSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    variants = ProductVariantSerializer(many=True, read_only=True)

    class Meta:
        model = Product
        fields = ['id', 'name', 'slug', 'description', 'category', 'price',
                  'created_at', 'modified_at', 'images', 'variants']


class ProductListSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    variants_count = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = ['id', 'name', 'slug', 'description', 'category', 'price',
                  'created_at', 'images', 'variants_count']

    def get_variants_count(self, obj):
        return obj.variants.count()
