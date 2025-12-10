from .models import Cart
from .views import get_cart  # import your get_cart function

def cart_data(request):
    cart = get_cart(request)
    if cart:
        subtotal = cart.get_subtotal if hasattr(cart, 'get_subtotal') else 0
        total = cart.get_total if hasattr(cart, 'get_total') else 0
        count = cart.items.count() if hasattr(cart, 'items') else 0

        return {
            "cart": cart,
            "cart_subtotal": subtotal,
            "cart_total": total,
            "cart_count": count,
        }

    return {
        "cart": None,
        "cart_subtotal": 0,
        "cart_total": 0,
        "cart_count": 0,
    }
