from django.shortcuts import render
from products.models import Product, Collection
from cart.models import Cart
import random

def home(request):
    # Get random 8 products for main display
    product_ids = list(Product.objects.values_list('id', flat=True))
    random.shuffle(product_ids)
    selected_ids = product_ids[:8]
    products = list(Product.objects.filter(id__in=selected_ids))
    products.sort(key=lambda p: selected_ids.index(p.id))
    
    # Get recommended products (works for both authenticated and unauthenticated users)
    recommended_products = []
    if request.user.is_authenticated:
        cart = Cart.objects.filter(user=request.user).first()
        if cart:
            # Exclude products already in cart
            cart_product_ids = cart.items.values_list('product_id', flat=True)
            recommended_products = list(
                Product.objects.exclude(id__in=cart_product_ids)
                .filter(available=True)[:8]
            )
        else:
            # Authenticated user but no cart - show random products
            recommended_products = list(
                Product.objects.filter(available=True)[:8]
            )
    else:
        # Unauthenticated user - show random available products
        recommended_products = list(
            Product.objects.filter(available=True)[:8]
        )
    
    # Shuffle and limit to 4 products
    random.shuffle(recommended_products)
    recommended_products = recommended_products[:4]
    
    # Get collections
    collections = Collection.objects.all()[:6]
    
    return render(request, 'base.html', {
        'products': products,
        'collections': collections,
        'recommended_products': recommended_products
    })



def about(request):
    return render(request, 'about.html')

def contact(request):
    return render(request, 'contact.html')