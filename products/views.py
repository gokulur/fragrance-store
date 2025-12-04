from django.shortcuts import render, get_object_or_404
from .models import Product, Category, Collection
from django.core.paginator import Paginator
from decimal import Decimal
from django.http import JsonResponse

def all_collections(request):
    categories = Category.objects.all()
    for category in categories:
        category.available_count = category.products.filter(available=True).count()
    return render(request, 'all_collections.html', {'categories': categories})

def product_list(request):
    products = Product.objects.all()
    paginator = Paginator(products, 12)   
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'product_list.html', {'page_obj': page_obj})

def product_detail(request, slug):
    product = get_object_or_404(Product, slug=slug, available=True)
    return render(request, 'product_detail.html', {'product': product})

def products_by_category(request, slug):
    """Category page with ALL FILTERS - AJAX VERSION"""
    category = get_object_or_404(Category, slug=slug)
    
    # Get all collections under this category
    collections_in_category = Collection.objects.filter(category=category)
    
    # Start with products in this category that are available
    products = Product.objects.filter(category=category, available=True)
    
    # Get all categories for sidebar
    all_categories = Category.objects.all()
    
    # ============================================
    # COLLECTION FILTER
    # ============================================
    selected_collection_ids = request.GET.getlist('collection')
    if selected_collection_ids:
        products = products.filter(collection_id__in=selected_collection_ids)
    
    # ============================================
    # PRICE FILTER
    # ============================================
    price_min = request.GET.get('price_min')
    price_max = request.GET.get('price_max')
    
    if price_min:
        try:
            products = products.filter(price__gte=Decimal(price_min))
        except:
            pass
    
    if price_max:
        try:
            products = products.filter(price__lte=Decimal(price_max))
        except:
            pass
    
    # ============================================
    # SORTING
    # ============================================
    sort_by = request.GET.get('sort_by', 'manual')
    
    if sort_by == 'best-selling':
        products = products.order_by('-created_at')
    elif sort_by == 'title-ascending':
        products = products.order_by('name')
    elif sort_by == 'title-descending':
        products = products.order_by('-name')
    elif sort_by == 'price-ascending':
        products = products.order_by('price')
    elif sort_by == 'price-descending':
        products = products.order_by('-price')
    elif sort_by == 'created-ascending':
        products = products.order_by('created_at')
    elif sort_by == 'created-descending':
        products = products.order_by('-created_at')
    else:
        products = products.order_by('-created_at')
    
    # ============================================
    # PAGINATION
    # ============================================
    paginator = Paginator(products, 12)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    # Get price range for slider
    all_category_products = Product.objects.filter(category=category, available=True)
    min_price_product = all_category_products.order_by('price').first()
    max_price_product = all_category_products.order_by('-price').first()
    
    context = {
        'products': page_obj,
        'page_obj': page_obj,
        'category': category,
        'collections': collections_in_category,
        'categories': all_categories,
        'sort_by': sort_by,
        'price_min': price_min or (min_price_product.price if min_price_product else 0),
        'price_max': price_max or (max_price_product.price if max_price_product else 1000),
        'min_price_range': min_price_product.price if min_price_product else 0,
        'max_price_range': max_price_product.price if max_price_product else 1000,
        'selected_collections': selected_collection_ids,
    }
    
    # Check if it's an AJAX request
    if request.GET.get('ajax'):
        # Return only the template without base
        return render(request, 'products_by_category.html', context)
    
    return render(request, 'products_by_category.html', context)

def products_by_collection(request, slug):
    """Collection page with filters - AJAX VERSION"""
    collection = get_object_or_404(Collection, slug=slug)
    
    # Get products in this collection that are available
    products = Product.objects.filter(collection=collection, available=True)
    
    # Get category of this collection
    category = collection.category
    
    # Get all collections in same category
    collections_in_category = Collection.objects.filter(category=category) if category else Collection.objects.all()
    
    # Get all categories
    all_categories = Category.objects.all()
    
    # ============================================
    # PRICE FILTER
    # ============================================
    price_min = request.GET.get('price_min')
    price_max = request.GET.get('price_max')
    
    if price_min:
        try:
            products = products.filter(price__gte=Decimal(price_min))
        except:
            pass
    
    if price_max:
        try:
            products = products.filter(price__lte=Decimal(price_max))
        except:
            pass
    
    # ============================================
    # SORTING
    # ============================================
    sort_by = request.GET.get('sort_by', 'manual')
    
    if sort_by == 'best-selling':
        products = products.order_by('-created_at')
    elif sort_by == 'title-ascending':
        products = products.order_by('name')
    elif sort_by == 'title-descending':
        products = products.order_by('-name')
    elif sort_by == 'price-ascending':
        products = products.order_by('price')
    elif sort_by == 'price-descending':
        products = products.order_by('-price')
    elif sort_by == 'created-ascending':
        products = products.order_by('created_at')
    elif sort_by == 'created-descending':
        products = products.order_by('-created_at')
    else:
        products = products.order_by('-created_at')
    
    # ============================================
    # PAGINATION
    # ============================================
    paginator = Paginator(products, 12)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    # Get price range
    all_collection_products = Product.objects.filter(collection=collection, available=True)
    min_price_product = all_collection_products.order_by('price').first()
    max_price_product = all_collection_products.order_by('-price').first()
    
    context = {
        'products': page_obj,
        'page_obj': page_obj,
        'collection': collection,
        'category': category,
        'collections': collections_in_category,
        'categories': all_categories,
        'sort_by': sort_by,
        'price_min': price_min or (min_price_product.price if min_price_product else 0),
        'price_max': price_max or (max_price_product.price if max_price_product else 1000),
        'min_price_range': min_price_product.price if min_price_product else 0,
        'max_price_range': max_price_product.price if max_price_product else 1000,
    }
    
    # Check if it's an AJAX request
    if request.GET.get('ajax'):
        return render(request, 'products_by_category.html', context)
    
    return render(request, 'products_by_category.html', context)




