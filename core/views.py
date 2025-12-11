from django.shortcuts import render
from products.models import Product, Collection
from cart.models import Cart
import random

def home(request):
    # Get 8 random products for main section
    product_ids = list(Product.objects.values_list('id', flat=True))
    random.shuffle(product_ids)
    selected_ids = product_ids[:8]
    products = list(Product.objects.filter(id__in=selected_ids))
    products.sort(key=lambda p: selected_ids.index(p.id))
    
    # Get collections
    collections = Collection.objects.all()[:6]
    
    # DON'T set recommended_products here - let context processor handle it
    # The context processor will automatically provide recommended_products
    
    return render(request, 'base.html', {
        'products': products,
        'collections': collections,
        # recommended_products comes from context_processors.py automatically
    })



def about(request):
    return render(request, 'about.html')

def contact(request):
    return render(request, 'contact.html')