from django.urls import path, include
from rest_framework.routers import DefaultRouter

from product.views import (
    ProductViewSet, ProductAttributeViewSet, ProductAttributeValueViewSet,
    ProductVariantViewSet
)

router = DefaultRouter()
router.register(r'products', ProductViewSet, basename='product')
router.register(r'attributes', ProductAttributeViewSet,
                basename='productattribute')
router.register(r'attribute-values', ProductAttributeValueViewSet,
                basename='productattributevalue')
router.register(r'variants', ProductVariantViewSet, basename='productvariant')

urlpatterns = [
    path('', include(router.urls)),
]
