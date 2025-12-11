from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils.text import slugify
from django.contrib.auth.models import User
from products.models import Product, Collection, Category,ProductImage
from orders.models import Order
from django.db.models import Sum
from django.utils.timezone import now, timedelta
from django.http import JsonResponse

# -------------------------------
# Access Control
# -------------------------------
def admin_only(user):
    return user.is_superuser or user.is_staff


# -------------------------------
# Dashboard
# -------------------------------
@login_required
@user_passes_test(admin_only)
def admin_dashboard(request):

    today = now().date()
    month_start = today.replace(day=1)

    # Daily Income
    daily_income = Order.objects.filter(created_at__date=today).aggregate(
        total=Sum('total_price')
    )['total'] or 0

    # Monthly Income
    monthly_income = Order.objects.filter(created_at__date__gte=month_start).aggregate(
        total=Sum('total_price')
    )['total'] or 0

    # Revenue (All order amount)
    revenue = Order.objects.aggregate(total=Sum('total_price'))['total'] or 0

    # Sales (Number of orders)
    sales = Order.objects.count()

    context = {
        'daily_income': daily_income,
        'monthly_income': monthly_income,
        'revenue': revenue,
        'sales': sales,
    }
    return render(request, 'admin_dashboard.html', context)

 


# -------------------------------
# PRODUCT MANAGEMENT
# -------------------------------
@login_required
@user_passes_test(admin_only)
def product_list(request):
    products = Product.objects.select_related('collection', 'category').all()
    return render(request, 'product_list.html', {'products': products})


@login_required
@user_passes_test(admin_only)
def product_add(request):
    collections = Collection.objects.all()
    categories = Category.objects.all()

    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description')
        price = request.POST.get('price')
        stock = request.POST.get('stock', 0)
        available = request.POST.get('available') == "True"
        category_id = request.POST.get('category')
        collection_id = request.POST.get('collection')

        category = Category.objects.get(id=category_id) if category_id else None
        collection = Collection.objects.get(id=collection_id) if collection_id else None

        # Create product
        product = Product.objects.create(
            name=name,
            slug=slugify(name),
            description=description,
            price=price,
            stock=stock,
            available=available,
            category=category,
            collection=collection,
        )

        # Multiple images
        images = request.FILES.getlist('images')
        for image in images:
            ProductImage.objects.create(product=product, image=image)

        messages.success(request, "Product added successfully!")
        return redirect('admin_product_list')

    return render(request, 'product_form.html', {
        'collections': collections,
        'categories': categories
    })


 
@login_required
@user_passes_test(admin_only)
def product_edit(request, pk):
    product = get_object_or_404(Product, pk=pk)
    collections = Collection.objects.all()
    categories = Category.objects.all()

    if request.method == 'POST':
        product.name = request.POST.get('name')
        product.description = request.POST.get('description')
        product.price = request.POST.get('price')
        product.stock = request.POST.get('stock', 0)
        product.available = request.POST.get('available') == "True"
        product.category_id = request.POST.get('category') or None
        product.collection_id = request.POST.get('collection') or None
        product.slug = slugify(product.name)
        product.save()

        # New images (append to gallery)
        images = request.FILES.getlist('images')
        for image in images:
            ProductImage.objects.create(product=product, image=image)

        messages.success(request, "Product updated successfully!")
        return redirect('admin_product_list')

    return render(request, 'product_form.html', {
        'product': product,
        'collections': collections,
        'categories': categories
    })


@login_required
@user_passes_test(admin_only)
def product_delete(request, pk):
    product = get_object_or_404(Product, pk=pk)
    product.delete()
    messages.success(request, "Product deleted successfully!")
    return redirect('admin_product_list')


# -------------------------------
# ORDER MANAGEMENT
# -------------------------------
@login_required
@user_passes_test(admin_only)
def order_list(request):
    orders = Order.objects.select_related('user').all()
    return render(request, 'admin_order_list.html', {'orders': orders})


 


# -------------------------------
# COLLECTION MANAGEMENT
# -------------------------------
@login_required
@user_passes_test(admin_only)
def collection_list(request):
    collections = Collection.objects.select_related('category').all().order_by('-created_at')
    return render(request, 'collection_lists.html', {'collections': collections})


@login_required
@user_passes_test(admin_only)
def collection_add(request):
    categories = Category.objects.all()

    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description')
        image = request.FILES.get('image')
        category_id = request.POST.get('category')

        if not name:
            messages.error(request, "Name is required.")
            return redirect('collection_add')

        category = Category.objects.get(id=category_id) if category_id else None

        Collection.objects.create(
            name=name,
            slug=slugify(name),
            description=description,
            image=image,
            category=category
        )
        messages.success(request, f"Collection '{name}' added successfully!")
        return redirect('collection_list')

    return render(request, 'collection_add.html', {'categories': categories})


@login_required
@user_passes_test(admin_only)
def collection_edit(request, pk):
    collection = get_object_or_404(Collection, pk=pk)
    categories = Category.objects.all()

    if request.method == 'POST':
        collection.name = request.POST.get('name')
        collection.description = request.POST.get('description')
        collection.category_id = request.POST.get('category') or None
        if request.FILES.get('image'):
            collection.image = request.FILES.get('image')
        collection.slug = slugify(collection.name)
        collection.save()
        messages.success(request, f"Collection '{collection.name}' updated successfully!")
        return redirect('collection_list')

    return render(request, 'collection_add.html', {'collection': collection, 'categories': categories})


@login_required
@user_passes_test(admin_only)
def collection_delete(request, pk):
    collection = get_object_or_404(Collection, pk=pk)
    collection.delete()
    messages.success(request, "Collection deleted successfully.")
    return redirect('collection_list')


# -------------------------------
# CATEGORY MANAGEMENT
# -------------------------------
@login_required
@user_passes_test(admin_only)
def category_list(request):
    categories = Category.objects.all().order_by('-created_at')
    return render(request, 'category_list.html', {'categories': categories})

@login_required
@user_passes_test(admin_only)
def category_add(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        image = request.FILES.get('image')

        if not name:
            messages.error(request, "Name is required.")
            return redirect('category_add')

        category = Category.objects.create(
            name=name,
            slug=slugify(name),
            image=image
        )
        messages.success(request, f"Category '{name}' added successfully!")
        return redirect('category_list')

    return render(request, 'category_add.html')


@login_required
@user_passes_test(admin_only)
def category_edit(request, pk):
    category = get_object_or_404(Category, pk=pk)
    if request.method == 'POST':
        category.name = request.POST.get('name')
        if request.FILES.get('image'):
            category.image = request.FILES.get('image')
        category.slug = slugify(category.name)
        category.save()
        messages.success(request, f"Category '{category.name}' updated successfully!")
        return redirect('category_list')
    return render(request, 'category_add.html', {'category': category})


@login_required
@user_passes_test(admin_only)
def category_delete(request, pk):
    category = get_object_or_404(Category, pk=pk)
    category.delete()
    messages.success(request, "Category deleted successfully.")
    return redirect('category_list')


# -------------------------------
# CUSTOMERS
# -------------------------------
@login_required
@user_passes_test(admin_only)
def admin_customers(request):
    customers = User.objects.filter(is_superuser=False).order_by('-date_joined')
    return render(request, 'admin_customers.html', {'customers': customers})

from decimal import Decimal

@login_required
@user_passes_test(admin_only)
def invoice(request, pk):
    order = get_object_or_404(Order, pk=pk)

    # Order items
    items = order.items.all()

    # Subtotal (same as checkout)
    subtotal = sum(item.price * item.quantity for item in items)

    # Shipping (fixed like checkout page)
    shipping = Decimal('50.00')

    # Tax (18% same as checkout page)
    tax = round(subtotal * Decimal('0.18'), 2)

    # Total final
    total = subtotal + shipping + tax

    context = {
        "order": order,
        "items": items,
        "subtotal": subtotal,
        "shipping": shipping,
        "tax": tax,
        "total": total,
    }

    return render(request, "invoice.html", context)



@login_required
@user_passes_test(admin_only)
def receipt(request, pk):
    order = get_object_or_404(Order, pk=pk)

    items = order.items.all() if hasattr(order, "items") else []

    # Subtotal
    subtotal = sum(item.price * item.quantity for item in items)

    # Shipping fixed (same as checkout)
    shipping = Decimal('50.00')

    # Tax 18% (same as checkout)
    tax = round(subtotal * Decimal('0.18'), 2)

    # Total
    total = subtotal + shipping + tax

    context = {
        "order": order,
        "items": items,
        "customer": order.user,
        "subtotal": subtotal,
        "shipping": shipping,
        "tax": tax,
        "total": total,
        "order_date": order.created_at,
    }

    return render(request, "receipt.html", context)



@login_required
@user_passes_test(admin_only)
def update_status_inline(request, order_id):
    order = get_object_or_404(Order, order_id=order_id)

    if request.method == "POST":
        new_status = request.POST.get("status")

        if new_status not in ['processing', 'shipped', 'delivered']:
            messages.error(request, "Invalid status!")
            return redirect("orders_list")   

        order.status = new_status
        order.save()
        messages.success(request, "Order status updated!")
        return redirect(request.META.get("HTTP_REFERER", "/"))
    


@login_required
@user_passes_test(admin_only)
def admin_delete_customer(request, customer_id):
    """
    Delete a customer and all their related data
    """
    customer = get_object_or_404(User, id=customer_id)
    
    # Prevent deleting yourself
    if customer.id == request.user.id:
        messages.error(request, "❌ You cannot delete your own account!")
        return redirect('admin_customers')
    
    # Get customer info for confirmation message
    customer_username = customer.username
    customer_email = customer.email
    
    # Delete customer (this also deletes related data via CASCADE)
    customer.delete()
    
    # Show success message
    messages.success(
        request, 
        f"✅ Customer '{customer_username}' ({customer_email}) has been deleted successfully!"
    )
    
    return redirect('admin_customers')