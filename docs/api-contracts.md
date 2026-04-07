# API Contracts

Complete REST API documentation.

---

## Base URL

- **Development:** `http://localhost:8000/api`
- **Production:** `https://back-end-production-1219.up.railway.app/api`

---

## Authentication

Most endpoints accept optional authentication. Some require it.

```
Authorization: Bearer <jwt_token>
```

---

## Recipes

### List Recipes

```
GET /api/recipes
```

**Query Parameters:**
| Param | Type | Description |
|-------|------|-------------|
| template | string | Filter by cocktail family |
| main_spirit | string | Filter by main spirit |
| glassware | string | Filter by glass type |
| serving_style | string | Filter by serving style |
| method | string | Filter by prep method |
| search | string | Search name/description |
| min_rating | int | Minimum personal rating (1-5) |
| user_id | string | Filter by owner |
| visibility | string | Filter by visibility |
| skip | int | Offset for pagination (default: 0) |
| limit | int | Max results (default: 50, max: 100) |

**Response:** `200 OK`
```json
[
  {
    "id": "abc123",
    "name": "Margarita",
    "template": "sour",
    "main_spirit": "tequila",
    "glassware": "coupe",
    "serving_style": "up",
    "has_image": true,
    "user_id": "user123",
    "visibility": "public",
    "my_rating": 5,
    "created_at": "2024-01-15T10:30:00Z"
  }
]
```

### Get Recipe Count

```
GET /api/recipes/count
```

Same query parameters as List Recipes.

**Response:** `200 OK`
```json
{
  "total": 150,
  "filtered": 42
}
```

### Get Recipe

```
GET /api/recipes/{id}
```

**Response:** `200 OK`
```json
{
  "id": "abc123",
  "name": "Margarita",
  "description": "Classic tequila sour",
  "instructions": "1. Add all to shaker...",
  "template": "sour",
  "main_spirit": "tequila",
  "glassware": "coupe",
  "serving_style": "up",
  "method": "shaken",
  "garnish": "Lime wheel",
  "notes": null,
  "source_type": "screenshot",
  "user_id": "user123",
  "visibility": "public",
  "my_rating": 5,
  "has_image": true,
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z",
  "ingredients": [
    {
      "id": "ing1",
      "amount": 2.0,
      "unit": "oz",
      "notes": null,
      "optional": false,
      "order": 0,
      "ingredient": {
        "id": "tequila1",
        "name": "Blanco Tequila",
        "type": "spirit",
        "spirit_category": "tequila"
      }
    }
  ]
}
```

### Get Recipe Image

```
GET /api/recipes/{id}/image
```

Supports HTTP Range requests for efficient streaming.

**Response:** `200 OK` (image/jpeg, image/png, etc.)

### Create Recipe

```
POST /api/recipes
Content-Type: application/json
Authorization: Bearer <token> (optional)
```

**Request Body:**
```json
{
  "name": "Margarita",
  "description": "Classic tequila sour",
  "instructions": "Shake all with ice...",
  "template": "sour",
  "main_spirit": "tequila",
  "glassware": "coupe",
  "serving_style": "up",
  "method": "shaken",
  "garnish": "Lime wheel",
  "visibility": "public",
  "ingredients": [
    {
      "ingredient_name": "Blanco Tequila",
      "ingredient_type": "spirit",
      "amount": 2.0,
      "unit": "oz"
    },
    {
      "ingredient_name": "Lime Juice",
      "ingredient_type": "juice",
      "amount": 1.0,
      "unit": "oz"
    }
  ]
}
```

**Response:** `200 OK` (full recipe object)

### Update Recipe

```
PUT /api/recipes/{id}
Content-Type: application/json
Authorization: Bearer <token>
```

Only the recipe owner can update. Same body format as Create.

**Response:** `200 OK` (updated recipe object)

### Delete Recipe

```
DELETE /api/recipes/{id}
Authorization: Bearer <token>
```

Only the recipe owner can delete.

**Response:** `200 OK`
```json
{"message": "Recipe deleted successfully"}
```

### Set Personal Rating

```
PUT /api/recipes/{id}/my-rating
Content-Type: application/json
Authorization: Bearer <token>
```

**Request Body:**
```json
{"rating": 5}
```

**Response:** `200 OK`
```json
{"message": "Rating updated", "rating": 5}
```

### Clear Personal Rating

```
DELETE /api/recipes/{id}/my-rating
Authorization: Bearer <token>
```

**Response:** `200 OK`
```json
{"message": "Rating cleared"}
```

---

## Upload & Extraction

### Upload Image (with duplicate check)

```
POST /api/upload
Content-Type: multipart/form-data
```

**Query Parameters:**
| Param | Type | Description |
|-------|------|-------------|
| check_duplicates | bool | Check for duplicates (default: true) |

**Form Data:**
- `file`: Image file (jpg, png, gif, webp)

**Response:** `200 OK`
```json
{
  "job": {
    "id": "job123",
    "status": "pending",
    "image_path": "/uploads/abc.jpg",
    "created_at": "2024-01-15T10:30:00Z"
  },
  "duplicates": {
    "is_duplicate": true,
    "matches": [
      {
        "recipe_id": "existing123",
        "recipe_name": "Margarita",
        "match_type": "exact_image",
        "confidence": 100,
        "details": "Identical image hash"
      }
    ]
  }
}
```

### Extract Recipe (from pending job)

```
POST /api/upload/{job_id}/extract
```

**Response:** `200 OK` (extracted recipe object)

### Upload and Extract Immediately

```
POST /api/upload/extract-immediate
Content-Type: multipart/form-data
```

**Form Data:**
- `file`: Image file

**Response:** `200 OK` (extracted recipe object)

### Upload Multiple Images

```
POST /api/upload/extract-multi
Content-Type: multipart/form-data
```

For recipes that span multiple screenshots.

**Form Data:**
- `files`: Multiple image files

**Response:** `200 OK` (single combined recipe)

### Enhance Recipe with More Images

```
POST /api/upload/enhance/{recipe_id}
Content-Type: multipart/form-data
Authorization: Bearer <token>
```

Add more screenshots to an existing recipe.

**Form Data:**
- `files`: Additional image files

**Response:** `200 OK` (updated recipe)

### Get Job Status

```
GET /api/upload/{job_id}
```

**Response:** `200 OK`
```json
{
  "id": "job123",
  "status": "completed",
  "recipe_id": "abc123",
  "created_at": "2024-01-15T10:30:00Z",
  "completed_at": "2024-01-15T10:30:05Z"
}
```

---

## Categories

### Get All Categories

```
GET /api/categories
```

**Response:** `200 OK`
```json
{
  "templates": [
    {"value": "sour", "display_name": "Sour", "description": "Spirit + citrus + sweet"}
  ],
  "spirits": [
    {"value": "gin", "display_name": "Gin"}
  ],
  "glassware": [
    {
      "name": "Stemmed",
      "items": [
        {"value": "coupe", "display_name": "Coupe"}
      ]
    }
  ],
  "serving_styles": [...],
  "methods": [...]
}
```

---

## Authentication

### Register

```
POST /api/auth/register
Content-Type: application/json
```

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "securepassword",
  "display_name": "John"
}
```

**Response:** `200 OK`
```json
{
  "access_token": "eyJ...",
  "token_type": "bearer",
  "user": {
    "id": "user123",
    "email": "user@example.com",
    "display_name": "John"
  }
}
```

### Login

```
POST /api/auth/login
Content-Type: application/x-www-form-urlencoded
```

**Form Data:**
- `username`: Email address
- `password`: Password

**Response:** `200 OK`
```json
{
  "access_token": "eyJ...",
  "token_type": "bearer",
  "user": {...}
}
```

### Get Current User

```
GET /api/auth/me
Authorization: Bearer <token>
```

**Response:** `200 OK`
```json
{
  "id": "user123",
  "email": "user@example.com",
  "display_name": "John",
  "created_at": "2024-01-01T00:00:00Z"
}
```

---

## Collections (Playlists)

### List Collections

```
GET /api/collections
Authorization: Bearer <token>
```

**Response:** `200 OK`
```json
[
  {
    "id": "col123",
    "name": "Favorites",
    "description": "My best cocktails",
    "is_public": false,
    "recipe_count": 15,
    "created_at": "2024-01-15T10:30:00Z"
  }
]
```

### Get Collection

```
GET /api/collections/{id}
Authorization: Bearer <token>
```

**Response:** `200 OK`
```json
{
  "id": "col123",
  "name": "Favorites",
  "description": "My best cocktails",
  "is_public": false,
  "recipe_count": 2,
  "recipes": [
    {
      "id": "cr1",
      "recipe_id": "abc123",
      "recipe_name": "Margarita",
      "recipe_template": "sour",
      "recipe_has_image": true,
      "position": 0,
      "added_at": "2024-01-15T10:30:00Z"
    }
  ]
}
```

### Create Collection

```
POST /api/collections
Content-Type: application/json
Authorization: Bearer <token>
```

**Request Body:**
```json
{
  "name": "Summer Drinks",
  "description": "Refreshing cocktails",
  "is_public": true
}
```

### Add Recipe to Collection

```
POST /api/collections/{id}/recipes
Content-Type: application/json
Authorization: Bearer <token>
```

**Request Body:**
```json
{"recipe_id": "abc123"}
```

### Remove Recipe from Collection

```
DELETE /api/collections/{id}/recipes/{recipe_id}
Authorization: Bearer <token>
```

---

## Error Responses

All errors return JSON:

```json
{
  "detail": "Error message here"
}
```

Common status codes:
- `400` - Bad request (validation error)
- `401` - Unauthorized (missing/invalid token)
- `403` - Forbidden (not owner)
- `404` - Not found
- `500` - Server error
