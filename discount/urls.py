from django.urls import path, include
from rest_framework.routers import DefaultRouter

from discount.views import (
    DiscountRuleViewSet, ProductDiscountViewSet, BulkPricingTierViewSet
)

router = DefaultRouter()
router.register(r'rules', DiscountRuleViewSet, basename='discountrule')
router.register(r'product-discounts', ProductDiscountViewSet,
                basename='productdiscount')
router.register(r'bulk-pricing', BulkPricingTierViewSet,
                basename='bulkpricingtier')

urlpatterns = [
    path('', include(router.urls)),
]
