# AI Coding Agent Instructions for Fragrance Store

## Project Overview
This is a Django 4.2 e-commerce platform for selling fragrances. The architecture uses a modular app structure with 7 Django apps, each handling a specific domain: accounts (authentication), cart, orders, products, adminpanel, wishlist, and core (general pages).

## Architecture & Key Components

### App Structure & Responsibilities
- **accounts**: User registration, login, OTP verification, password reset, profile management. Key: OTP-based email verification required for signup.
- **products**: Catalog management (Product, Category, Collection models) with slug-based URLs and auto-slug generation via `slugify()`. Supports product images via `ProductImage` model.
- **cart**: Shopping cart with `Cart` (user-scoped) and `CartItem` models. Uses `unique_together` constraint to prevent duplicate items. Session-based for anonymous users (stored in request.session).
- **orders**: Order creation with auto-generated order IDs (format: `RZ-{8-char-code}`). Status workflow: processing → shipped → delivered. `OrderItem` stores snapshot of product price at purchase time.
- **wishlist**: User wishlists (OneToOne with User, ManyToMany with Product). Separate from cart.
- **adminpanel**: Admin-only views (staff/superuser only) for product/category/collection management and order/customer dashboards.
- **core**: Homepage, about, contact pages. Contains shared context processors for cart/wishlist counts and recommended products.

### Data Flow & Cross-Component Communication
1. **Cart & Orders**: Cart items → OrderItem (cart not cleared, just creates Order with snapshots)
2. **Product Availability**: `Product.available` boolean controls visibility in recommendations
3. **Context Processors** (auto-injected into all templates):
   - `cart_count`: Current cart item count for authenticated users
   - `wishlist_count`: Current wishlist product count
   - `recommended_products`: 8 random products (excludes user's cart items if logged in)
   - `cart_data`: Full cart with subtotal/total for checkout pages
4. **User Relationships**: One User can have one Profile (address/phone), one Wishlist, multiple Orders

### Media & Static Files
- Images stored in `media/` subdirectories: `categories/`, `collections/`, `products/gallery/`
- Static assets in `static/assets/`, `static/cdn/`
- Configure with `MEDIA_URL`, `MEDIA_ROOT` in settings.py

## Critical Development Patterns

### Model Conventions
- **Slug Auto-Generation**: All slug fields use `slugify()` in model's `save()` method (see Category, Collection, Product). Never leave slug blank.
- **Decimal Fields**: Use `DecimalField(max_digits=10, decimal_places=2)` for prices (not Float).
- **Foreign Keys**: Prefer `on_delete=models.CASCADE` for owned relationships; use `models.SET_NULL` only for optional references (e.g., Product.category).
- **Timestamps**: Use `created_at` with `auto_now_add=True`, not `updated_at` (removed in v2 of orders).
- **User Relationships**: Use `on_delete=models.CASCADE` (cascade deletes user data if account removed).

### View Access Control
```python
@login_required
@user_passes_test(admin_only)
def admin_function(request):
    # admin_only = lambda user: user.is_superuser or user.is_staff
```
All `/adminpanel/` views require both decorators. No AJAX endpoints secured this way.

### Cart Handling (Session vs. DB)
- **Authenticated users**: Cart stored in DB via `Cart` model
- **Anonymous users**: Cart stored in `request.session['cart']` (dict of {product_id: quantity})
- **Context processor `cart_data()`** handles both cases; always check `hasattr(cart, 'items')`

### Template Context Processor Pattern
Custom context processors defined in each app (e.g., `cart.context_processors`, `core.context_processors`), registered in `TEMPLATES['OPTIONS']['context_processors']` in settings.py. Always add to settings when creating new processors.

### OTP & Email Flow
- OTP generated as random 6-digit string, stored in `EmailOTP` (OneToOne with User)
- Sent via `django.core.mail.send_mail()`
- User must verify OTP to activate account (`user.is_active = False` until verified)
- Uses `settings.EMAIL_HOST_USER` for sender email

## Developer Workflow

### Running the Server
```bash
python manage.py runserver  # http://localhost:8000
```

### Database Migrations
```bash
python manage.py makemigrations  # Detect model changes
python manage.py migrate         # Apply all pending migrations
```

### Creating a New App
```bash
python manage.py startapp <app_name>
# Then: 1) Add to INSTALLED_APPS in settings.py
#       2) Create urls.py and include in ecommerce/urls.py
#       3) Define models, migrations, views
```

### Django Shell (Testing Queries)
```bash
python manage.py shell
>>> from products.models import Product
>>> Product.objects.filter(available=True).count()
```

### Database & Environment
- **Database**: SQLite (`db.sqlite3`) for development; requires `mysqlclient==2.2.7` for MySQL production
- **Secret Key**: Currently hardcoded (insecure) in settings.py — do NOT commit production secrets
- **Debug**: `DEBUG = True` in settings.py; set to False in production

## Project-Specific Conventions

### URL Naming Conventions
- Category/Collection/Product detail pages use slug: `reverse('category_detail', args=[slug])`
- Admin URLs follow `admin<resource>list`/`admin<resource>add`/`admin<resource>edit` pattern
- Include resource-specific URLs with `include('<app>.urls')` in main urlpatterns

### Template Hierarchy
- Base template: `templates/base.html` (extends with `{% extends "base.html" %}`)
- App-specific templates in `<app>/templates/` (auto-discovered via `APP_DIRS: True`)
- Template tags: Use `{% load static %}` and `{% static 'path' %}` for static files

### Price & Quantity Calculations
- `CartItem.total_price` = `product.price * quantity` (property, not DB field)
- `Order.total_quantity` = sum of all `OrderItem.quantity` values
- `OrderItem.total_price` = `quantity * price` (both as properties)
- **Important**: Order stores snapshot of price at purchase time, not linked to Product.price

### Authentication & Authorization
- User creation: `User.objects.create_user(username, email, password)`
- Check admin: `user.is_superuser or user.is_staff`
- Check authenticated: `request.user.is_authenticated`
- Password reset: Uses token stored in `password_reset_tokens` dict (in-memory, not persistent)

## Known Limitations & Quirks
1. **Password reset tokens** stored in memory dict — lost on server restart; migrate to DB-backed tokens for production
2. **Cart for anonymous users** stored in session — not persistent across browsers/devices
3. **Recommended products** use `.order_by('?')` for randomization — slow on large datasets; consider caching
4. **Admin panel** has no role-based permissions (only superuser/staff check) — consider adding granular permissions
5. **Email configuration** requires `EMAIL_HOST`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD` in settings (currently missing/incomplete)
6. **Media files** require manual cleanup of orphaned images when products deleted

## Key Files Reference
- Settings & config: `ecommerce/settings.py`, `ecommerce/urls.py`
- Models: `products/models.py`, `orders/models.py`, `accounts/models.py`, `cart/models.py`
- Views: `adminpanel/views.py` (admin workflows), `accounts/views.py` (auth flows)
- Templates: `templates/base.html`, `adminpanel/templates/`, `accounts/templates/`
- Context processors: `core/context_processors.py`, `cart/context_processors.py`
