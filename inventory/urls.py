from django.urls import path, include
from rest_framework.routers import DefaultRouter

from inventory.views import (
    WarehouseViewSet, ProductInventoryViewSet, InventoryTransactionViewSet,
    InventoryTransactionCreateViewSet
)

router = DefaultRouter()
router.register(r'warehouses', WarehouseViewSet, basename='warehouse')
router.register(r'inventory', ProductInventoryViewSet,
                basename='productinventory')
router.register(r'transactions', InventoryTransactionViewSet,
                basename='inventorytransaction')
router.register(r'transactions/create', InventoryTransactionCreateViewSet,
                basename='inventorytransaction-create')

urlpatterns = [
    path('', include(router.urls)),
]
