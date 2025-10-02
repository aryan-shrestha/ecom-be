import time
from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q, Count, Prefetch

from backend.permissions import IsAdminOrReadOnly

from product.models import Product, ProductAttribute, ProductAttributeValue, ProductVariant, ProductVariantAttribute
from product.serializers import (
    ProductReadSerializer, ProductWritableSerializer, ProductDetailSerializer,
    ProductListSerializer, ProductAttributeSerializer, ProductAttributeValueSerializer,
    ProductVariantSerializer, ProductVariantCreateSerializer, ProductVariantAttributeSerializer
)


class ProductViewSet(viewsets.ModelViewSet):
    """Full CRUD for Product with enhanced functionality"""

    permission_classes = [IsAdminOrReadOnly]
    filter_backends = [DjangoFilterBackend,
                       filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category__slug', 'category__id']
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'price', 'created_at']
    lookup_field = 'slug'

    def get_serializer_class(self):
        if self.action == 'list':
            return ProductListSerializer
        elif self.action == 'retrieve':
            return ProductDetailSerializer
        elif self.request.method in ['POST', 'PUT', 'PATCH']:
            return ProductWritableSerializer
        else:
            return ProductReadSerializer

    def get_queryset(self):
        """Optimized queryset with proper prefetching"""
        queryset = Product.objects.select_related('category').prefetch_related(
            Prefetch('variants', queryset=ProductVariant.objects.select_related().prefetch_related(
                'attributes__attribute_value__attribute'
            ))
        )

        # Filter by price range
        min_price = self.request.query_params.get('min_price')
        max_price = self.request.query_params.get('max_price')
        if min_price:
            queryset = queryset.filter(price__gte=min_price)
        if max_price:
            queryset = queryset.filter(price__lte=max_price)

        return queryset

    @action(detail=True, methods=['get'])
    def variants(self, request, slug=None):
        """Get all variants for a product"""
        product = self.get_object()
        variants = product.variants.prefetch_related(
            'attributes__attribute_value__attribute')
        serializer = ProductVariantSerializer(variants, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def add_variant(self, request, slug=None):
        """Add a new variant to a product"""
        product = self.get_object()
        serializer = ProductVariantCreateSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(product=product)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def search(self, request):
        """Advanced search with filters"""
        queryset = self.get_queryset()

        # Search by attributes
        attribute_filters = request.query_params.get('attributes')
        if attribute_filters:
            attribute_ids = [
                int(x) for x in attribute_filters.split(',') if x.isdigit()]
            queryset = queryset.filter(
                variants__attributes__attribute_value__id__in=attribute_ids
            ).distinct()

        # Apply other filters
        queryset = self.filter_queryset(queryset)

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class ProductAttributeViewSet(viewsets.ModelViewSet):
    """Manage product attributes like Color, Size, etc."""

    queryset = ProductAttribute.objects.prefetch_related('values')
    serializer_class = ProductAttributeSerializer
    permission_classes = [IsAdminOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'display_name']
    ordering_fields = ['name', 'created_at']

    @action(detail=True, methods=['get'])
    def values(self, request, pk=None):
        """Get all values for an attribute"""
        attribute = self.get_object()
        values = attribute.values.all()
        serializer = ProductAttributeValueSerializer(values, many=True)
        return Response(serializer.data)


class ProductAttributeValueViewSet(viewsets.ModelViewSet):
    """Manage specific attribute values"""

    queryset = ProductAttributeValue.objects.select_related('attribute')
    serializer_class = ProductAttributeValueSerializer
    permission_classes = [IsAdminOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['attribute']
    search_fields = ['value', 'display_value']


class ProductVariantViewSet(viewsets.ModelViewSet):
    """Manage product variants"""

    queryset = ProductVariant.objects.select_related('product').prefetch_related(
        'attributes__attribute_value__attribute'
    )
    permission_classes = [IsAdminOrReadOnly]
    filter_backends = [DjangoFilterBackend,
                       filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['product', 'is_active']
    search_fields = ['name', 'sku']
    ordering_fields = ['sku', 'created_at', 'final_price']

    def get_serializer_class(self):
        if self.action == 'create':
            return ProductVariantCreateSerializer
        return ProductVariantSerializer

    @action(detail=True, methods=['post'])
    def update_attributes(self, request, pk=None):
        """Update variant attributes"""
        variant = self.get_object()
        attribute_values = request.data.get('attribute_values', [])

        # Clear existing attributes
        variant.attributes.all().delete()

        # Add new attributes
        for attr_value_id in attribute_values:
            ProductVariantAttribute.objects.create(
                variant=variant,
                attribute_value_id=attr_value_id
            )

        serializer = self.get_serializer(variant)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def by_attributes(self, request):
        """Find variants by attribute combinations"""
        attribute_values = request.query_params.get(
            'attributes', '').split(',')
        if not attribute_values or not all(x.isdigit() for x in attribute_values):
            return Response({'error': 'Valid attribute value IDs required'},
                            status=status.HTTP_400_BAD_REQUEST)

        variants = self.get_queryset().filter(
            attributes__attribute_value__id__in=attribute_values
        ).annotate(
            matched_attributes=Count('attributes__attribute_value',
                                     filter=Q(attributes__attribute_value__id__in=attribute_values))
        ).filter(matched_attributes=len(attribute_values))

        serializer = self.get_serializer(variants, many=True)
        return Response(serializer.data)
