from urllib import request
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib import messages
from .models import Cart, CartItem, Product


# -------------------------------
# GET CART
# -------------------------------
def get_cart(request):
    if request.user.is_authenticated:
        cart, created = Cart.objects.get_or_create(user=request.user)
    else:
        # Guest cart in session
        cart_id = request.session.get("cart_id")
        if cart_id:
            try:
                cart = Cart.objects.get(id=cart_id, user__isnull=True)
            except Cart.DoesNotExist:
                cart = Cart.objects.create()
                request.session["cart_id"] = cart.id
        else:
            cart = Cart.objects.create()
            request.session["cart_id"] = cart.id
    return cart


# # -------------------------------
# # ADD TO CART
# # -------------------------------
# def add_to_cart(request, product_id):
#     if request.method != "POST":
#         return JsonResponse({"success": False, "error": "POST required"}, status=400)
    
#     cart = get_cart(request)
#     product = get_object_or_404(Product, id=product_id)

#     # Get or create cart item
#     item, created = CartItem.objects.get_or_create(cart=cart, product=product)

#     # Get quantity from form
#     qty = int(request.POST.get("quantity", 1))

#     # Check stock limit
#     if item.quantity + qty > product.stock:
#         # Set to max stock
#         item.quantity = product.stock
#         item.save()

#         # Check if AJAX request
#         if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
#             items = cart.items.all()
#             return JsonResponse({
#                 "success": False,
#                 "limit": True,
#                 "message": f"Only {product.stock} items available in stock!",
#                 "cart_count": items.count(),  # COUNT OF UNIQUE PRODUCTS
#                 "cart_total": float(sum(i.total_price for i in items))
#             })
        
#         messages.warning(request, f"Only {product.stock} items available!")
#         return redirect("cart_page")

 
#     if not created:
#         item.quantity += qty
#     else:
#         item.quantity = qty
    
#     item.save()

#     # Check if AJAX request
#     if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
#         items = cart.items.all()
#         return JsonResponse({
#             "success": True,
#             "limit": False,
#             "message": "Product added to cart successfully!",
#             "cart_count": items.count(),  # COUNT OF UNIQUE PRODUCTS
#             "cart_total": float(sum(i.total_price for i in items)),
#             "product_name": product.name
#         })
    
    
#     messages.success(request, f"{product.name} added to cart!")
#     return redirect("cart_page")

# cart/views.py

def add_to_cart(request, product_id):
    if request.method != "POST":
        return JsonResponse({"success": False, "error": "POST required"}, status=400)
    
    cart = get_cart(request)
    product = get_object_or_404(Product, id=product_id)

    # Get or create cart item
    item, created = CartItem.objects.get_or_create(cart=cart, product=product)

    # Get quantity from form
    qty = int(request.POST.get("quantity", 1))

    # Check stock limit
    if item.quantity + qty > product.stock:
        item.quantity = product.stock
        item.save()

        # AJAX request
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            items = cart.items.all()
            return JsonResponse({
                "success": False,
                "limit": True,
                "message": f"Only {product.stock} items available in stock!",
                "cart_count": items.count(),
                "cart_total": float(sum(i.total_price for i in items))
            })
        
        messages.warning(request, f"Only {product.stock} items available!")
        # ✅ REDIRECT TO PREVIOUS PAGE INSTEAD OF cart_page
        return redirect(request.META.get('HTTP_REFERER', 'cart_page'))

    # Normal add
    if not created:
        item.quantity += qty
    else:
        item.quantity = qty
    
    item.save()

    # AJAX request
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        items = cart.items.all()
        return JsonResponse({
            "success": True,
            "limit": False,
            "message": "Product added to cart successfully!",
            "cart_count": items.count(),
            "cart_total": float(sum(i.total_price for i in items)),
            "product_name": product.name
        })
    
    messages.success(request, f"{product.name} added to cart!")
    # ✅ REDIRECT TO PREVIOUS PAGE INSTEAD OF cart_page
    return redirect(request.META.get('HTTP_REFERER', 'cart_page'))

# def add_to_cart(request, product_id):
#     if request.method != "POST":
#         return JsonResponse({"success": False, "error": "POST required"}, status=400)
    
#     cart = get_cart(request)
#     product = get_object_or_404(Product, id=product_id)

#     # Get or create cart item
#     item, created = CartItem.objects.get_or_create(cart=cart, product=product)

#     # Get quantity from form
#     qty = int(request.POST.get("quantity", 1))

#     # Check stock limit
#     if item.quantity + qty > product.stock:
#         item.quantity = product.stock
#         item.save()

#         # AJAX request
#         if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
#             items = cart.items.all()
#             return JsonResponse({
#                 "success": False,
#                 "limit": True,
#                 "message": f"Only {product.stock} items available!",
#                 "cart_count": items.count(),
#                 "cart_total": float(sum(i.total_price for i in items))
#             })
        
#         messages.warning(request, f"Only {product.stock} items available!")
#         return redirect(request.META.get('HTTP_REFERER', '/'))

#     # Normal add
#     if not created:
#         item.quantity += qty
#     else:
#         item.quantity = qty
#     item.save()

#     # AJAX request
#     if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
#         items = cart.items.all()
#         return JsonResponse({
#             "success": True,
#             "limit": False,
#             "message": "Product added to cart successfully!",
#             "cart_count": items.count(),
#             "cart_total": float(sum(i.total_price for i in items)),
#             "product_name": product.name
#         })
    
#     # Normal request
#     messages.success(request, f"{product.name} added to cart!")
#     return redirect(request.META.get('HTTP_REFERER', '/'))

# -------------------------------
# VIEW CART
# -------------------------------
def cart_page(request):
    cart = get_cart(request)
    items = cart.items.all()
    total = sum(item.total_price for item in items)

    return render(request, "cart.html", {
        "cart": cart,
        "items": items,
        "total": total,
    })


# -------------------------------
# INCREASE QUANTITY
# -------------------------------
def increase_qty(request, item_id):
    item = get_object_or_404(CartItem, id=item_id)
    product = item.product

    # Check stock limit
    if item.quantity >= product.stock:
        return JsonResponse({
            'success': False,
            'limit_reached': True,
            'quantity': item.quantity,
            'message': 'Maximum stock reached!',
            'item_total': float(item.total_price),
            'cart_total': float(sum(i.total_price for i in item.cart.items.all())),
            'cart_count': item.cart.items.count()  # COUNT OF UNIQUE PRODUCTS
        })
    
    # Increase by 1
    item.quantity += 1
    item.save()

    cart = item.cart
    items = cart.items.all()
    total = sum(i.total_price for i in items)

    # If from checkout page, redirect
    if "checkout" in request.GET:
        return redirect("checkout_page")

    return JsonResponse({
        'success': True,
        'quantity': item.quantity,
        'item_total': float(item.total_price),
        'cart_total': float(total),
        'cart_count': items.count()  # COUNT OF UNIQUE PRODUCTS
    })


# -------------------------------
# DECREASE QUANTITY
# -------------------------------
def decrease_qty(request, item_id):
    item = get_object_or_404(CartItem, id=item_id)
    cart = item.cart
 
    # Block if quantity is 1
    if item.quantity == 1:
        return JsonResponse({
            "success": False,
            "block": True,
            "quantity": item.quantity,
            "message": "Minimum quantity is 1",
            "item_total": float(item.total_price),
            "cart_total": float(sum(i.total_price for i in cart.items.all())),
            "cart_count": cart.items.count()  # COUNT OF UNIQUE PRODUCTS
        })

    # Decrease by 1
    item.quantity -= 1
    item.save()

    items = cart.items.all()
    total = sum(i.total_price for i in items)

    # If from checkout page, redirect
    if "checkout" in request.GET:
        return redirect("checkout_page")

    return JsonResponse({
        "success": True,
        "block": False,
        "quantity": item.quantity,
        "item_total": float(item.total_price),
        "cart_total": float(total),
        "cart_count": items.count()  # COUNT OF UNIQUE PRODUCTS
    })


# ---------------------------------------------------
# REMOVE ITEM
# ---------------------------------------------------
 

def remove_item(request, item_id):
    item = get_object_or_404(CartItem, id=item_id)
    cart = item.cart
    product_name = item.product.name

    item.delete()

    # Recalculate totals after deletion
    items = cart.items.all()
    total = sum(i.total_price for i in items)
    cart_count = items.count()

    # AJAX RESPONSE
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return JsonResponse({
            "success": True,
            "message": f"{product_name} removed from cart",
            "cart_total": float(total),
            "cart_count": cart_count,
        })

    messages.success(request, f"{product_name} removed from cart")
    return redirect("cart_page")