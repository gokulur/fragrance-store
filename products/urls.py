# products/urls.py - COMPLETE FILE - COPY PASTE THIS ENTIRE FILE
from django.urls import path
from . import views

urlpatterns = [
    path('all_collections/', views.all_collections, name='all_collections'),
    path('category/<slug:slug>/', views.products_by_category, name='product_by_category'),
    path('collection/<slug:slug>/', views.products_by_collection, name='product_by_collection'),
    path('<slug:slug>/', views.product_detail, name='product_detail'),
    
]