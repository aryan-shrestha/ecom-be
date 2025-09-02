import time
from rest_framework import viewsets, filters
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from django_filters.rest_framework import DjangoFilterBackend

from Products.models import Product
from Products.serializers import ProductSerializer


class ProductViewSet(viewsets.ModelViewSet):
    """Full CRUD for Product. Uses slug as lookup field and supports filtering, search and ordering."""
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend,
                       filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category__slug']
    search_fields = ['name',]
    ordering_fields = ['name', 'og_price']

    def get_queryset(self):
        """Optionally restricts the returned products to a given category."""
        time.sleep(2)  # Simulate delay for testing loading states
        return super().get_queryset()
