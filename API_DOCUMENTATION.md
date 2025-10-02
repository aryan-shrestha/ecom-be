# Comprehensive API Documentation

## Overview

This document outlines all the API endpoints for the enhanced ecommerce product management system with separate apps for products, inventory, and discount management.

## Base URL

```
http://localhost:8001/
```

## Authentication

Most endpoints require authentication. Use JWT tokens for authentication:

- Login: `POST /auth/jwt/create/`
- Refresh: `POST /auth/jwt/refresh/`

## API Endpoints

### 🛍️ Product Management APIs

#### Products

- **GET** `/products/` - List all products with filtering, search, and pagination

  - Query params: `category__slug`, `min_price`, `max_price`, `search`, `ordering`
  - Example: `/products/?category__slug=electronics&min_price=100&search=laptop`

- **GET** `/products/{slug}/` - Get product details with variants
- **POST** `/products/` - Create new product (Admin only)
- **PUT/PATCH** `/products/{slug}/` - Update product (Admin only)
- **DELETE** `/products/{slug}/` - Delete product (Admin only)

#### Product Custom Actions

- **GET** `/products/{slug}/variants/` - Get all variants for a product
- **POST** `/products/{slug}/add_variant/` - Add variant to product (Admin only)
- **GET** `/products/search/` - Advanced search with attribute filters
  - Query params: `attributes` (comma-separated attribute value IDs)

#### Product Attributes

- **GET** `/attributes/` - List product attributes (Color, Size, etc.)
- **GET** `/attributes/{id}/` - Get attribute details
- **POST** `/attributes/` - Create attribute (Admin only)
- **GET** `/attributes/{id}/values/` - Get all values for an attribute

#### Product Attribute Values

- **GET** `/attribute-values/` - List attribute values
- **GET** `/attribute-values/{id}/` - Get attribute value details
- **POST** `/attribute-values/` - Create attribute value (Admin only)
- **Filter**: `?attribute={attribute_id}`

#### Product Variants

- **GET** `/variants/` - List product variants
- **GET** `/variants/{id}/` - Get variant details
- **POST** `/variants/` - Create variant (Admin only)
- **POST** `/variants/{id}/update_attributes/` - Update variant attributes
- **GET** `/variants/by_attributes/` - Find variants by attribute combination
  - Query params: `attributes` (comma-separated attribute value IDs)

### 📦 Inventory Management APIs

#### Warehouses

- **GET** `/inventory/warehouses/` - List all warehouses
- **GET** `/inventory/warehouses/{id}/` - Get warehouse details
- **POST** `/inventory/warehouses/` - Create warehouse (Admin only)
- **GET** `/inventory/warehouses/active/` - Get only active warehouses

#### Warehouse Custom Actions

- **GET** `/inventory/warehouses/{id}/inventory/` - Get warehouse inventory
  - Query params: `low_stock=true` - Filter low stock items
- **GET** `/inventory/warehouses/{id}/overview/` - Get warehouse statistics

#### Product Inventory

- **GET** `/inventory/inventory/` - List inventory across all warehouses
- **GET** `/inventory/inventory/{id}/` - Get detailed inventory with transactions
- **POST** `/inventory/inventory/` - Create inventory record (Admin only)
- **PUT/PATCH** `/inventory/inventory/{id}/` - Update inventory (Admin only)

#### Inventory Custom Actions

- **GET** `/inventory/inventory/low_stock/` - Get low stock items across all warehouses
- **GET** `/inventory/inventory/out_of_stock/` - Get out of stock items
- **POST** `/inventory/inventory/{id}/reserve_stock/` - Reserve stock for order
  ```json
  {
    "quantity": 5,
    "reference_number": "ORDER-123",
    "created_by": "user123"
  }
  ```
- **POST** `/inventory/inventory/{id}/release_stock/` - Release reserved stock

#### Inventory Transactions

- **GET** `/inventory/transactions/` - List all inventory transactions (Read-only)
- **GET** `/inventory/transactions/{id}/` - Get transaction details
- **POST** `/inventory/transactions/create/` - Create new transaction
  ```json
  {
    "inventory": 1,
    "transaction_type": "IN",
    "quantity": 100,
    "reference_number": "PO-456",
    "notes": "New stock arrival",
    "created_by": "admin"
  }
  ```

#### Transaction Custom Actions

- **GET** `/inventory/transactions/recent/` - Get transactions from last 7 days

### 💰 Discount Management APIs

#### Discount Rules

- **GET** `/discounts/rules/` - List all discount rules
- **GET** `/discounts/rules/{id}/` - Get discount rule details
- **POST** `/discounts/rules/` - Create discount rule (Admin only)
  ```json
  {
    "name": "Summer Sale",
    "description": "20% off summer items",
    "discount_type": "PERCENTAGE",
    "discount_value": 20.0,
    "apply_to": "CATEGORY",
    "minimum_quantity": 1,
    "minimum_amount": 50.0,
    "start_date": "2025-06-01T00:00:00Z",
    "end_date": "2025-08-31T23:59:59Z",
    "is_active": true
  }
  ```

#### Discount Custom Actions

- **GET** `/discounts/rules/active/` - Get currently active discounts
- **GET** `/discounts/rules/expiring_soon/` - Get discounts expiring in 7 days
- **POST** `/discounts/rules/{id}/apply_to_products/` - Apply discount to products
  ```json
  {
    "product_ids": [1, 2, 3, 4]
  }
  ```
- **POST** `/discounts/rules/{id}/increment_usage/` - Increment usage count

#### Product Discounts

- **GET** `/discounts/product-discounts/` - List product-specific discounts
- **POST** `/discounts/product-discounts/` - Link product to discount rule
- **GET** `/discounts/product-discounts/by_product/?product_id=1` - Get discounts for product

#### Product Discount Custom Actions

- **POST** `/discounts/product-discounts/calculate_discount/` - Calculate discount amount
  ```json
  {
    "discount_rule_id": 1,
    "product_id": 1,
    "quantity": 3
  }
  ```

#### Bulk Pricing Tiers

- **GET** `/discounts/bulk-pricing/` - List bulk pricing tiers
- **GET** `/discounts/bulk-pricing/{id}/` - Get bulk pricing details
- **POST** `/discounts/bulk-pricing/` - Create bulk pricing tier (Admin only)
  ```json
  {
    "product": 1,
    "variant": null,
    "min_quantity": 10,
    "max_quantity": 50,
    "discount_percentage": 15.0,
    "is_active": true
  }
  ```

#### Bulk Pricing Custom Actions

- **GET** `/discounts/bulk-pricing/by_product/?product_id=1&variant_id=2` - Get tiers for product
- **POST** `/discounts/bulk-pricing/calculate_bulk_price/` - Calculate bulk price
  ```json
  {
    "product_id": 1,
    "variant_id": 2,
    "quantity": 25
  }
  ```

## Response Formats

### Standard List Response

```json
{
  "count": 100,
  "next": "http://localhost:8001/products/?page=2",
  "previous": null,
  "results": [...]
}
```

### Product Detail Response

```json
{
  "id": 1,
  "name": "Premium Laptop",
  "slug": "premium-laptop",
  "description": "High-performance laptop...",
  "category": {
    "id": 1,
    "name": "Electronics",
    "slug": "electronics"
  },
  "price": 1299.99,
  "images": ["url1.jpg", "url2.jpg"],
  "variants": [
    {
      "id": 1,
      "sku": "LAP-001-RED-16GB",
      "name": "Red 16GB",
      "price_adjustment": 200.0,
      "final_price": 1499.99,
      "attributes": [
        {
          "attribute_value": {
            "id": 1,
            "value": "Red",
            "attribute": {
              "name": "Color"
            }
          }
        }
      ]
    }
  ]
}
```

### Inventory Response

```json
{
  "id": 1,
  "product": {...},
  "variant": {...},
  "warehouse": {...},
  "quantity_available": 50,
  "quantity_reserved": 5,
  "quantity_sold": 100,
  "quantity_on_hand": 55,
  "needs_reorder": false,
  "reorder_level": 10,
  "reorder_quantity": 100
}
```

## Error Responses

```json
{
  "error": "Error message",
  "details": {...}
}
```

## Common Query Parameters

- `page` - Page number for pagination
- `page_size` - Items per page (default: 20)
- `search` - Text search across searchable fields
- `ordering` - Sort by field (prefix with `-` for descending)
- Various filter parameters specific to each endpoint

## Status Codes

- `200` - Success
- `201` - Created
- `400` - Bad Request
- `401` - Unauthorized
- `403` - Forbidden
- `404` - Not Found
- `500` - Internal Server Error
