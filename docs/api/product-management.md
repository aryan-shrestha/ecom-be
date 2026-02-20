# Product Management API Documentation

## 1. Overview

### Base Configuration

- **Base URL**: `http://localhost:8000/api`
- **Content-Type**: `application/json`
- **API Version**: None (unversioned)
- **Protocol**: REST over HTTP/HTTPS

### Authentication Summary

All admin endpoints require JWT-based authentication. Storefront endpoints are publicly accessible.

To obtain an access token:

1. Register via `POST /api/auth/register`
2. Login via `POST /api/auth/login` to receive an access token
3. Include the token in the `Authorization` header for subsequent requests

### Standard Response Format

This API uses direct JSON responses without additional envelope wrapping. Success responses return the documented schema directly. Error responses follow this structure:

```json
{
  "detail": "Error message description"
}
```

### Common HTTP Status Codes

- **200 OK**: Successful GET/PATCH/POST operation
- **201 Created**: Successful resource creation
- **204 No Content**: Successful deletion
- **400 Bad Request**: Validation error or business rule violation
- **401 Unauthorized**: Missing or invalid authentication token
- **403 Forbidden**: Insufficient permissions
- **404 Not Found**: Resource does not exist
- **409 Conflict**: Duplicate resource (slug/SKU already exists)
- **422 Unprocessable Entity**: Request body validation failed
- **500 Internal Server Error**: Unexpected server error

### Correlation & Request Tracking

No correlation ID headers are currently implemented in this API version.

### Idempotency

No idempotency headers are currently supported.

### Image Upload Configuration

The API supports direct image file uploads to cloud storage (Cloudinary) or local storage.

**Environment Variables**:
| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `CLOUDINARY_URL` | No | None | Cloudinary connection URL (format: `cloudinary://API_KEY:API_SECRET@CLOUD_NAME`). If not set, falls back to local file storage. |
| `CLOUDINARY_FOLDER_PREFIX` | No | `ecom/dev` | Folder prefix for organizing images in Cloudinary |
| `MAX_IMAGE_BYTES` | No | `5242880` | Maximum image file size in bytes (default: 5MB) |
| `ALLOWED_IMAGE_MIME_TYPES` | No | `image/jpeg,image/png,image/webp` | Comma-separated list of allowed MIME types |

**Supported Image Formats**: JPEG, PNG, WebP

**Image Storage Locations**:

- Product images: `{prefix}/products/{product_id}/`
- Variant images: `{prefix}/variants/{variant_id}/`

**Local Storage Fallback**:
If `CLOUDINARY_URL` is not configured, images are saved to `./storage/uploads` and served from `/storage/uploads`. This is suitable for development but not recommended for production.

---

## 2. Authentication & Authorization

### Authentication Mechanism

**Method**: Bearer JWT (JSON Web Token)

**Header Format**:

```
Authorization: Bearer <access_token>
```

**Token Details**:

- **Algorithm**: RS256 (RSA with SHA-256)
- **Lifetime**: 10 minutes (configurable via `JWT_ACCESS_TOKEN_TTL_MINUTES`)
- **Issuer**: `ecom-auth-service`
- **Audience**: `ecom-api`

**Token Claims**:

- `sub`: User ID (UUID)
- `roles`: Array of role names assigned to user
- `ver`: Token version (used for token invalidation)
- `iat`: Issued at timestamp
- `exp`: Expiration timestamp

### Authorization (RBAC)

The API enforces Role-Based Access Control (RBAC) using permission codes. Each admin endpoint requires specific permissions assigned to the authenticated user's roles.

### Permission Codes

| Endpoint Pattern                                       | Required Permission      | Description                   |
| ------------------------------------------------------ | ------------------------ | ----------------------------- |
| `POST /admin/products`                                 | `products:write`         | Create products               |
| `GET /admin/products`                                  | `products:read`          | List/view products            |
| `GET /admin/products/{id}`                             | `products:read`          | Get product details           |
| `PATCH /admin/products/{id}`                           | `products:write`         | Update product metadata       |
| `POST /admin/products/{id}/publish`                    | `products:publish`       | Publish product to storefront |
| `POST /admin/products/{id}/archive`                    | `products:archive`       | Archive product               |
| `POST /admin/products/{id}/variants`                   | `products:variant_write` | Create variant                |
| `PATCH /admin/products/variants/{id}`                  | `products:variant_write` | Update variant                |
| `POST /admin/products/variants/{id}/deactivate`        | `products:variant_write` | Deactivate variant            |
| `POST /admin/products/variants/{id}/stock-adjustments` | `inventory:adjust`       | Adjust inventory              |
| `POST /admin/products/{id}/images`                     | `products:media_write`   | Add product image (URL)       |
| `POST /admin/products/{id}/images/upload`              | `products:media_write`   | Upload product image file     |
| `POST /admin/products/variants/{id}/images/upload`     | `products:media_write`   | Upload variant image file     |
| `DELETE /admin/products/{id}/images/{image_id}`        | `products:media_write`   | Remove product image          |
| `POST /admin/products/{id}/images/reorder`             | `products:media_write`   | Reorder product images        |
| `POST /admin/products/{id}/categories`                 | `categories:write`       | Assign categories             |
| `POST /admin/categories`                               | `categories:write`       | Create category               |
| `GET /admin/categories`                                | `categories:read`        | List categories               |
| `GET /store/products`                                  | None (public)            | List published products       |
| `GET /store/products/{slug}`                           | None (public)            | Get published product         |

**Default Admin User** (from seed data):

- Email: `admin@example.com`
- Password: `Admin123!`
- Has all product management permissions

---

## 3. Data Models

### MoneySchema

Monetary amounts are represented in **minor units** (cents for USD) to avoid floating-point precision issues.

| Field      | Type    | Required | Constraints | Description                        | Example           |
| ---------- | ------- | -------- | ----------- | ---------------------------------- | ----------------- |
| `amount`   | integer | Yes      | N/A         | Amount in minor units (cents)      | `1999` (= $19.99) |
| `currency` | string  | Yes      | Length: 3   | ISO 4217 currency code (uppercase) | `"USD"`           |

**Example**:

```json
{
  "amount": 2999,
  "currency": "USD"
}
```

### ProductResponseSchema

| Field               | Type          | Required | Description                                      | Example                                  |
| ------------------- | ------------- | -------- | ------------------------------------------------ | ---------------------------------------- |
| `id`                | UUID          | Yes      | Product identifier                               | `"550e8400-e29b-41d4-a716-446655440000"` |
| `status`            | string        | Yes      | Product status: `DRAFT`, `PUBLISHED`, `ARCHIVED` | `"DRAFT"`                                |
| `name`              | string        | Yes      | Product name (1-255 chars)                       | `"Wireless Bluetooth Headphones"`        |
| `slug`              | string        | Yes      | URL-safe slug (1-200 chars)                      | `"wireless-bluetooth-headphones"`        |
| `description_short` | string        | No       | Short description (max 500 chars)                | `"Premium noise-cancelling headphones"`  |
| `description_long`  | string        | No       | Full description (unlimited)                     | `"Experience crystal-clear audio..."`    |
| `tags`              | array[string] | Yes      | Product tags                                     | `["electronics", "audio", "wireless"]`   |
| `featured`          | boolean       | Yes      | Featured flag                                    | `false`                                  |
| `sort_order`        | integer       | Yes      | Display order (>= 0)                             | `0`                                      |
| `created_at`        | datetime      | Yes      | ISO 8601 timestamp                               | `"2024-01-15T10:30:00Z"`                 |
| `updated_at`        | datetime      | Yes      | ISO 8601 timestamp                               | `"2024-01-15T10:30:00Z"`                 |
| `created_by`        | UUID          | No       | User ID who created                              | `"450e8400-e29b-41d4-a716-446655440000"` |
| `updated_by`        | UUID          | No       | User ID who last updated                         | `"450e8400-e29b-41d4-a716-446655440000"` |

### VariantResponseSchema

| Field              | Type        | Required | Description                              | Example                                  |
| ------------------ | ----------- | -------- | ---------------------------------------- | ---------------------------------------- |
| `id`               | UUID        | Yes      | Variant identifier                       | `"660e8400-e29b-41d4-a716-446655440000"` |
| `product_id`       | UUID        | Yes      | Parent product ID                        | `"550e8400-e29b-41d4-a716-446655440000"` |
| `sku`              | string      | Yes      | Stock Keeping Unit (unique, 1-100 chars) | `"WBH-BLK-2024"`                         |
| `barcode`          | string      | No       | Product barcode (max 100 chars)          | `"1234567890123"`                        |
| `status`           | string      | Yes      | Variant status: `ACTIVE`, `INACTIVE`     | `"ACTIVE"`                               |
| `price`            | MoneySchema | Yes      | Selling price                            | `{"amount": 7999, "currency": "USD"}`    |
| `compare_at_price` | MoneySchema | No       | Original price (for discounts)           | `{"amount": 9999, "currency": "USD"}`    |
| `cost`             | MoneySchema | No       | Cost basis (admin only)                  | `{"amount": 4500, "currency": "USD"}`    |
| `weight`           | integer     | No       | Weight in grams                          | `250`                                    |
| `length`           | integer     | No       | Length in millimeters                    | `200`                                    |
| `width`            | integer     | No       | Width in millimeters                     | `180`                                    |
| `height`           | integer     | No       | Height in millimeters                    | `85`                                     |
| `is_default`       | boolean     | Yes      | Default variant flag                     | `true`                                   |
| `created_at`       | datetime    | Yes      | ISO 8601 timestamp                       | `"2024-01-15T10:30:00Z"`                 |
| `updated_at`       | datetime    | Yes      | ISO 8601 timestamp                       | `"2024-01-15T10:30:00Z"`                 |

### InventoryResponseSchema

| Field             | Type    | Required | Description                                    | Example                                  |
| ----------------- | ------- | -------- | ---------------------------------------------- | ---------------------------------------- |
| `variant_id`      | UUID    | Yes      | Variant identifier                             | `"660e8400-e29b-41d4-a716-446655440000"` |
| `on_hand`         | integer | Yes      | Physical stock quantity                        | `100`                                    |
| `reserved`        | integer | Yes      | Reserved (pending orders)                      | `5`                                      |
| `allow_backorder` | boolean | Yes      | Allow negative stock                           | `false`                                  |
| `available`       | integer | Yes      | Available stock (computed: on_hand - reserved) | `95`                                     |

### CategoryResponseSchema

| Field       | Type   | Required | Description                         | Example                                  |
| ----------- | ------ | -------- | ----------------------------------- | ---------------------------------------- |
| `id`        | UUID   | Yes      | Category identifier                 | `"770e8400-e29b-41d4-a716-446655440000"` |
| `name`      | string | Yes      | Category name (1-100 chars)         | `"Electronics"`                          |
| `slug`      | string | Yes      | URL-safe slug (unique, 1-200 chars) | `"electronics"`                          |
| `parent_id` | UUID   | No       | Parent category ID (for hierarchy)  | `null`                                   |

### ProductImageResponseSchema

| Field                | Type     | Required | Description                                    | Example                                       |
| -------------------- | -------- | -------- | ---------------------------------------------- | --------------------------------------------- |
| `id`                 | UUID     | Yes      | Image identifier                               | `"880e8400-e29b-41d4-a716-446655440000"`      |
| `product_id`         | UUID     | Yes      | Parent product ID                              | `"550e8400-e29b-41d4-a716-446655440000"`      |
| `url`                | string   | Yes      | Image URL (1-1000 chars)                       | `"https://cdn.example.com/img/product-1.jpg"` |
| `alt_text`           | string   | No       | Accessibility text (max 255 chars)             | `"Wireless headphones in black"`              |
| `position`           | integer  | Yes      | Display order (0-based)                        | `0`                                           |
| `created_at`         | datetime | Yes      | ISO 8601 timestamp                             | `"2024-01-15T10:30:00Z"`                      |
| `provider`           | string   | No       | Storage provider (e.g., "cloudinary", "local") | `"cloudinary"`                                |
| `provider_public_id` | string   | No       | Provider-specific public identifier            | `"ecom/dev/products/uuid/image.jpg"`          |
| `bytes_size`         | integer  | No       | File size in bytes                             | `123456`                                      |
| `width`              | integer  | No       | Image width in pixels                          | `1920`                                        |
| `height`             | integer  | No       | Image height in pixels                         | `1080`                                        |
| `format`             | string   | No       | Image format (e.g., "jpg", "png", "webp")      | `"jpg"`                                       |

### VariantImageResponseSchema

| Field                | Type     | Required | Description                                    | Example                                          |
| -------------------- | -------- | -------- | ---------------------------------------------- | ------------------------------------------------ |
| `id`                 | UUID     | Yes      | Image identifier                               | `"990e8400-e29b-41d4-a716-446655440000"`         |
| `variant_id`         | UUID     | Yes      | Parent variant ID                              | `"660e8400-e29b-41d4-a716-446655440000"`         |
| `url`                | string   | Yes      | Image URL (1-1000 chars)                       | `"https://res.cloudinary.com/img/variant-1.jpg"` |
| `alt_text`           | string   | No       | Accessibility text (max 255 chars)             | `"Black variant front view"`                     |
| `position`           | integer  | Yes      | Display order (0-based)                        | `0`                                              |
| `created_at`         | datetime | Yes      | ISO 8601 timestamp                             | `"2024-01-15T10:30:00Z"`                         |
| `provider`           | string   | No       | Storage provider (e.g., "cloudinary", "local") | `"cloudinary"`                                   |
| `provider_public_id` | string   | No       | Provider-specific public identifier            | `"ecom/dev/variants/uuid/image.jpg"`             |
| `bytes_size`         | integer  | No       | File size in bytes                             | `98765`                                          |
| `width`              | integer  | No       | Image width in pixels                          | `1024`                                           |
| `height`             | integer  | No       | Image height in pixels                         | `768`                                            |
| `format`             | string   | No       | Image format (e.g., "jpg", "png", "webp")      | `"jpg"`                                          |

### StockMovementResponseSchema

| Field        | Type     | Required | Description                                    | Example                                  |
| ------------ | -------- | -------- | ---------------------------------------------- | ---------------------------------------- |
| `id`         | UUID     | Yes      | Movement record identifier                     | `"990e8400-e29b-41d4-a716-446655440000"` |
| `variant_id` | UUID     | Yes      | Variant identifier                             | `"660e8400-e29b-41d4-a716-446655440000"` |
| `delta`      | integer  | Yes      | Stock change (positive=add, negative=subtract) | `50`                                     |
| `reason`     | string   | Yes      | Adjustment reason (1-100 chars)                | `"purchase_order"`                       |
| `note`       | string   | No       | Additional notes (max 500 chars)               | `"PO #12345 received"`                   |
| `created_at` | datetime | Yes      | ISO 8601 timestamp                             | `"2024-01-15T10:30:00Z"`                 |
| `created_by` | UUID     | No       | User ID who adjusted                           | `"450e8400-e29b-41d4-a716-446655440000"` |

### Product Status Values

| Status      | Description                                         |
| ----------- | --------------------------------------------------- |
| `DRAFT`     | Product is being prepared, not visible to customers |
| `PUBLISHED` | Product is live and visible on storefront           |
| `ARCHIVED`  | Product is archived, removed from storefront        |

### Variant Status Values

| Status     | Description                                 |
| ---------- | ------------------------------------------- |
| `ACTIVE`   | Variant is active and can be purchased      |
| `INACTIVE` | Variant is inactive, hidden from storefront |

---

## 4. Endpoints

### 4.1 Admin Product Endpoints

#### Create Product

Create a new product in DRAFT status.

- **Method**: `POST`
- **Path**: `/api/admin/products`
- **Authentication**: Required
- **Authorization**: `products:write`
- **Headers**:
  - `Authorization: Bearer <token>` (required)
  - `Content-Type: application/json` (required)

**Request Body** (`CreateProductRequestSchema`):

```json
{
  "name": "Wireless Bluetooth Headphones",
  "slug": "wireless-bluetooth-headphones",
  "description_short": "Premium noise-cancelling headphones with 30-hour battery",
  "description_long": "Experience crystal-clear audio with our premium wireless headphones...",
  "tags": ["electronics", "audio", "wireless"],
  "featured": false,
  "sort_order": 0
}
```

**Success Response** (201 Created):

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "DRAFT",
  "name": "Wireless Bluetooth Headphones",
  "slug": "wireless-bluetooth-headphones",
  "description_short": "Premium noise-cancelling headphones with 30-hour battery",
  "description_long": "Experience crystal-clear audio with our premium wireless headphones...",
  "tags": ["electronics", "audio", "wireless"],
  "featured": false,
  "sort_order": 0,
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z",
  "created_by": "450e8400-e29b-41d4-a716-446655440000",
  "updated_by": "450e8400-e29b-41d4-a716-446655440000"
}
```

**Error Response** (409 Conflict - duplicate slug):

```json
{
  "detail": "Product with slug 'wireless-bluetooth-headphones' already exists"
}
```

**Error Response** (401 Unauthorized):

```json
{
  "detail": "Missing or invalid authorization header"
}
```

**Error Response** (403 Forbidden):

```json
{
  "detail": "Permission denied: products:write"
}
```

**Error Response** (400 Bad Request - validation):

```json
{
  "detail": "Product name cannot be empty"
}
```

**cURL Example**:

```bash
curl -X POST http://localhost:8000/api/admin/products \
  -H "Authorization: Bearer eyJhbGc..." \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Wireless Bluetooth Headphones",
    "slug": "wireless-bluetooth-headphones",
    "description_short": "Premium noise-cancelling headphones",
    "tags": ["electronics", "audio"],
    "featured": false
  }'
```

---

#### List Products (Admin)

List all products with filtering and pagination. Returns products in any status (DRAFT, PUBLISHED, ARCHIVED).

- **Method**: `GET`
- **Path**: `/api/admin/products`
- **Authentication**: Required
- **Authorization**: `products:read`
- **Headers**:
  - `Authorization: Bearer <token>` (required)

**Query Parameters**:
| Parameter | Type | Default | Constraints | Description |
|-----------|------|---------|-------------|-------------|
| `offset` | integer | 0 | >= 0 | Number of items to skip |
| `limit` | integer | 20 | 1-100 | Number of items to return |
| `status` | string | None | `DRAFT`, `PUBLISHED`, `ARCHIVED` | Filter by product status |
| `category_id` | UUID | None | Valid UUID | Filter by category |
| `tag` | string | None | N/A | Filter by tag (exact match) |
| `featured` | boolean | None | true/false | Filter by featured flag |
| `sort_by` | string | `created_at` | `created_at`, `sort_order` | Sort field |
| `sort_desc` | boolean | true | true/false | Sort descending if true |

**Success Response** (200 OK):

```json
{
  "products": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "status": "PUBLISHED",
      "name": "Wireless Bluetooth Headphones",
      "slug": "wireless-bluetooth-headphones",
      "description_short": "Premium noise-cancelling headphones",
      "description_long": null,
      "tags": ["electronics", "audio"],
      "featured": true,
      "sort_order": 10,
      "created_at": "2024-01-15T10:30:00Z",
      "updated_at": "2024-01-16T14:20:00Z",
      "created_by": "450e8400-e29b-41d4-a716-446655440000",
      "updated_by": "450e8400-e29b-41d4-a716-446655440000"
    }
  ],
  "total": 1,
  "offset": 0,
  "limit": 20
}
```

**Error Response** (401 Unauthorized):

```json
{
  "detail": "Token has expired"
}
```

**Error Response** (403 Forbidden):

```json
{
  "detail": "Permission denied: products:read"
}
```

**cURL Examples**:

List all products:

```bash
curl -X GET "http://localhost:8000/api/admin/products" \
  -H "Authorization: Bearer eyJhbGc..."
```

Filter by status and tag:

```bash
curl -X GET "http://localhost:8000/api/admin/products?status=PUBLISHED&tag=electronics" \
  -H "Authorization: Bearer eyJhbGc..."
```

Pagination example:

```bash
curl -X GET "http://localhost:8000/api/admin/products?offset=20&limit=10" \
  -H "Authorization: Bearer eyJhbGc..."
```

---

#### Get Product Detail (Admin)

Get detailed product information including variants, images, categories, and inventory data.

- **Method**: `GET`
- **Path**: `/api/admin/products/{product_id}`
- **Authentication**: Required
- **Authorization**: `products:read`
- **Headers**:
  - `Authorization: Bearer <token>` (required)

**Path Parameters**:
| Parameter | Type | Description |
|-----------|------|-------------|
| `product_id` | UUID | Product identifier |

**Success Response** (200 OK):

```json
{
  "product": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "status": "PUBLISHED",
    "name": "Wireless Bluetooth Headphones",
    "slug": "wireless-bluetooth-headphones",
    "description_short": "Premium noise-cancelling headphones",
    "description_long": "Experience crystal-clear audio...",
    "tags": ["electronics", "audio"],
    "featured": true,
    "sort_order": 10,
    "created_at": "2024-01-15T10:30:00Z",
    "updated_at": "2024-01-16T14:20:00Z",
    "created_by": "450e8400-e29b-41d4-a716-446655440000",
    "updated_by": "450e8400-e29b-41d4-a716-446655440000"
  },
  "variants": [
    {
      "id": "660e8400-e29b-41d4-a716-446655440000",
      "product_id": "550e8400-e29b-41d4-a716-446655440000",
      "sku": "WBH-BLK-2024",
      "barcode": "1234567890123",
      "status": "ACTIVE",
      "price": {
        "amount": 7999,
        "currency": "USD"
      },
      "compare_at_price": {
        "amount": 9999,
        "currency": "USD"
      },
      "cost": {
        "amount": 4500,
        "currency": "USD"
      },
      "weight": 250,
      "length": 200,
      "width": 180,
      "height": 85,
      "is_default": true,
      "created_at": "2024-01-15T10:35:00Z",
      "updated_at": "2024-01-15T10:35:00Z"
    }
  ],
  "images": [
    {
      "id": "880e8400-e29b-41d4-a716-446655440000",
      "product_id": "550e8400-e29b-41d4-a716-446655440000",
      "url": "https://cdn.example.com/products/headphones-1.jpg",
      "alt_text": "Wireless headphones front view",
      "position": 0,
      "created_at": "2024-01-15T10:40:00Z",
      "provider": "cloudinary",
      "provider_public_id": "ecom/dev/products/550e8400-e29b-41d4-a716-446655440000/headphones-1",
      "bytes_size": 145678,
      "width": 2048,
      "height": 1536,
      "format": "jpg"
    }
  ],
  "categories": [
    {
      "id": "770e8400-e29b-41d4-a716-446655440000",
      "name": "Electronics",
      "slug": "electronics",
      "parent_id": null
    }
  ],
  "inventory": {
    "660e8400-e29b-41d4-a716-446655440000": {
      "variant_id": "660e8400-e29b-41d4-a716-446655440000",
      "on_hand": 100,
      "reserved": 5,
      "allow_backorder": false,
      "available": 95
    }
  }
}
```

**Error Response** (404 Not Found):

```json
{
  "detail": "Product 550e8400-e29b-41d4-a716-446655440000 not found"
}
```

**cURL Example**:

```bash
curl -X GET "http://localhost:8000/api/admin/products/550e8400-e29b-41d4-a716-446655440000" \
  -H "Authorization: Bearer eyJhbGc..."
```

---

#### Update Product

Update product metadata. Product slug cannot be changed after creation.

- **Method**: `PATCH`
- **Path**: `/api/admin/products/{product_id}`
- **Authentication**: Required
- **Authorization**: `products:write`
- **Headers**:
  - `Authorization: Bearer <token>` (required)
  - `Content-Type: application/json` (required)

**Path Parameters**:
| Parameter | Type | Description |
|-----------|------|-------------|
| `product_id` | UUID | Product identifier |

**Request Body** (`UpdateProductRequestSchema`):

```json
{
  "name": "Premium Wireless Headphones",
  "description_short": "Updated description",
  "description_long": "Full updated description...",
  "tags": ["electronics", "audio", "premium"],
  "featured": true,
  "sort_order": 5
}
```

**Success Response** (200 OK):

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "DRAFT",
  "name": "Premium Wireless Headphones",
  "slug": "wireless-bluetooth-headphones",
  "description_short": "Updated description",
  "description_long": "Full updated description...",
  "tags": ["electronics", "audio", "premium"],
  "featured": true,
  "sort_order": 5,
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-16T15:45:00Z",
  "created_by": "450e8400-e29b-41d4-a716-446655440000",
  "updated_by": "450e8400-e29b-41d4-a716-446655440000"
}
```

**Error Response** (404 Not Found):

```json
{
  "detail": "Product 550e8400-e29b-41d4-a716-446655440000 not found"
}
```

**cURL Example**:

```bash
curl -X PATCH "http://localhost:8000/api/admin/products/550e8400-e29b-41d4-a716-446655440000" \
  -H "Authorization: Bearer eyJhbGc..." \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Premium Wireless Headphones",
    "description_short": "Updated description",
    "tags": ["electronics", "premium"],
    "featured": true,
    "sort_order": 5
  }'
```

---

#### Publish Product

Publish a product to make it visible on the storefront. The product must pass business validation rules:

- Must have a name and slug
- Must have at least one ACTIVE variant
- All ACTIVE variants must have valid price and SKU

- **Method**: `POST`
- **Path**: `/api/admin/products/{product_id}/publish`
- **Authentication**: Required
- **Authorization**: `products:publish`
- **Headers**:
  - `Authorization: Bearer <token>` (required)

**Path Parameters**:
| Parameter | Type | Description |
|-----------|------|-------------|
| `product_id` | UUID | Product identifier |

**Success Response** (200 OK):

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "PUBLISHED",
  "name": "Wireless Bluetooth Headphones",
  "slug": "wireless-bluetooth-headphones",
  "description_short": "Premium noise-cancelling headphones",
  "description_long": null,
  "tags": ["electronics", "audio"],
  "featured": false,
  "sort_order": 0,
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-16T16:00:00Z",
  "created_by": "450e8400-e29b-41d4-a716-446655440000",
  "updated_by": "450e8400-e29b-41d4-a716-446655440000"
}
```

**Error Response** (400 Bad Request - validation failed):

```json
{
  "detail": "Cannot publish product: Product must have at least one active variant"
}
```

**Error Response** (404 Not Found):

```json
{
  "detail": "Product 550e8400-e29b-41d4-a716-446655440000 not found"
}
```

**Notes**:

- Publishing invalidates cache keys: `product:{id}`, `product:slug:{slug}`, and all `products:storefront:*` patterns
- Audit event `product.published` is logged

**cURL Example**:

```bash
curl -X POST "http://localhost:8000/api/admin/products/550e8400-e29b-41d4-a716-446655440000/publish" \
  -H "Authorization: Bearer eyJhbGc..."
```

---

#### Archive Product

Archive a product to remove it from the storefront. Archived products are hidden but not deleted.

- **Method**: `POST`
- **Path**: `/api/admin/products/{product_id}/archive`
- **Authentication**: Required
- **Authorization**: `products:archive`
- **Headers**:
  - `Authorization: Bearer <token>` (required)

**Path Parameters**:
| Parameter | Type | Description |
|-----------|------|-------------|
| `product_id` | UUID | Product identifier |

**Success Response** (200 OK):

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "ARCHIVED",
  "name": "Wireless Bluetooth Headphones",
  "slug": "wireless-bluetooth-headphones",
  "description_short": "Premium noise-cancelling headphones",
  "description_long": null,
  "tags": ["electronics", "audio"],
  "featured": false,
  "sort_order": 0,
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-16T16:30:00Z",
  "created_by": "450e8400-e29b-41d4-a716-446655440000",
  "updated_by": "450e8400-e29b-41d4-a716-446655440000"
}
```

**Error Response** (404 Not Found):

```json
{
  "detail": "Product 550e8400-e29b-41d4-a716-446655440000 not found"
}
```

**Notes**:

- Archiving invalidates cache keys similar to publishing

**cURL Example**:

```bash
curl -X POST "http://localhost:8000/api/admin/products/550e8400-e29b-41d4-a716-446655440000/archive" \
  -H "Authorization: Bearer eyJhbGc..."
```

---

### 4.2 Admin Variant Endpoints

#### Add Variant to Product

Create a new variant for a product. Each variant represents a specific SKU with its own pricing and inventory.

- **Method**: `POST`
- **Path**: `/api/admin/products/{product_id}/variants`
- **Authentication**: Required
- **Authorization**: `products:variant_write`
- **Headers**:
  - `Authorization: Bearer <token>` (required)
  - `Content-Type: application/json` (required)

**Path Parameters**:
| Parameter | Type | Description |
|-----------|------|-------------|
| `product_id` | UUID | Product identifier |

**Request Body** (`CreateVariantRequestSchema`):

```json
{
  "sku": "WBH-BLK-2024",
  "barcode": "1234567890123",
  "price_amount": 7999,
  "price_currency": "USD",
  "compare_at_price_amount": 9999,
  "compare_at_price_currency": "USD",
  "cost_amount": 4500,
  "cost_currency": "USD",
  "weight": 250,
  "length": 200,
  "width": 180,
  "height": 85,
  "is_default": true,
  "initial_stock": 100,
  "allow_backorder": false
}
```

**Field Notes**:

- `sku`: Must be unique across all variants
- `price_amount`: Required, must be > 0 (in cents/minor units)
- `compare_at_price_amount`: Optional, for displaying discounts
- `cost_amount`: Optional, internal cost tracking
- Dimensions in grams (weight) and millimeters (length/width/height)
- `initial_stock`: Sets initial inventory quantity

**Success Response** (201 Created):

```json
{
  "id": "660e8400-e29b-41d4-a716-446655440000",
  "product_id": "550e8400-e29b-41d4-a716-446655440000",
  "sku": "WBH-BLK-2024",
  "barcode": "1234567890123",
  "status": "ACTIVE",
  "price": {
    "amount": 7999,
    "currency": "USD"
  },
  "compare_at_price": {
    "amount": 9999,
    "currency": "USD"
  },
  "cost": {
    "amount": 4500,
    "currency": "USD"
  },
  "weight": 250,
  "length": 200,
  "width": 180,
  "height": 85,
  "is_default": true,
  "created_at": "2024-01-15T11:00:00Z",
  "updated_at": "2024-01-15T11:00:00Z"
}
```

**Error Response** (409 Conflict - duplicate SKU):

```json
{
  "detail": "Variant with SKU 'WBH-BLK-2024' already exists"
}
```

**Error Response** (404 Not Found):

```json
{
  "detail": "Product 550e8400-e29b-41d4-a716-446655440000 not found"
}
```

**cURL Example**:

```bash
curl -X POST "http://localhost:8000/api/admin/products/550e8400-e29b-41d4-a716-446655440000/variants" \
  -H "Authorization: Bearer eyJhbGc..." \
  -H "Content-Type: application/json" \
  -d '{
    "sku": "WBH-BLK-2024",
    "price_amount": 7999,
    "price_currency": "USD",
    "is_default": true,
    "initial_stock": 100
  }'
```

---

#### Update Variant

Update variant details including pricing, status, and dimensions.

- **Method**: `PATCH`
- **Path**: `/api/admin/products/variants/{variant_id}`
- **Authentication**: Required
- **Authorization**: `products:variant_write`
- **Headers**:
  - `Authorization: Bearer <token>` (required)
  - `Content-Type: application/json` (required)

**Path Parameters**:
| Parameter | Type | Description |
|-----------|------|-------------|
| `variant_id` | UUID | Variant identifier |

**Request Body** (`UpdateVariantRequestSchema`):

```json
{
  "barcode": "1234567890123",
  "status": "ACTIVE",
  "price_amount": 6999,
  "price_currency": "USD",
  "compare_at_price_amount": 9999,
  "compare_at_price_currency": "USD",
  "cost_amount": 4000,
  "cost_currency": "USD",
  "weight": 240,
  "length": 200,
  "width": 180,
  "height": 85
}
```

**Field Notes**:

- `status`: Must be either `ACTIVE` or `INACTIVE`
- SKU cannot be changed after creation

**Success Response** (200 OK):

```json
{
  "id": "660e8400-e29b-41d4-a716-446655440000",
  "product_id": "550e8400-e29b-41d4-a716-446655440000",
  "sku": "WBH-BLK-2024",
  "barcode": "1234567890123",
  "status": "ACTIVE",
  "price": {
    "amount": 6999,
    "currency": "USD"
  },
  "compare_at_price": {
    "amount": 9999,
    "currency": "USD"
  },
  "cost": {
    "amount": 4000,
    "currency": "USD"
  },
  "weight": 240,
  "length": 200,
  "width": 180,
  "height": 85,
  "is_default": true,
  "created_at": "2024-01-15T11:00:00Z",
  "updated_at": "2024-01-16T12:00:00Z"
}
```

**Error Response** (404 Not Found):

```json
{
  "detail": "Variant 660e8400-e29b-41d4-a716-446655440000 not found"
}
```

**Notes**:

- Updates invalidate product cache

**cURL Example**:

```bash
curl -X PATCH "http://localhost:8000/api/admin/products/variants/660e8400-e29b-41d4-a716-446655440000" \
  -H "Authorization: Bearer eyJhbGc..." \
  -H "Content-Type: application/json" \
  -d '{
    "status": "ACTIVE",
    "price_amount": 6999,
    "price_currency": "USD"
  }'
```

---

#### Deactivate Variant

Set variant status to INACTIVE, hiding it from storefront without deleting it.

- **Method**: `POST`
- **Path**: `/api/admin/products/variants/{variant_id}/deactivate`
- **Authentication**: Required
- **Authorization**: `products:variant_write`
- **Headers**:
  - `Authorization: Bearer <token>` (required)

**Path Parameters**:
| Parameter | Type | Description |
|-----------|------|-------------|
| `variant_id` | UUID | Variant identifier |

**Success Response** (200 OK):

```json
{
  "id": "660e8400-e29b-41d4-a716-446655440000",
  "product_id": "550e8400-e29b-41d4-a716-446655440000",
  "sku": "WBH-BLK-2024",
  "barcode": null,
  "status": "INACTIVE",
  "price": {
    "amount": 7999,
    "currency": "USD"
  },
  "compare_at_price": null,
  "cost": null,
  "weight": null,
  "length": null,
  "width": null,
  "height": null,
  "is_default": true,
  "created_at": "2024-01-15T11:00:00Z",
  "updated_at": "2024-01-16T13:00:00Z"
}
```

**Error Response** (404 Not Found):

```json
{
  "detail": "Variant 660e8400-e29b-41d4-a716-446655440000 not found"
}
```

**cURL Example**:

```bash
curl -X POST "http://localhost:8000/api/admin/products/variants/660e8400-e29b-41d4-a716-446655440000/deactivate" \
  -H "Authorization: Bearer eyJhbGc..."
```

---

### 4.3 Inventory Management

#### Adjust Stock

Adjust inventory levels for a variant. Uses database row locking (SELECT FOR UPDATE) to prevent race conditions in concurrent adjustments.

- **Method**: `POST`
- **Path**: `/api/admin/products/variants/{variant_id}/stock-adjustments`
- **Authentication**: Required
- **Authorization**: `inventory:adjust`
- **Headers**:
  - `Authorization: Bearer <token>` (required)
  - `Content-Type: application/json` (required)

**Path Parameters**:
| Parameter | Type | Description |
|-----------|------|-------------|
| `variant_id` | UUID | Variant identifier |

**Request Body** (`AdjustStockRequestSchema`):

```json
{
  "delta": 50,
  "reason": "purchase_order",
  "note": "Received PO #12345 from supplier"
}
```

**Field Notes**:

- `delta`: Positive to add stock, negative to remove
- `delta`: Cannot be zero
- `reason`: Common values: `purchase_order`, `return`, `damage`, `correction`, `sale`, etc.
- Adjustment will fail if result would be negative (unless `allow_backorder` is enabled)

**Success Response** (200 OK) - Returns stock movement record:

```json
{
  "id": "990e8400-e29b-41d4-a716-446655440000",
  "variant_id": "660e8400-e29b-41d4-a716-446655440000",
  "delta": 50,
  "reason": "purchase_order",
  "note": "Received PO #12345 from supplier",
  "created_at": "2024-01-16T14:00:00Z",
  "created_by": "450e8400-e29b-41d4-a716-446655440000"
}
```

**Error Response** (400 Bad Request - insufficient stock):

```json
{
  "detail": "Cannot adjust stock: Would result in negative inventory (current: 10, delta: -50)"
}
```

**Error Response** (400 Bad Request - zero delta):

```json
{
  "detail": "Delta cannot be zero"
}
```

**Error Response** (404 Not Found):

```json
{
  "detail": "Variant 660e8400-e29b-41d4-a716-446655440000 not found"
}
```

**Notes**:

- Creates audit trail in `stock_movements` table
- Uses pessimistic locking for thread-safety
- Invalidates product cache

**cURL Example** (Add stock):

```bash
curl -X POST "http://localhost:8000/api/admin/products/variants/660e8400-e29b-41d4-a716-446655440000/stock-adjustments" \
  -H "Authorization: Bearer eyJhbGc..." \
  -H "Content-Type: application/json" \
  -d '{
    "delta": 50,
    "reason": "purchase_order",
    "note": "Received PO #12345"
  }'
```

**cURL Example** (Remove stock):

```bash
curl -X POST "http://localhost:8000/api/admin/products/variants/660e8400-e29b-41d4-a716-446655440000/stock-adjustments" \
  -H "Authorization: Bearer eyJhbGc..." \
  -H "Content-Type: application/json" \
  -d '{
    "delta": -10,
    "reason": "damage",
    "note": "Damaged units removed from inventory"
  }'
```

---

### 4.4 Product Images

#### Add Product Image (URL-based)

Add an image to a product by providing an image URL. Use this endpoint when the image is already hosted elsewhere. For uploading image files directly, use the `/images/upload` endpoint instead. Images are automatically positioned based on insertion order.

- **Method**: `POST`
- **Path**: `/api/admin/products/{product_id}/images`
- **Authentication**: Required
- **Authorization**: `products:media_write`
- **Headers**:
  - `Authorization: Bearer <token>` (required)
  - `Content-Type: application/json` (required)

**Path Parameters**:
| Parameter | Type | Description |
|-----------|------|-------------|
| `product_id` | UUID | Product identifier |

**Request Body** (`AddProductImageRequestSchema`):

```json
{
  "url": "https://cdn.example.com/products/headphones-front.jpg",
  "alt_text": "Wireless headphones front view"
}
```

**Success Response** (201 Created):

```json
{
  "id": "880e8400-e29b-41d4-a716-446655440000",
  "product_id": "550e8400-e29b-41d4-a716-446655440000",
  "url": "https://cdn.example.com/products/headphones-front.jpg",
  "alt_text": "Wireless headphones front view",
  "position": 0,
  "created_at": "2024-01-16T15:00:00Z"
}
```

**Error Response** (404 Not Found):

```json
{
  "detail": "Product 550e8400-e29b-41d4-a716-446655440000 not found"
}
```

**Notes**:

- Position is auto-assigned (next available position)
- Use reorder endpoint to change positions

**cURL Example**:

```bash
curl -X POST "http://localhost:8000/api/admin/products/550e8400-e29b-41d4-a716-446655440000/images" \
  -H "Authorization: Bearer eyJhbGc..." \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://cdn.example.com/products/headphones-front.jpg",
    "alt_text": "Front view"
  }'
```

---

#### Upload Product Image

Upload an image file directly to cloud storage (Cloudinary) and associate it with a product. This endpoint accepts multipart/form-data and performs comprehensive validation before uploading.

- **Method**: `POST`
- **Path**: `/api/admin/products/{product_id}/images/upload`
- **Authentication**: Required
- **Authorization**: `products:media_write`
- **Headers**:
  - `Authorization: Bearer <token>` (required)
  - `Content-Type: multipart/form-data` (required)

**Path Parameters**:
| Parameter | Type | Description |
|-----------|------|-------------|
| `product_id` | UUID | Product identifier |

**Form Data**:
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `file` | binary | Yes | Image file (JPEG, PNG, or WebP) |
| `alt_text` | string | No | Accessibility text (max 255 chars) |
| `position` | integer | No | Display order position (0-based, defaults to end) |

**Validation Rules**:

- Content-Type must be `image/jpeg`, `image/png`, or `image/webp`
- Maximum file size: 5MB (configurable via `MAX_IMAGE_BYTES`)
- File content validated using magic bytes (prevents extension spoofing)
- Image format must be parseable by image processing library

**Success Response** (201 Created):

```json
{
  "id": "880e8400-e29b-41d4-a716-446655440000",
  "product_id": "550e8400-e29b-41d4-a716-446655440000",
  "url": "https://res.cloudinary.com/cloud-name/image/upload/ecom/dev/products/550e.../image.jpg",
  "alt_text": "Wireless headphones front view",
  "position": 0,
  "created_at": "2024-01-16T15:00:00Z",
  "provider": "cloudinary",
  "provider_public_id": "ecom/dev/products/550e8400-e29b-41d4-a716-446655440000/image",
  "bytes_size": 123456,
  "width": 1920,
  "height": 1080,
  "format": "jpg"
}
```

**Error Response** (400 Bad Request - invalid format):

```json
{
  "detail": "Invalid image format. Allowed: image/jpeg, image/png, image/webp"
}
```

**Error Response** (400 Bad Request - file too large):

```json
{
  "detail": "Image file too large. Maximum size: 5242880 bytes"
}
```

**Error Response** (400 Bad Request - corrupted image):

```json
{
  "detail": "Unable to process image file. File may be corrupted or invalid."
}
```

**Error Response** (404 Not Found):

```json
{
  "detail": "Product 550e8400-e29b-41d4-a716-446655440000 not found"
}
```

**Error Response** (401 Unauthorized):

```json
{
  "detail": "Missing or invalid authorization header"
}
```

**Error Response** (403 Forbidden):

```json
{
  "detail": "Permission denied: products:media_write"
}
```

**Error Response** (500 Internal Server Error):

```json
{
  "detail": "Failed to upload image to storage provider"
}
```

**Notes**:

- Images are stored in cloud storage (Cloudinary by default)
- Position is auto-assigned to end if not specified
- Upload triggers cache invalidation for product detail and list endpoints
- Audit event `product.image.uploaded` is logged with metadata
- If `CLOUDINARY_URL` is not configured, falls back to local file storage

**cURL Example**:

```bash
curl -X POST "http://localhost:8000/api/admin/products/550e8400-e29b-41d4-a716-446655440000/images/upload" \
  -H "Authorization: Bearer eyJhbGc..." \
  -F "file=@/path/to/headphones-front.jpg" \
  -F "alt_text=Wireless headphones front view" \
  -F "position=0"
```

**Python Example** (using requests):

```python
import requests

url = "http://localhost:8000/api/admin/products/550e8400-e29b-41d4-a716-446655440000/images/upload"
headers = {"Authorization": "Bearer eyJhbGc..."}
files = {"file": open("headphones-front.jpg", "rb")}
data = {"alt_text": "Front view", "position": 0}

response = requests.post(url, headers=headers, files=files, data=data)
print(response.json())
```

---

#### Upload Variant Image

Upload an image file directly to cloud storage and associate it with a product variant. Identical validation and behavior to product image upload.

- **Method**: `POST`
- **Path**: `/api/admin/products/variants/{variant_id}/images/upload`
- **Authentication**: Required
- **Authorization**: `products:media_write`
- **Headers**:
  - `Authorization: Bearer <token>` (required)
  - `Content-Type: multipart/form-data` (required)

**Path Parameters**:
| Parameter | Type | Description |
|-----------|------|-------------|
| `variant_id` | UUID | Variant identifier |

**Form Data**:
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `file` | binary | Yes | Image file (JPEG, PNG, or WebP) |
| `alt_text` | string | No | Accessibility text (max 255 chars) |
| `position` | integer | No | Display order position (0-based, defaults to end) |

**Validation Rules**:

- Same validation as product image upload
- Content-Type: `image/jpeg`, `image/png`, or `image/webp`
- Maximum file size: 5MB (default)
- Magic byte validation enforced

**Success Response** (201 Created):

```json
{
  "id": "990e8400-e29b-41d4-a716-446655440000",
  "variant_id": "660e8400-e29b-41d4-a716-446655440000",
  "url": "https://res.cloudinary.com/cloud-name/image/upload/ecom/dev/variants/660e.../image.jpg",
  "alt_text": "Black variant side view",
  "position": 0,
  "created_at": "2024-01-16T15:30:00Z",
  "provider": "cloudinary",
  "provider_public_id": "ecom/dev/variants/660e8400-e29b-41d4-a716-446655440000/image",
  "bytes_size": 98765,
  "width": 1024,
  "height": 768,
  "format": "jpg"
}
```

**Error Response** (400 Bad Request - invalid format):

```json
{
  "detail": "Invalid image format. Allowed: image/jpeg, image/png, image/webp"
}
```

**Error Response** (404 Not Found):

```json
{
  "detail": "Variant 660e8400-e29b-41d4-a716-446655440000 not found"
}
```

**Notes**:

- Images stored in separate variant folder in cloud storage
- Invalidates parent product caches
- Audit event `variant.image.uploaded` is logged
- Variants can have multiple images (e.g., color variations)

**cURL Example**:

```bash
curl -X POST "http://localhost:8000/api/admin/products/variants/660e8400-e29b-41d4-a716-446655440000/images/upload" \
  -H "Authorization: Bearer eyJhbGc..." \
  -F "file=@/path/to/variant-black.jpg" \
  -F "alt_text=Black variant front view"
```

---

#### Remove Product Image

Delete an image from a product.

- **Method**: `DELETE`
- **Path**: `/api/admin/products/{product_id}/images/{image_id}`
- **Authentication**: Required
- **Authorization**: `products:media_write`
- **Headers**:
  - `Authorization: Bearer <token>` (required)

**Path Parameters**:
| Parameter | Type | Description |
|-----------|------|-------------|
| `product_id` | UUID | Product identifier |
| `image_id` | UUID | Image identifier |

**Success Response** (204 No Content):

```
(empty body)
```

**Error Response** (404 Not Found):

```json
{
  "detail": "Image 880e8400-e29b-41d4-a716-446655440000 not found for product 550e8400-e29b-41d4-a716-446655440000"
}
```

**Notes**:

- Invalidates product cache

**cURL Example**:

```bash
curl -X DELETE "http://localhost:8000/api/admin/products/550e8400-e29b-41d4-a716-446655440000/images/880e8400-e29b-41d4-a716-446655440000" \
  -H "Authorization: Bearer eyJhbGc..."
```

---

#### Reorder Product Images

Change the display order of product images.

- **Method**: `POST`
- **Path**: `/api/admin/products/{product_id}/images/reorder`
- **Authentication**: Required
- **Authorization**: `products:media_write`
- **Headers**:
  - `Authorization: Bearer <token>` (required)
  - `Content-Type: application/json` (required)

**Path Parameters**:
| Parameter | Type | Description |
|-----------|------|-------------|
| `product_id` | UUID | Product identifier |

**Request Body** (`ReorderImagesRequestSchema`):

```json
{
  "image_positions": {
    "880e8400-e29b-41d4-a716-446655440000": 2,
    "881e8400-e29b-41d4-a716-446655440001": 0,
    "882e8400-e29b-41d4-a716-446655440002": 1
  }
}
```

**Field Notes**:

- `image_positions`: Map of image_id (UUID) to position (integer, 0-based)
- Only images with changed positions need to be included

**Success Response** (200 OK):

```json
{
  "message": "Images reordered successfully"
}
```

**Error Response** (404 Not Found):

```json
{
  "detail": "Product 550e8400-e29b-41d4-a716-446655440000 not found"
}
```

**cURL Example**:

```bash
curl -X POST "http://localhost:8000/api/admin/products/550e8400-e29b-41d4-a716-446655440000/images/reorder" \
  -H "Authorization: Bearer eyJhbGc..." \
  -H "Content-Type: application/json" \
  -d '{
    "image_positions": {
      "880e8400-e29b-41d4-a716-446655440000": 2,
      "881e8400-e29b-41d4-a716-446655440001": 0
    }
  }'
```

---

### 4.5 Category Management

#### Create Category

Create a new product category. Supports hierarchical categories via `parent_id`.

- **Method**: `POST`
- **Path**: `/api/admin/categories`
- **Authentication**: Required
- **Authorization**: `categories:write`
- **Headers**:
  - `Authorization: Bearer <token>` (required)
  - `Content-Type: application/json` (required)

**Request Body** (`CreateCategoryRequestSchema`):

```json
{
  "name": "Electronics",
  "slug": "electronics",
  "parent_id": null
}
```

**Field Notes**:

- `parent_id`: Optional, UUID of parent category for hierarchical structure
- `slug`: Must be unique across all categories

**Success Response** (201 Created):

```json
{
  "id": "770e8400-e29b-41d4-a716-446655440000",
  "name": "Electronics",
  "slug": "electronics",
  "parent_id": null
}
```

**Error Response** (409 Conflict - duplicate slug):

```json
{
  "detail": "Category with slug 'electronics' already exists"
}
```

**cURL Example** (Root category):

```bash
curl -X POST "http://localhost:8000/api/admin/categories" \
  -H "Authorization: Bearer eyJhbGc..." \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Electronics",
    "slug": "electronics"
  }'
```

**cURL Example** (Child category):

```bash
curl -X POST "http://localhost:8000/api/admin/categories" \
  -H "Authorization: Bearer eyJhbGc..." \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Headphones",
    "slug": "headphones",
    "parent_id": "770e8400-e29b-41d4-a716-446655440000"
  }'
```

---

#### List Categories

List all categories. Returns flat list (clients must reconstruct hierarchy using `parent_id`).

- **Method**: `GET`
- **Path**: `/api/admin/categories`
- **Authentication**: Required
- **Authorization**: `categories:read`
- **Headers**:
  - `Authorization: Bearer <token>` (required)

**Success Response** (200 OK):

```json
[
  {
    "id": "770e8400-e29b-41d4-a716-446655440000",
    "name": "Electronics",
    "slug": "electronics",
    "parent_id": null
  },
  {
    "id": "771e8400-e29b-41d4-a716-446655440001",
    "name": "Headphones",
    "slug": "headphones",
    "parent_id": "770e8400-e29b-41d4-a716-446655440000"
  }
]
```

**Error Response** (401 Unauthorized):

```json
{
  "detail": "Missing or invalid authorization header"
}
```

**Error Response** (403 Forbidden):

```json
{
  "detail": "Permission denied: categories:read"
}
```

**cURL Example**:

```bash
curl -X GET "http://localhost:8000/api/admin/categories" \
  -H "Authorization: Bearer eyJhbGc..."
```

---

#### Assign Categories to Product

Assign one or more categories to a product. Replaces all existing category assignments.

- **Method**: `POST`
- **Path**: `/api/admin/products/{product_id}/categories`
- **Authentication**: Required
- **Authorization**: `categories:write`
- **Headers**:
  - `Authorization: Bearer <token>` (required)
  - `Content-Type: application/json` (required)

**Path Parameters**:
| Parameter | Type | Description |
|-----------|------|-------------|
| `product_id` | UUID | Product identifier |

**Request Body** (`AssignCategoriesRequestSchema`):

```json
{
  "category_ids": [
    "770e8400-e29b-41d4-a716-446655440000",
    "771e8400-e29b-41d4-a716-446655440001"
  ]
}
```

**Field Notes**:

- Empty array removes all category assignments
- Replaces existing assignments (not additive)

**Success Response** (200 OK):

```json
{
  "message": "Categories assigned successfully"
}
```

**Error Response** (404 Not Found):

```json
{
  "detail": "Product 550e8400-e29b-41d4-a716-446655440000 not found"
}
```

**cURL Example**:

```bash
curl -X POST "http://localhost:8000/api/admin/products/550e8400-e29b-41d4-a716-446655440000/categories" \
  -H "Authorization: Bearer eyJhbGc..." \
  -H "Content-Type: application/json" \
  -d '{
    "category_ids": [
      "770e8400-e29b-41d4-a716-446655440000"
    ]
  }'
```

---

### 4.6 Storefront Endpoints (Public)

#### List Published Products

List products visible on storefront. Only returns PUBLISHED products with ACTIVE variants. **No authentication required.**

- **Method**: `GET`
- **Path**: `/api/store/products`
- **Authentication**: None (public endpoint)
- **Authorization**: None

**Query Parameters**:
| Parameter | Type | Default | Constraints | Description |
|-----------|------|---------|-------------|-------------|
| `offset` | integer | 0 | >= 0 | Number of items to skip |
| `limit` | integer | 20 | 1-100 | Number of items to return |
| `category_id` | UUID | None | Valid UUID | Filter by category |
| `tag` | string | None | N/A | Filter by tag (exact match) |
| `featured` | boolean | None | true/false | Filter by featured flag |
| `sort_by` | string | `created_at` | `created_at`, `sort_order` | Sort field |
| `sort_desc` | boolean | true | true/false | Sort descending if true |

**Success Response** (200 OK):

```json
{
  "products": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "slug": "wireless-bluetooth-headphones",
      "name": "Wireless Bluetooth Headphones",
      "description_short": "Premium noise-cancelling headphones",
      "tags": ["electronics", "audio"],
      "featured": true
    }
  ],
  "total": 1,
  "offset": 0,
  "limit": 20
}
```

**Notes**:

- Response excludes internal fields: status, created_by, updated_by, timestamps
- Results are cached with key pattern `products:storefront:*`

**cURL Example** (List all):

```bash
curl -X GET "http://localhost:8000/api/store/products"
```

**cURL Example** (Filter by category):

```bash
curl -X GET "http://localhost:8000/api/store/products?category_id=770e8400-e29b-41d4-a716-446655440000"
```

**cURL Example** (Featured only):

```bash
curl -X GET "http://localhost:8000/api/store/products?featured=true"
```

---

#### Get Published Product Detail

Get detailed information for a published product by slug. **No authentication required.**

- **Method**: `GET`
- **Path**: `/api/store/products/{slug}`
- **Authentication**: None (public endpoint)
- **Authorization**: None

**Path Parameters**:
| Parameter | Type | Description |
|-----------|------|-------------|
| `slug` | string | Product slug (URL-safe identifier) |

**Success Response** (200 OK):

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "slug": "wireless-bluetooth-headphones",
  "name": "Wireless Bluetooth Headphones",
  "description_short": "Premium noise-cancelling headphones with 30-hour battery",
  "description_long": "Experience crystal-clear audio with advanced noise cancellation...",
  "tags": ["electronics", "audio", "wireless"],
  "featured": true,
  "variants": [
    {
      "id": "660e8400-e29b-41d4-a716-446655440000",
      "sku": "WBH-BLK-2024",
      "price": {
        "amount": 7999,
        "currency": "USD"
      },
      "compare_at_price": {
        "amount": 9999,
        "currency": "USD"
      },
      "is_default": true,
      "in_stock": true
    }
  ],
  "images": [
    {
      "id": "880e8400-e29b-41d4-a716-446655440000",
      "product_id": "550e8400-e29b-41d4-a716-446655440000",
      "url": "https://cdn.example.com/products/headphones-front.jpg",
      "alt_text": "Wireless headphones front view",
      "position": 0,
      "created_at": "2024-01-16T15:00:00Z",
      "provider": "cloudinary",
      "provider_public_id": "ecom/dev/products/550e8400-e29b-41d4-a716-446655440000/image",
      "bytes_size": 123456,
      "width": 1920,
      "height": 1080,
      "format": "jpg"
    }
  ],
  "categories": [
    {
      "id": "770e8400-e29b-41d4-a716-446655440000",
      "name": "Electronics",
      "slug": "electronics",
      "parent_id": null
    }
  ]
}
```

**Field Notes**:

- `in_stock`: Computed from inventory (available > 0 OR allow_backorder = true)
- `cost` field is **excluded** from storefront responses
- Only ACTIVE variants are included

**Error Response** (404 Not Found):

```json
{
  "detail": "Product with slug 'non-existent-slug' not found"
}
```

**Notes**:

- Result is cached with key `product:slug:{slug}`

**cURL Example**:

```bash
curl -X GET "http://localhost:8000/api/store/products/wireless-bluetooth-headphones"
```

---

## 5. End-to-End Flows

### Flow 1: Complete Product Lifecycle (Draft → Published)

This flow demonstrates the complete process of creating a product, adding variants and images, publishing it, and verifying storefront visibility.

#### Step 1: Login as Admin

**Request**:

```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@example.com",
    "password": "Admin123!"
  }'
```

**Response** (200 OK):

```json
{
  "access_token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "Bearer",
  "expires_in": 600
}
```

Save the `access_token` for subsequent requests.

---

#### Step 2: Create Product (DRAFT)

**Request**:

```bash
curl -X POST http://localhost:8000/api/admin/products \
  -H "Authorization: Bearer eyJhbGc..." \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Premium Wireless Earbuds",
    "slug": "premium-wireless-earbuds",
    "description_short": "True wireless earbuds with active noise cancellation",
    "description_long": "Immerse yourself in premium sound quality...",
    "tags": ["electronics", "audio", "wireless", "earbuds"],
    "featured": true,
    "sort_order": 5
  }'
```

**Response** (201 Created):

```json
{
  "id": "a10e8400-e29b-41d4-a716-446655440000",
  "status": "DRAFT",
  "name": "Premium Wireless Earbuds",
  "slug": "premium-wireless-earbuds",
  "description_short": "True wireless earbuds with active noise cancellation",
  "description_long": "Immerse yourself in premium sound quality...",
  "tags": ["electronics", "audio", "wireless", "earbuds"],
  "featured": true,
  "sort_order": 5,
  "created_at": "2024-01-20T10:00:00Z",
  "updated_at": "2024-01-20T10:00:00Z",
  "created_by": "450e8400-e29b-41d4-a716-446655440000",
  "updated_by": null
}
```

Save `product_id`: `a10e8400-e29b-41d4-a716-446655440000`

---

#### Step 3: Add Variant with Initial Stock

**Request**:

```bash
curl -X POST http://localhost:8000/api/admin/products/a10e8400-e29b-41d4-a716-446655440000/variants \
  -H "Authorization: Bearer eyJhbGc..." \
  -H "Content-Type: application/json" \
  -d '{
    "sku": "PWE-WHT-2024",
    "barcode": "9876543210987",
    "price_amount": 12999,
    "price_currency": "USD",
    "compare_at_price_amount": 15999,
    "compare_at_price_currency": "USD",
    "cost_amount": 7500,
    "cost_currency": "USD",
    "weight": 50,
    "is_default": true,
    "initial_stock": 250,
    "allow_backorder": false
  }'
```

**Response** (201 Created):

```json
{
  "id": "b20e8400-e29b-41d4-a716-446655440000",
  "product_id": "a10e8400-e29b-41d4-a716-446655440000",
  "sku": "PWE-WHT-2024",
  "barcode": "9876543210987",
  "status": "ACTIVE",
  "price": {
    "amount": 12999,
    "currency": "USD"
  },
  "compare_at_price": {
    "amount": 15999,
    "currency": "USD"
  },
  "cost": {
    "amount": 7500,
    "currency": "USD"
  },
  "weight": 50,
  "length": null,
  "width": null,
  "height": null,
  "is_default": true,
  "created_at": "2024-01-20T10:05:00Z",
  "updated_at": "2024-01-20T10:05:00Z"
}
```

Save `variant_id`: `b20e8400-e29b-41d4-a716-446655440000`

---

#### Step 4: Add Product Images

> **Note**: This example uses the URL-based endpoint (`/images`). Alternatively, you can upload image files directly using `/images/upload` with multipart/form-data. See "Upload Product Image" endpoint documentation for details.

**Request** (Image 1):

```bash
curl -X POST http://localhost:8000/api/admin/products/a10e8400-e29b-41d4-a716-446655440000/images \
  -H "Authorization: Bearer eyJhbGc..." \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://cdn.example.com/earbuds-main.jpg",
    "alt_text": "Premium wireless earbuds with charging case"
  }'
```

**Response** (201 Created):

```json
{
  "id": "c30e8400-e29b-41d4-a716-446655440000",
  "product_id": "a10e8400-e29b-41d4-a716-446655440000",
  "url": "https://cdn.example.com/earbuds-main.jpg",
  "alt_text": "Premium wireless earbuds with charging case",
  "position": 0,
  "created_at": "2024-01-20T10:10:00Z"
}
```

**Request** (Image 2):

```bash
curl -X POST http://localhost:8000/api/admin/products/a10e8400-e29b-41d4-a716-446655440000/images \
  -H "Authorization: Bearer eyJhbGc..." \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://cdn.example.com/earbuds-detail.jpg",
    "alt_text": "Earbud detail view"
  }'
```

**Response** (201 Created):

```json
{
  "id": "c31e8400-e29b-41d4-a716-446655440000",
  "product_id": "a10e8400-e29b-41d4-a716-446655440000",
  "url": "https://cdn.example.com/earbuds-detail.jpg",
  "alt_text": "Earbud detail view",
  "position": 1,
  "created_at": "2024-01-20T10:11:00Z"
}
```

---

#### Step 5: Attempt to Publish (Will Fail if Business Rules Not Met)

If a product doesn't meet publish criteria (no variants, inactive variants, etc.), publishing will fail.

**Request**:

```bash
curl -X POST http://localhost:8000/api/admin/products/a10e8400-e29b-41d4-a716-446655440000/publish \
  -H "Authorization: Bearer eyJhbGc..."
```

**Response** (200 OK - Success because we have active variant):

```json
{
  "id": "a10e8400-e29b-41d4-a716-446655440000",
  "status": "PUBLISHED",
  "name": "Premium Wireless Earbuds",
  "slug": "premium-wireless-earbuds",
  "description_short": "True wireless earbuds with active noise cancellation",
  "description_long": "Immerse yourself in premium sound quality...",
  "tags": ["electronics", "audio", "wireless", "earbuds"],
  "featured": true,
  "sort_order": 5,
  "created_at": "2024-01-20T10:00:00Z",
  "updated_at": "2024-01-20T10:15:00Z",
  "created_by": "450e8400-e29b-41d4-a716-446655440000",
  "updated_by": "450e8400-e29b-41d4-a716-446655440000"
}
```

---

#### Step 6: Verify Storefront Visibility (No Auth)

**Request**:

```bash
curl -X GET "http://localhost:8000/api/store/products/premium-wireless-earbuds"
```

**Response** (200 OK):

```json
{
  "id": "a10e8400-e29b-41d4-a716-446655440000",
  "slug": "premium-wireless-earbuds",
  "name": "Premium Wireless Earbuds",
  "description_short": "True wireless earbuds with active noise cancellation",
  "description_long": "Immerse yourself in premium sound quality...",
  "tags": ["electronics", "audio", "wireless", "earbuds"],
  "featured": true,
  "variants": [
    {
      "id": "b20e8400-e29b-41d4-a716-446655440000",
      "sku": "PWE-WHT-2024",
      "price": {
        "amount": 12999,
        "currency": "USD"
      },
      "compare_at_price": {
        "amount": 15999,
        "currency": "USD"
      },
      "is_default": true,
      "in_stock": true
    }
  ],
  "images": [
    {
      "id": "c30e8400-e29b-41d4-a716-446655440000",
      "product_id": "a10e8400-e29b-41d4-a716-446655440000",
      "url": "https://cdn.example.com/earbuds-main.jpg",
      "alt_text": "Premium wireless earbuds with charging case",
      "position": 0,
      "created_at": "2024-01-20T10:10:00Z"
    },
    {
      "id": "c31e8400-e29b-41d4-a716-446655440000",
      "product_id": "a10e8400-e29b-41d4-a716-446655440000",
      "url": "https://cdn.example.com/earbuds-detail.jpg",
      "alt_text": "Earbud detail view",
      "position": 1,
      "created_at": "2024-01-20T10:11:00Z"
    }
  ],
  "categories": []
}
```

**Note**: `cost` field is excluded from storefront response for security.

---

### Flow 2: Inventory Adjustment with Concurrency Safety

This flow demonstrates safe stock adjustments with audit trail.

#### Step 1: Check Current Inventory

**Request**:

```bash
curl -X GET "http://localhost:8000/api/admin/products/a10e8400-e29b-41d4-a716-446655440000" \
  -H "Authorization: Bearer eyJhbGc..."
```

**Response** (200 OK - extract inventory section):

```json
{
  "product": {...},
  "variants": [...],
  "inventory": {
    "b20e8400-e29b-41d4-a716-446655440000": {
      "variant_id": "b20e8400-e29b-41d4-a716-446655440000",
      "on_hand": 250,
      "reserved": 0,
      "allow_backorder": false,
      "available": 250
    }
  }
}
```

---

#### Step 2: Adjust Stock (Add Inventory)

**Request**:

```bash
curl -X POST "http://localhost:8000/api/admin/products/variants/b20e8400-e29b-41d4-a716-446655440000/stock-adjustments" \
  -H "Authorization: Bearer eyJhbGc..." \
  -H "Content-Type: application/json" \
  -d '{
    "delta": 100,
    "reason": "purchase_order",
    "note": "Received shipment from supplier - PO#2024-0115"
  }'
```

**Response** (200 OK):

```json
{
  "id": "d40e8400-e29b-41d4-a716-446655440000",
  "variant_id": "b20e8400-e29b-41d4-a716-446655440000",
  "delta": 100,
  "reason": "purchase_order",
  "note": "Received shipment from supplier - PO#2024-0115",
  "created_at": "2024-01-20T11:00:00Z",
  "created_by": "450e8400-e29b-41d4-a716-446655440000"
}
```

New inventory: `on_hand = 350`

---

#### Step 3: Adjust Stock (Remove Damaged Units)

**Request**:

```bash
curl -X POST "http://localhost:8000/api/admin/products/variants/b20e8400-e29b-41d4-a716-446655440000/stock-adjustments" \
  -H "Authorization: Bearer eyJhbGc..." \
  -H "Content-Type: application/json" \
  -d '{
    "delta": -5,
    "reason": "damage",
    "note": "5 units damaged during inspection"
  }'
```

**Response** (200 OK):

```json
{
  "id": "d41e8400-e29b-41d4-a716-446655440000",
  "variant_id": "b20e8400-e29b-41d4-a716-446655440000",
  "delta": -5,
  "reason": "damage",
  "note": "5 units damaged during inspection",
  "created_at": "2024-01-20T11:30:00Z",
  "created_by": "450e8400-e29b-41d4-a716-446655440000"
}
```

New inventory: `on_hand = 345`

---

#### Step 4: Attempt Invalid Adjustment (Insufficient Stock)

**Request**:

```bash
curl -X POST "http://localhost:8000/api/admin/products/variants/b20e8400-e29b-41d4-a716-446655440000/stock-adjustments" \
  -H "Authorization: Bearer eyJhbGc..." \
  -H "Content-Type: application/json" \
  -d '{
    "delta": -500,
    "reason": "sale",
    "note": "Large order"
  }'
```

**Response** (400 Bad Request):

```json
{
  "detail": "Cannot adjust stock: Would result in negative inventory"
}
```

**Note**: Concurrent adjustments are protected by database row-level locking (SELECT FOR UPDATE).

---

### Flow 3: Category Management and Assignment

#### Step 1: Create Category Hierarchy

**Request** (Root category):

```bash
curl -X POST http://localhost:8000/api/admin/categories \
  -H "Authorization: Bearer eyJhbGc..." \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Electronics",
    "slug": "electronics"
  }'
```

**Response** (201 Created):

```json
{
  "id": "e50e8400-e29b-41d4-a716-446655440000",
  "name": "Electronics",
  "slug": "electronics",
  "parent_id": null
}
```

---

**Request** (Child category):

```bash
curl -X POST http://localhost:8000/api/admin/categories \
  -H "Authorization: Bearer eyJhbGc..." \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Audio Devices",
    "slug": "audio-devices",
    "parent_id": "e50e8400-e29b-41d4-a716-446655440000"
  }'
```

**Response** (201 Created):

```json
{
  "id": "e51e8400-e29b-41d4-a716-446655440000",
  "name": "Audio Devices",
  "slug": "audio-devices",
  "parent_id": "e50e8400-e29b-41d4-a716-446655440000"
}
```

---

#### Step 2: Assign Categories to Product

**Request**:

```bash
curl -X POST "http://localhost:8000/api/admin/products/a10e8400-e29b-41d4-a716-446655440000/categories" \
  -H "Authorization: Bearer eyJhbGc..." \
  -H "Content-Type: application/json" \
  -d '{
    "category_ids": [
      "e50e8400-e29b-41d4-a716-446655440000",
      "e51e8400-e29b-41d4-a716-446655440000"
    ]
  }'
```

**Response** (200 OK):

```json
{
  "message": "Categories assigned successfully"
}
```

---

#### Step 3: Filter Products by Category

**Request**:

```bash
curl -X GET "http://localhost:8000/api/store/products?category_id=e51e8400-e29b-41d4-a716-446655440000"
```

**Response** (200 OK):

```json
{
  "products": [
    {
      "id": "a10e8400-e29b-41d4-a716-446655440000",
      "slug": "premium-wireless-earbuds",
      "name": "Premium Wireless Earbuds",
      "description_short": "True wireless earbuds with active noise cancellation",
      "tags": ["electronics", "audio", "wireless", "earbuds"],
      "featured": true
    }
  ],
  "total": 1,
  "offset": 0,
  "limit": 20
}
```

---

## 6. Appendix

### A. Common Error Codes

| HTTP Status | Error Type            | Common Causes                               | Example Detail Message                                                  |
| ----------- | --------------------- | ------------------------------------------- | ----------------------------------------------------------------------- |
| 400         | Bad Request           | Validation failure, business rule violation | "Product name cannot be empty"                                          |
| 400         | Bad Request           | Invalid stock adjustment                    | "Cannot adjust stock: Would result in negative inventory"               |
| 400         | Bad Request           | Publish validation failed                   | "Cannot publish product: Product must have at least one active variant" |
| 401         | Unauthorized          | Missing/invalid token                       | "Missing or invalid authorization header"                               |
| 401         | Unauthorized          | Token expired                               | "Token has expired"                                                     |
| 401         | Unauthorized          | Token version mismatch                      | "Token has been revoked"                                                |
| 403         | Forbidden             | Insufficient permissions                    | "Permission denied: products:write"                                     |
| 404         | Not Found             | Resource doesn't exist                      | "Product 550e8400-e29b-41d4-a716-446655440000 not found"                |
| 409         | Conflict              | Duplicate slug/SKU                          | "Product with slug 'wireless-headphones' already exists"                |
| 422         | Unprocessable Entity  | Request body schema validation              | Pydantic validation errors                                              |
| 500         | Internal Server Error | Unexpected server error                     | "Internal server error"                                                 |

### B. Business Rules & Constraints

#### Product Publishing Rules

A product can only be published if:

1. Product has a non-empty name and slug
2. Product has **at least one ACTIVE variant**
3. All ACTIVE variants have:
   - Valid SKU (non-empty)
   - Valid price (amount > 0)

**Implementation**: `ProductPublishPolicy` in domain layer

#### Stock Adjustment Rules

Stock adjustments must satisfy:

1. Delta cannot be zero
2. Result cannot be negative (unless `allow_backorder = true`)
3. Adjustments use database row-level locking for concurrency safety

**Implementation**: `InventoryPolicy` in domain layer

#### Uniqueness Constraints

- **Product slug**: Must be unique across all products
- **Variant SKU**: Must be unique across all variants
- **Category slug**: Must be unique across all categories
- **Product-Category**: One product cannot be assigned to the same category twice

#### Money Representation

All monetary values use **minor units** (cents for USD):

- `$19.99` → `{"amount": 1999, "currency": "USD"}`
- `€50.00` → `{"amount": 5000, "currency": "EUR"}`

This prevents floating-point precision errors in financial calculations.

#### Variant Status Transitions

- New variants are created with `status = ACTIVE`
- Use `PATCH /variants/{id}` or `POST /variants/{id}/deactivate` to change status
- Only `ACTIVE` variants appear on storefront

#### Product Status Transitions

```
DRAFT ────────> PUBLISHED ────────> ARCHIVED
  ^                 │                    │
  │                 │                    │
  └─────────────────┴────────────────────┘
         (status can change multiple times)
```

### C. Caching Behavior

The API implements caching at the application layer with automatic invalidation:

#### Cached Resources

- Individual products: `product:{product_id}`
- Products by slug: `product:slug:{slug}`
- Storefront listings: `products:storefront:*` (wildcard pattern)

#### Cache Invalidation Triggers

| Operation        | Invalidated Keys                                               |
| ---------------- | -------------------------------------------------------------- |
| Update product   | `product:{id}`, `product:slug:{slug}`                          |
| Publish product  | `product:{id}`, `product:slug:{slug}`, `products:storefront:*` |
| Archive product  | `product:{id}`, `product:slug:{slug}`, `products:storefront:*` |
| Update variant   | `product:{product_id}`, related slug and storefront keys       |
| Adjust stock     | `product:{product_id}`, related keys                           |
| Add/remove image | `product:{product_id}`, related keys                           |

**Implementation**: `CachePort` with Redis or in-memory cache

### D. Rate Limiting

No rate limiting is currently implemented for product endpoints. Consider implementing rate limiting for production deployments:

- Admin endpoints: 100 requests/minute per user
- Storefront endpoints: 1000 requests/minute per IP

### E. Audit Logging

All state-changing operations are logged via `AuditLogPort`:

**Event Types**:

- `product.created`
- `product.updated`
- `product.published`
- `product.archived`
- `variant.created`
- `variant.updated`
- `inventory.adjusted`
- `product.image.added`
- `product.image.uploaded`
- `product.image.removed`
- `variant.image.uploaded`
- `category.created`
- `product.categories.assigned`

**Event Structure**:

```json
{
  "event_type": "product.published",
  "user_id": "450e8400-e29b-41d4-a716-446655440000",
  "timestamp": "2024-01-20T10:15:00Z",
  "details": {
    "product_id": "a10e8400-e29b-41d4-a716-446655440000",
    "product_slug": "premium-wireless-earbuds"
  }
}
```

**Example - Image Upload Event**:

```json
{
  "event_type": "product.image.uploaded",
  "user_id": "450e8400-e29b-41d4-a716-446655440000",
  "timestamp": "2024-01-20T10:20:00Z",
  "details": {
    "product_id": "a10e8400-e29b-41d4-a716-446655440000",
    "image_id": "c30e8400-e29b-41d4-a716-446655440000",
    "url": "https://res.cloudinary.com/...",
    "provider": "cloudinary",
    "bytes_size": 123456
  }
}
```

---

**Document Version**: 1.1  
**Last Updated**: 2026-02-21  
**API Version**: Unversioned  
**Contact**: Backend Team

### Changelog

**Version 1.1** (2026-02-21):

- Added image upload endpoints (`/images/upload`) for products and variants
- Added support for Cloudinary cloud storage integration
- Updated ProductImageResponseSchema with metadata fields (provider, bytes_size, width, height, format)
- Added VariantImageResponseSchema
- Added image upload configuration documentation
- Updated audit logging to include image upload events

**Version 1.0** (2024-01-20):

- Initial API documentation release
