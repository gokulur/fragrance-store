from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
import random

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
    
    request.session['buy_now_item'] = {
        'product_id': product.id,
        'quantity': qty
    }
    request.session.modified = True
    
    return redirect("checkout_page")


# -----------------------------
# UPDATE BUY NOW QUANTITY (AJAX)
# -----------------------------
@login_required
def update_buy_now_quantity(request, action):
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
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
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
    if 'buy_now_item' in request.session:
        del request.session['buy_now_item']
        request.session.modified = True
    
    return redirect(request.META.get('HTTP_REFERER', 'home'))


# -----------------------------
# CHECKOUT PAGE (GET)
# -----------------------------
@login_required
def checkout_page(request):
    cart = get_cart(request)
    
    from_cart = request.GET.get('from') == 'cart'
    has_cart_items = cart.items.exists()
    
    if from_cart and has_cart_items:
        if 'buy_now_item' in request.session:
            del request.session['buy_now_item']
            request.session.modified = True
    
    buy_now_item = request.session.get('buy_now_item')
    
    if buy_now_item:
        product = get_object_or_404(Product, id=buy_now_item['product_id'])
        
        class TempItem:
            def __init__(self, product, quantity):
                self.id = None
                self.product = product
                self.quantity = quantity
                self.total_price = product.price * quantity
        
        items = [TempItem(product, buy_now_item['quantity'])]
        is_buy_now = True
        
    else:
        items = cart.items.all()
        is_buy_now = False
        
        if not items:
            messages.info(request, "Your cart is empty. Add some products first!")
            return redirect("cart_page")
    
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
# SEND OTP FOR CHECKOUT
# -----------------------------
@login_required
def send_checkout_otp(request):
    """Send OTP to user's email for checkout verification"""
    if request.method == 'POST':
        user = request.user
        
        # Generate 6-digit OTP
        otp = str(random.randint(100000, 999999))
        
        # Store OTP in session (expires in 10 minutes)
        request.session['checkout_otp'] = otp
        request.session['checkout_otp_time'] = timezone.now().isoformat()
        request.session['otp_verified'] = False
        request.session.modified = True
        
        # Email content
        subject = "🔐 Order Verification Code"
        message = f"""
Hello {user.first_name or user.username},

Your verification code for completing your order is:

{otp}

⏰ This code will expire in 10 minutes.
🔒 Do not share this code with anyone.

Thank you for shopping with us!

Best regards,
Your Store Team
"""
        
        try:
            send_mail(
                subject,
                message,
                settings.EMAIL_HOST_USER,
                [user.email],
                fail_silently=False
            )
            return JsonResponse({
                'success': True, 
                'message': f'OTP sent to {user.email}'
            })
        except Exception as e:
            print(f"❌ Email error: {e}")
            return JsonResponse({
                'success': False, 
                'message': 'Failed to send OTP. Please check your email settings.'
            })
    
    return JsonResponse({'success': False, 'message': 'Invalid request method'})


# -----------------------------
# VERIFY OTP
# -----------------------------
@login_required
def verify_checkout_otp(request):
    """Verify OTP entered by user"""
    if request.method == 'POST':
        entered_otp = request.POST.get('otp', '').strip()
        stored_otp = request.session.get('checkout_otp')
        otp_time_str = request.session.get('checkout_otp_time')
        
        print(f"🔍 Entered OTP: {entered_otp}")
        print(f"🔍 Stored OTP: {stored_otp}")
        
        # Check if OTP exists
        if not stored_otp or not otp_time_str:
            return JsonResponse({
                'success': False, 
                'message': 'OTP expired. Please request a new one.'
            })
        
        # Check if OTP is expired (10 minutes)
        try:
            otp_time = timezone.datetime.fromisoformat(otp_time_str)
            if timezone.is_naive(otp_time):
                otp_time = timezone.make_aware(otp_time)
            
            if timezone.now() - otp_time > timedelta(minutes=10):
                # Clear expired OTP
                request.session['checkout_otp'] = None
                request.session.modified = True
                return JsonResponse({
                    'success': False, 
                    'message': 'OTP expired. Please request a new one.'
                })
        except Exception as e:
            print(f"❌ OTP time error: {e}")
            return JsonResponse({
                'success': False, 
                'message': 'Invalid OTP session. Please try again.'
            })
        
        # Verify OTP
        if entered_otp == stored_otp:
            # Mark OTP as verified
            request.session['otp_verified'] = True
            request.session.modified = True
            
            print("✅ OTP Verified successfully!")
            
            return JsonResponse({
                'success': True, 
                'message': 'OTP verified successfully!'
            })
        else:
            print("❌ Invalid OTP")
            return JsonResponse({
                'success': False, 
                'message': 'Invalid OTP. Please try again.'
            })
    
    return JsonResponse({'success': False, 'message': 'Invalid request method'})


# -----------------------------
# CHECKOUT ACTION (POST) - WITH OTP CHECK
# -----------------------------
@login_required
def checkout_action(request):
    if request.method != 'POST':
        return redirect('checkout_page')
    
   
    if not request.session.get('otp_verified', False):
        messages.error(request, "⚠️ Please verify OTP before placing order!")
        return redirect('checkout_page')
    
    cart = get_cart(request)
    buy_now_item = request.session.get('buy_now_item')
    
    # Determine if this is Buy Now or Cart checkout
    if buy_now_item:
        # BUY NOW MODE
        product = get_object_or_404(Product, id=buy_now_item['product_id'])
        quantity = buy_now_item['quantity']
        
        # Check stock
        if quantity > product.stock:
            messages.error(request, f"Only {product.stock} items available!")
            return redirect('checkout_page')
        
        total_price = product.price * quantity
        
        # Create order
        order = Order.objects.create(
            user=request.user,
            total_price=total_price
        )
        
        # Create order item
        OrderItem.objects.create(
            order=order,
            product=product,
            quantity=quantity,
            price=product.price
        )
        
        # Reduce stock
        product.stock -= quantity
        product.save()
        
        # Clear buy_now session
        del request.session['buy_now_item']
        request.session.modified = True
        
    else:
        # CART MODE
        items = cart.items.all()
        
        if not items:
            messages.error(request, "Your cart is empty!")
            return redirect("cart_page")
        
        # Check stock for all items
        for item in items:
            if item.quantity > item.product.stock:
                messages.error(request, f"Only {item.product.stock} of {item.product.name} available!")
                return redirect('checkout_page')
        
        total_price = sum(i.total_price for i in items)
        
        # Create order
        order = Order.objects.create(
            user=request.user,
            total_price=total_price
        )
        
        # Create order items and reduce stock
        for item in items:
            OrderItem.objects.create(
                order=order,
                product=item.product,
                quantity=item.quantity,
                price=item.product.price
            )
            
            # Reduce stock
            item.product.stock -= item.quantity
            item.product.save()
        
        # Clear cart
        cart.items.all().delete()
    
    # Create shipping address
    ShippingAddress.objects.create(
        order=order,
        full_name=request.POST.get('name', ''),
        address_line=request.POST.get('address_line', ''),
        city=request.POST.get('city', ''),
        postal_code=request.POST.get('postal_code', ''),
        country=request.POST.get('country', ''),
        phone=request.POST.get('phone', ''),
        delivery_latitude=request.POST.get('delivery_latitude') or None,
        delivery_longitude=request.POST.get('delivery_longitude') or None,
    )
    
    # ✅ SEND ADMIN EMAIL - ADD THIS LINE
    try:
        send_admin_order_email(order)
    except Exception as e:
        print(f"❌ Failed to send admin email: {e}")
    
    # Clear OTP session
    request.session['otp_verified'] = False
    request.session['checkout_otp'] = None
    request.session.modified = True
    
    messages.success(request, "🎉 Order placed successfully!")
    return redirect("order_detail_page", order_id=order.order_id)



# -----------------------------
# ORDER DETAIL PAGE
# -----------------------------
@login_required
def order_detail_page(request, order_id):
    order = get_object_or_404(Order, order_id=order_id, user=request.user)
    
    # ✅ FIX: Use item instead of order to avoid variable shadowing
    subtotal = sum(item.total_price for item in order.items.all())
    # OR use the order's total_price directly if it's the subtotal:
    # subtotal = order.total_price
    
    shipping = Decimal('50.00')
    tax = round(subtotal * Decimal('0.18'), 2)
    total = subtotal + shipping + tax
    
    return render(request, "order_detail.html", {
        "order": order,
        "items": order.items.all(),
        "shipping": order.shippingaddress,
        "subtotal": subtotal,
        "shipping_cost": shipping,
        "tax": tax,
        "total": total,
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


def send_admin_order_email(order):
    """Send entire order details to admin email automatically"""

    admin_email = "shyamchandgemini@gmail.com"   

    order_items = order.items.all()
    shipping = order.shippingaddress

  
    items_text = ""
    for item in order_items:
        items_text += (
            f"- {item.product.name} | Qty: {item.quantity} | "
            f"Price: ₹{item.price} | Total: ₹{item.total_price}\n"
        )

 
    message = f"""
A new order has been placed!

===============================
🧾 ORDER SUMMARY
===============================
Order ID: {order.order_id}
User: {order.user.username}
Date: {order.created_at.strftime('%d-%m-%Y %H:%M')}
Total Amount: ₹{order.total_price}

===============================
📦 ITEMS
===============================
{items_text}

===============================
📍 SHIPPING INFO
===============================
Name: {shipping.full_name}
Address: {shipping.address_line}
City: {shipping.city}
Postal Code: {shipping.postal_code}
Country: {shipping.country}
Phone: {shipping.phone}

Please process this order.
"""

    send_mail(
        subject=f"📦 New Order Received – #{order.order_id}",
        message=message,
        from_email=settings.EMAIL_HOST_USER, 
        recipient_list=[admin_email],           
        fail_silently=False,
    )
