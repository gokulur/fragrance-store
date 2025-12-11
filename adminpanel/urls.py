from django.urls import path
from . import views  

urlpatterns = [
    # Dashboard
    path('dashboard/', views.admin_dashboard, name='admin_dashboard'),
    


    # Products
    path('products/', views.product_list, name='admin_product_list'),
    path('products/add/', views.product_add, name='admin_product_add'),
    path('products/edit/<int:pk>/', views.product_edit, name='admin_product_edit'),
    path('products/delete/<int:pk>/', views.product_delete, name='admin_product_delete'),

    # Orders
    path('orders/', views.order_list, name='admin_order_list'),
 

    # Collections
    path('collections/', views.collection_list, name='collection_list'),
    path('collections/add/', views.collection_add, name='collection_add'),
    path('collections/edit/<int:pk>/', views.collection_edit, name='collection_edit'),
    path('collections/delete/<int:pk>/', views.collection_delete, name='collection_delete'),

    # Categories
    path('categories/', views.category_list, name='category_list'),
    path('categories/add/', views.category_add, name='category_add'),
    path('categories/edit/<int:pk>/', views.category_edit, name='category_edit'),
    path('categories/delete/<int:pk>/', views.category_delete, name='category_delete'),

    # Customers
    path('customers/', views.admin_customers, name='admin_customers'),
    path('admin/customer/<int:customer_id>/delete/', views.admin_delete_customer, name='admin_delete_customer'),
    # invoices and receipts
    path('invoices/<int:pk>/', views.invoice, name='invoice'),
    path('receipts/<int:pk>/', views.receipt, name='receipt'),
    path("order/<str:order_id>/update-status/", views.update_status_inline, name="update_status_inline"),

]
