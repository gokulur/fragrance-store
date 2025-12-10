from django.shortcuts import redirect, get_object_or_404,render
from django.contrib.auth.decorators import login_required
from products.models import Product
from .models import Wishlist
from django.http import JsonResponse
from django.views.decorators.http import require_POST

 
def wishlist_page(request):

    if request.user.is_authenticated:
        wishlist, created = Wishlist.objects.get_or_create(user=request.user)
        products = wishlist.products.all()
    else:
        session_wishlist = request.session.get("wishlist", [])
        products = Product.objects.filter(id__in=session_wishlist)

    return render(request, 'wishlist.html', {
        'products': products
    })

# @login_required
# def toggle_wishlist(request, product_id):
#     product = get_object_or_404(Product, id=product_id)
#     wishlist, created = Wishlist.objects.get_or_create(user=request.user)

#     if product in wishlist.products.all():
#         wishlist.products.remove(product)
#     else:
#         wishlist.products.add(product)
#     return redirect(request.META.get('HTTP_REFERER', '/'))



# @login_required
# @require_POST
# def toggle_wishlist(request, product_id):
#     product = get_object_or_404(Product, id=product_id)
#     wishlist, created = Wishlist.objects.get_or_create(user=request.user)

#     if product in wishlist.products.all():
#         wishlist.products.remove(product)
#         added = False
#     else:
#         wishlist.products.add(product)
#         added = True

#     return JsonResponse({
#         "added": added,
#         "wishlist_count": request.user.wishlist.products.count()
#     })
from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from .models import Product, Wishlist

def toggle_wishlist(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    # ----------------------------------------
    # If user is logged in
    # ----------------------------------------
    if request.user.is_authenticated:
        wishlist, created = Wishlist.objects.get_or_create(user=request.user)
        if product in wishlist.products.all():
            wishlist.products.remove(product)
            added = False
        else:
            wishlist.products.add(product)
            added = True
        count = wishlist.products.count()
    
    # ----------------------------------------
    # Guest user - store wishlist in session
    # ----------------------------------------
    else:
        session_wishlist = request.session.get('wishlist', [])
        product_id_str = str(product.id)

        if product_id_str in session_wishlist:
            session_wishlist.remove(product_id_str)
            added = False
        else:
            session_wishlist.append(product_id_str)
            added = True

        request.session['wishlist'] = session_wishlist
        request.session.modified = True
        count = len(session_wishlist)

    return JsonResponse({
        "added": added,
        "wishlist_count": count
    })



