from cart.models import Cart

def cart_data(request):
    if request.user.is_authenticated:
        cart, created = Cart.objects.get_or_create(user=request.user)
        subtotal = cart.get_subtotal
        total = cart.get_total
        count = cart.items.count()

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
