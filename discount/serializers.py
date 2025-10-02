from rest_framework import serializers
from django.utils import timezone
from .models import DiscountRule, ProductDiscount, BulkPricingTier
from product.serializers import ProductListSerializer, ProductVariantSerializer


class DiscountRuleSerializer(serializers.ModelSerializer):
    is_valid_now = serializers.SerializerMethodField()
    days_remaining = serializers.SerializerMethodField()

    class Meta:
        model = DiscountRule
        fields = ['id', 'name', 'description', 'discount_type', 'discount_value',
                  'apply_to', 'minimum_quantity', 'minimum_amount', 'maximum_uses',
                  'current_uses', 'start_date', 'end_date', 'is_active',
                  'is_valid_now', 'days_remaining', 'created_at', 'modified_at']
        read_only_fields = ['id', 'current_uses', 'is_valid_now', 'days_remaining',
                            'created_at', 'modified_at']

    def get_is_valid_now(self, obj):
        return obj.is_valid()

    def get_days_remaining(self, obj):
        if obj.end_date:
            delta = obj.end_date.date() - timezone.now().date()
            return delta.days if delta.days >= 0 else 0
        return None


class DiscountRuleCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = DiscountRule
        fields = ['name', 'description', 'discount_type', 'discount_value',
                  'apply_to', 'minimum_quantity', 'minimum_amount', 'maximum_uses',
                  'start_date', 'end_date', 'is_active']

    def validate(self, data):
        if data['start_date'] >= data['end_date']:
            raise serializers.ValidationError(
                "End date must be after start date")

        if data['discount_type'] == 'PERCENTAGE' and data['discount_value'] > 100:
            raise serializers.ValidationError(
                "Percentage discount cannot exceed 100%")

        if data['discount_value'] <= 0:
            raise serializers.ValidationError(
                "Discount value must be positive")

        return data


class ProductDiscountSerializer(serializers.ModelSerializer):
    discount_rule = DiscountRuleSerializer(read_only=True)
    product = ProductListSerializer(read_only=True)

    class Meta:
        model = ProductDiscount
        fields = ['id', 'discount_rule', 'product']


class ProductDiscountCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductDiscount
        fields = ['discount_rule', 'product']

    def validate(self, data):
        # Check if this product-discount combination already exists
        if ProductDiscount.objects.filter(
            discount_rule=data['discount_rule'],
            product=data['product']
        ).exists():
            raise serializers.ValidationError(
                "This product is already associated with this discount rule"
            )
        return data


class BulkPricingTierSerializer(serializers.ModelSerializer):
    product = ProductListSerializer(read_only=True)
    variant = ProductVariantSerializer(read_only=True)
    calculated_price = serializers.SerializerMethodField()

    class Meta:
        model = BulkPricingTier
        fields = ['id', 'product', 'variant', 'min_quantity', 'max_quantity',
                  'discount_percentage', 'fixed_price', 'calculated_price',
                  'is_active', 'created_at']
        read_only_fields = ['id', 'calculated_price', 'created_at']

    def get_calculated_price(self, obj):
        if obj.product:
            base_price = obj.product.price
            if obj.variant:
                base_price = obj.variant.final_price
            return obj.get_price(base_price)
        return None


class BulkPricingTierCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = BulkPricingTier
        fields = ['product', 'variant', 'min_quantity', 'max_quantity',
                  'discount_percentage', 'fixed_price', 'is_active']

    def validate(self, data):
        if data.get('max_quantity') and data['min_quantity'] >= data['max_quantity']:
            raise serializers.ValidationError(
                "Max quantity must be greater than min quantity")

        if not data.get('discount_percentage') and not data.get('fixed_price'):
            raise serializers.ValidationError(
                "Either discount_percentage or fixed_price must be provided")

        if data.get('discount_percentage') and data.get('fixed_price'):
            raise serializers.ValidationError(
                "Cannot have both discount_percentage and fixed_price")

        if data.get('discount_percentage') and (data['discount_percentage'] <= 0 or data['discount_percentage'] > 100):
            raise serializers.ValidationError(
                "Discount percentage must be between 0 and 100")

        if data.get('fixed_price') and data['fixed_price'] <= 0:
            raise serializers.ValidationError("Fixed price must be positive")

        return data


class ProductDiscountDetailSerializer(serializers.ModelSerializer):
    """Detailed view of product with all associated discounts and bulk pricing"""
    discounts = serializers.SerializerMethodField()
    bulk_pricing_tiers = serializers.SerializerMethodField()
    active_discounts = serializers.SerializerMethodField()

    class Meta:
        model = ProductListSerializer.Meta.model
        fields = ['id', 'name', 'slug', 'price', 'discounts',
                  'bulk_pricing_tiers', 'active_discounts']

    def get_discounts(self, obj):
        discounts = obj.discounts.select_related('discount_rule')
        return ProductDiscountSerializer(discounts, many=True).data

    def get_bulk_pricing_tiers(self, obj):
        tiers = obj.bulk_pricing.filter(
            is_active=True).order_by('min_quantity')
        return BulkPricingTierSerializer(tiers, many=True).data

    def get_active_discounts(self, obj):
        now = timezone.now()
        active_discounts = obj.discounts.filter(
            discount_rule__is_active=True,
            discount_rule__start_date__lte=now,
            discount_rule__end_date__gte=now
        ).select_related('discount_rule')
        return ProductDiscountSerializer(active_discounts, many=True).data


class DiscountUsageSerializer(serializers.Serializer):
    """Serializer for applying discounts"""
    discount_rule_id = serializers.IntegerField()
    product_id = serializers.IntegerField()
    quantity = serializers.IntegerField(min_value=1)

    def validate(self, data):
        try:
            discount_rule = DiscountRule.objects.get(
                id=data['discount_rule_id'])
        except DiscountRule.DoesNotExist:
            raise serializers.ValidationError("Discount rule not found")

        if not discount_rule.is_valid():
            raise serializers.ValidationError(
                "Discount rule is not currently valid")

        if data['quantity'] < discount_rule.minimum_quantity:
            raise serializers.ValidationError(
                f"Minimum quantity required: {discount_rule.minimum_quantity}"
            )

        return data


class BulkPricingCalculatorSerializer(serializers.Serializer):
    """Serializer for calculating bulk pricing"""
    product_id = serializers.IntegerField()
    variant_id = serializers.IntegerField(required=False)
    quantity = serializers.IntegerField(min_value=1)

    def validate(self, data):
        try:
            from product.models import Product
            product = Product.objects.get(id=data['product_id'])
        except Product.DoesNotExist:
            raise serializers.ValidationError("Product not found")

        if data.get('variant_id'):
            try:
                from product.models import ProductVariant
                variant = ProductVariant.objects.get(
                    id=data['variant_id'], product=product)
            except ProductVariant.DoesNotExist:
                raise serializers.ValidationError("Product variant not found")

        return data
