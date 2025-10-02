from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q, Sum, F
from django.utils import timezone

from backend.permissions import IsAdminOrReadOnly
from .models import Warehouse, ProductInventory, InventoryTransaction
from .serializers import (
    WarehouseSerializer, ProductInventorySerializer, ProductInventoryCreateSerializer,
    ProductInventoryUpdateSerializer, InventoryTransactionSerializer,
    InventoryTransactionCreateSerializer, InventoryStockUpdateSerializer,
    WarehouseInventorySerializer, ProductInventoryDetailSerializer
)


class WarehouseViewSet(viewsets.ModelViewSet):
    """Manage warehouses"""

    queryset = Warehouse.objects.all()
    serializer_class = WarehouseSerializer
    permission_classes = [IsAdminOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'code', 'address']
    ordering_fields = ['name', 'code', 'created_at']

    def get_serializer_class(self):
        if self.action == 'overview':
            return WarehouseInventorySerializer
        return WarehouseSerializer

    @action(detail=True, methods=['get'])
    def inventory(self, request, pk=None):
        """Get all inventory items for a warehouse"""
        warehouse = self.get_object()
        inventory = warehouse.inventory.select_related(
            'product', 'variant').all()

        # Filter by low stock if requested
        low_stock = request.query_params.get('low_stock')
        if low_stock == 'true':
            inventory = inventory.filter(
                quantity_available__lte=F('reorder_level'))

        serializer = ProductInventorySerializer(inventory, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def overview(self, request, pk=None):
        """Get warehouse overview with statistics"""
        warehouse = self.get_object()
        serializer = WarehouseInventorySerializer(warehouse)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def active(self, request):
        """Get only active warehouses"""
        warehouses = self.get_queryset().filter(is_active=True)
        serializer = self.get_serializer(warehouses, many=True)
        return Response(serializer.data)


class ProductInventoryViewSet(viewsets.ModelViewSet):
    """Manage product inventory across warehouses"""

    queryset = ProductInventory.objects.select_related(
        'product', 'variant', 'warehouse'
    ).prefetch_related('transactions')
    permission_classes = [IsAdminOrReadOnly]
    filter_backends = [DjangoFilterBackend,
                       filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['warehouse', 'product', 'variant']
    search_fields = ['product__name', 'variant__name', 'warehouse__name']
    ordering_fields = ['quantity_available', 'quantity_on_hand', 'created_at']

    def get_serializer_class(self):
        if self.action == 'create':
            return ProductInventoryCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return ProductInventoryUpdateSerializer
        elif self.action == 'retrieve':
            return ProductInventoryDetailSerializer
        return ProductInventorySerializer

    @action(detail=False, methods=['get'])
    def low_stock(self, request):
        """Get items with low stock across all warehouses"""
        low_stock_items = self.get_queryset().filter(
            quantity_available__lte=F('reorder_level')
        )
        serializer = self.get_serializer(low_stock_items, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def out_of_stock(self, request):
        """Get out of stock items"""
        out_of_stock = self.get_queryset().filter(quantity_available=0)
        serializer = self.get_serializer(out_of_stock, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def reserve_stock(self, request, pk=None):
        """Reserve stock for an order"""
        inventory = self.get_object()
        quantity = request.data.get('quantity', 0)

        if quantity <= 0:
            return Response({'error': 'Quantity must be positive'},
                            status=status.HTTP_400_BAD_REQUEST)

        if inventory.quantity_available < quantity:
            return Response({'error': 'Insufficient stock available'},
                            status=status.HTTP_400_BAD_REQUEST)

        # Create reservation transaction
        InventoryTransaction.objects.create(
            inventory=inventory,
            transaction_type='RESERVE',
            quantity=quantity,
            reference_number=request.data.get('reference_number', ''),
            notes=f"Reserved for order",
            created_by=request.data.get('created_by', 'system')
        )

        # Update inventory
        inventory.quantity_available -= quantity
        inventory.quantity_reserved += quantity
        inventory.save()

        serializer = self.get_serializer(inventory)
        return Response(serializer.data)


class InventoryTransactionViewSet(viewsets.ReadOnlyModelViewSet):
    """View inventory transactions (read-only for audit trail)"""

    queryset = InventoryTransaction.objects.select_related(
        'inventory__product', 'inventory__variant', 'inventory__warehouse'
    ).all()
    serializer_class = InventoryTransactionSerializer
    permission_classes = [IsAdminOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['transaction_type',
                        'inventory__warehouse', 'inventory__product']
    ordering_fields = ['created_at', 'quantity']
    ordering = ['-created_at']

    @action(detail=False, methods=['get'])
    def recent(self, request):
        """Get recent transactions (last 7 days)"""
        seven_days_ago = timezone.now() - timezone.timedelta(days=7)
        recent_transactions = self.get_queryset().filter(created_at__gte=seven_days_ago)
        serializer = self.get_serializer(recent_transactions, many=True)
        return Response(serializer.data)


class InventoryTransactionCreateViewSet(viewsets.ModelViewSet):
    """Create new inventory transactions"""

    queryset = InventoryTransaction.objects.all()
    serializer_class = InventoryTransactionCreateSerializer
    permission_classes = [IsAdminOrReadOnly]

    # Only allow POST requests
    http_method_names = ['post']

    def perform_create(self, serializer):
        # Set created_by from request user if not provided
        if not serializer.validated_data.get('created_by') and self.request.user.is_authenticated:
            serializer.save(created_by=self.request.user.username)
        else:
            serializer.save()
