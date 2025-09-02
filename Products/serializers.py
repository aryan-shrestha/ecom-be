from rest_framework import serializers
from drf_writable_nested.serializers import WritableNestedModelSerializer
from cloudinary import CloudinaryImage

from Products.models import Product, ProductImages, Category
from category.serializers import CategorySerializer


class ProductImageSerializer(serializers.ModelSerializer):
    url = serializers.SerializerMethodField()

    class Meta:
        model = ProductImages
        fields = ['id', 'url']

    def get_url(self, obj):
        return CloudinaryImage(obj.image.url).build_url()


class ProductSerializer(WritableNestedModelSerializer):
    images = ProductImageSerializer(many=True)
    category = CategorySerializer()

    class Meta:
        model = Product
        fields = ['id', 'name', 'slug', 'description', 'category', 'og_price',
                  'dis_price', 'stock', 'dis_percentage', 'created_at', 'modified_at', 'images']
