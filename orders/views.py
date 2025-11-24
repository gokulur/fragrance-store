from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from decimal import Decimal
from .models import Order, OrderItem, ShippingAddress
from products.models import Product
from cart.models import Cart, CartItem
from cart.views import get_cart

# -----------------------------
# BUY NOW - Store in Session
# -----------------------------
@login_required
def buy_now(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    
    qty = int(request.POST.get("quantity", 1))
    
    # Store buy_now product in session (doesn't affect cart)
    request.session['buy_now_item'] = {
        'product_id': product.id,
        'quantity': qty
    }
    request.session.modified = True
    
    return redirect("checkout_page")


# -----------------------------
# UPDATE BUY NOW QUANTITY (AJAX SUPPORT)
# -----------------------------
@login_required
def update_buy_now_quantity(request, action):
    """Update quantity for buy_now item in session"""
    buy_now_item = request.session.get('buy_now_item')
    
    if buy_now_item:
        product = get_object_or_404(Product, id=buy_now_item['product_id'])
        
        if action == 'increase':
            if buy_now_item['quantity'] < product.stock:
                buy_now_item['quantity'] += 1
        elif action == 'decrease':
            if buy_now_item['quantity'] > 1:
                buy_now_item['quantity'] -= 1
        
        request.session['buy_now_item'] = buy_now_item
        request.session.modified = True
        
        # Check if AJAX request
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            # Calculate new totals
            subtotal = product.price * buy_now_item['quantity']
            shipping = Decimal('50.00')
            tax = round(subtotal * Decimal('0.18'), 2)
            total = subtotal + shipping + tax
            
            return JsonResponse({
                'success': True,
                'quantity': buy_now_item['quantity'],
                'subtotal': float(subtotal),
                'shipping': float(shipping),
                'tax': float(tax),
                'total': float(total)
            })
    
    return redirect('checkout_page')


# -----------------------------
# CANCEL BUY NOW
# -----------------------------
@login_required
def cancel_buy_now(request):
    """Cancel buy now and return to previous page"""
    if 'buy_now_item' in request.session:
        del request.session['buy_now_item']
        request.session.modified = True
    
    return redirect(request.META.get('HTTP_REFERER', 'home'))


# -----------------------------
# CHECKOUT PAGE (GET) - FIXED
# -----------------------------
@login_required
def checkout_page(request):
    cart = get_cart(request)
    
    # Check if user came from cart (has ?from=cart or has cart items)
    from_cart = request.GET.get('from') == 'cart'
    has_cart_items = cart.items.exists()
    
    # If coming from cart and has items, clear any old buy_now session
    if from_cart and has_cart_items:
        if 'buy_now_item' in request.session:
            del request.session['buy_now_item']
            request.session.modified = True
    
    # Check if this is a "Buy Now" checkout
    buy_now_item = request.session.get('buy_now_item')
    
    if buy_now_item:
        # BUY NOW MODE - Show only the buy_now product
        product = get_object_or_404(Product, id=buy_now_item['product_id'])
        
        # Create a temporary item structure (not saved to database)
        class TempItem:
            def __init__(self, product, quantity):
                self.id = None  # No database ID for session items
                self.product = product
                self.quantity = quantity
                self.total_price = product.price * quantity
        
        items = [TempItem(product, buy_now_item['quantity'])]
        is_buy_now = True
        
    else:
        # REGULAR CART CHECKOUT - Show all cart items
        items = cart.items.all()
        is_buy_now = False
        
        if not items:
            messages.info(request, "Your cart is empty. Add some products first!")
            return redirect("cart_page")
    
    # Calculate totals
    subtotal = sum(item.total_price for item in items)
    shipping = Decimal('50.00')
    tax = round(subtotal * Decimal('0.18'), 2)
    total = subtotal + shipping + tax
    
    profile = getattr(request.user, "profile", None)
    
    return render(request, "checkout.html", {
        "cart": cart,
        "items": items,
        "subtotal": subtotal,
        "shipping": shipping,
        "tax": tax,
        "total": total,
        "profile": profile,
        "user": request.user,
        "is_buy_now": is_buy_now,
    })


# -----------------------------
# CHECKOUT ACTION (POST)
# -----------------------------
@login_required
def checkout_action(request):
    if request.method != 'POST':
        return redirect('checkout_page')
    
    cart = get_cart(request)
    buy_now_item = request.session.get('buy_now_item')
    
    # Determine if this is Buy Now or Cart checkout
    if buy_now_item:
        # BUY NOW MODE - Process only buy_now item
        product = get_object_or_404(Product, id=buy_now_item['product_id'])
        quantity = buy_now_item['quantity']
        total_price = product.price * quantity
        
        # Create order
        order = Order.objects.create(
            user=request.user,
            total_price=total_price
        )
        
        # Create single order item
        OrderItem.objects.create(
            order=order,
            product=product,
            quantity=quantity,
            price=product.price
        )
        
        # Clear buy_now session after successful order
        del request.session['buy_now_item']
        request.session.modified = True
        
    else:
        # REGULAR CART MODE - Process all cart items
        items = cart.items.all()
        
        if not items:
            messages.error(request, "Your cart is empty!")
            return redirect("cart_page")
        
        total_price = sum(i.total_price for i in items)
        
        # Create order
        order = Order.objects.create(
            user=request.user,
            total_price=total_price
        )
        
        # Create order items from cart
        for item in items:
            OrderItem.objects.create(
                order=order,
                product=item.product,
                quantity=item.quantity,
                price=item.product.price
            )
        
        # Clear cart after order
        cart.items.all().delete()
    
    # Create shipping address (common for both)
    ShippingAddress.objects.create(
        order=order,
        full_name=request.POST.get('name', ''),
        address_line=request.POST.get('address_line', ''),
        city=request.POST.get('city', ''),
        postal_code=request.POST.get('postal_code', ''),
        country=request.POST.get('country', ''),
        phone=request.POST.get('phone', ''),
    )
    
    messages.success(request, "🎉 Order placed successfully!")
    return redirect("order_detail_page", order_id=order.id)


# -----------------------------
# ORDER DETAIL PAGE
# -----------------------------
@login_required
def order_detail_page(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    
    return render(request, "order_detail.html", {
        "order": order,
        "items": order.items.all(),
        "shipping": order.shippingaddress
    })


# -----------------------------
# TRACK ORDER PAGE
# -----------------------------
@login_required
def track_order_page(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    
    steps = {
        "processed": 1,
        "shipped": 2,
        "enroute": 3,
        "arrived": 4,
    }
    
    active_step = steps.get(order.status.lower(), 1) if hasattr(order, 'status') else 1
    
    return render(request, "track_order.html", {
        "order": order,
        "active_step": active_step
    })


# -----------------------------
# ORDER LIST PAGE
# -----------------------------
@login_required
def order_list_page(request):
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    return render(request, "order_list.html", {"orders": orders})



from django.core.mail import send_mail
from django.conf import settings
import random

# Create a model to store OTPs (add this to your models.py)
# from django.db import models
# class CheckoutOTP(models.Model):
#     user = models.ForeignKey(User, on_delete=models.CASCADE)
#     otp = models.CharField(max_length=6)
#     created_at = models.DateTimeField(auto_now_add=True)

from django.utils import timezone
from datetime import timedelta

@login_required
def send_checkout_otp(request):
    """Send OTP to user's email for checkout verification"""
    if request.method == 'POST':
        user = request.user
        otp = str(random.randint(100000, 999999))
        
        # Store OTP in session (expires in 10 minutes)
        request.session['checkout_otp'] = otp
        request.session['checkout_otp_time'] = timezone.now().isoformat()
        request.session.modified = True
        
        # Send email
        subject = "Order Verification Code"
        message = f"""
Hello {user.first_name or user.username},

Your verification code for completing your order is: {otp}

This code will expire in 10 minutes.

Do not share this code with anyone.

Thank you for shopping with us!
"""
        
        try:
            send_mail(
                subject,
                message,
                settings.EMAIL_HOST_USER,
                [user.email],
                fail_silently=False
            )
            return JsonResponse({'success': True, 'message': 'OTP sent successfully'})
        except Exception as e:
            print(f"Email error: {e}")
            return JsonResponse({'success': False, 'message': 'Failed to send OTP'})
    
    return JsonResponse({'success': False, 'message': 'Invalid request'})


@login_required
def verify_checkout_otp(request):
    """Verify OTP entered by user"""
    if request.method == 'POST':
        entered_otp = request.POST.get('otp', '')
        stored_otp = request.session.get('checkout_otp')
        otp_time_str = request.session.get('checkout_otp_time')
        
        if not stored_otp or not otp_time_str:
            return JsonResponse({'success': False, 'message': 'OTP expired. Please request a new one.'})
        
        # Check if OTP is expired (10 minutes)
        otp_time = timezone.datetime.fromisoformat(otp_time_str)
        if timezone.is_naive(otp_time):
            otp_time = timezone.make_aware(otp_time)
        
        if timezone.now() - otp_time > timedelta(minutes=10):
            return JsonResponse({'success': False, 'message': 'OTP expired. Please request a new one.'})
        
        # Verify OTP
        if entered_otp == stored_otp:
            # Mark OTP as verified
            request.session['otp_verified'] = True
            request.session.modified = True
            return JsonResponse({'success': True, 'message': 'OTP verified successfully'})
        else:
            return JsonResponse({'success': False, 'message': 'Invalid OTP. Please try again.'})
    
    return JsonResponse({'success': False, 'message': 'Invalid request'})