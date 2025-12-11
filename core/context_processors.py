from cart.models import Cart
from wishlist.models import Wishlist
from products.models import Product
import random 

def cart_count(request):
    if request.user.is_authenticated:
        try:
            cart = Cart.objects.get(user=request.user)
            return {"cart_count": cart.items.count()}
        except Cart.DoesNotExist:
            return {"cart_count": 0}
    return {"cart_count": 0}


 

def wishlist_count(request):
    if request.user.is_authenticated:
        try:
            wishlist = Wishlist.objects.get(user=request.user)
            return {"wishlist_count": wishlist.products.count()}
        except Wishlist.DoesNotExist:
            return {"wishlist_count": 0}
    return {"wishlist_count": 0}


def recommended_products(request):
    """
    Return recommended products for ALL users.
    - Authenticated users: Shows products NOT in their cart
    - Non-authenticated users: Shows random available products
    """
    recommended_products_list = []
    
    if request.user.is_authenticated:
        try:
            cart = Cart.objects.get(user=request.user)
            
            # Get product IDs in user's cart
            cart_product_ids = list(cart.items.values_list('product_id', flat=True))
            
            if cart_product_ids:
                # Get available products not in cart
                recommended_products_list = list(
                    Product.objects.exclude(id__in=cart_product_ids)
                    .filter(available=True)
                    .order_by('?')[:8]  # Random order, get 8
                )
            else:
                # Cart is empty, show random products
                recommended_products_list = list(
                    Product.objects.filter(available=True)
                    .order_by('?')[:8]
                )
                
        except Cart.DoesNotExist:
            # If no cart exists, show random available products
            recommended_products_list = list(
                Product.objects.filter(available=True)
                .order_by('?')[:8]
            )
    else:
        # For NON-AUTHENTICATED users, show random products
        recommended_products_list = list(
            Product.objects.filter(available=True)
            .order_by('?')[:8]
        )
    
    # Shuffle for variety
    random.shuffle(recommended_products_list)
    
    # Return only 4 products for the carousel
    return {"recommended_products": recommended_products_list[:4]}
