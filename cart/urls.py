from django.urls import path
from . import views

urlpatterns = [
    path('cart/', views.cart_page, name='cart_page'),
    path('cart/add/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/increase/<int:item_id>/', views.increase_qty, name='increase_qty'),
    path('cart/decrease/<int:item_id>/', views.decrease_qty, name='decrease_qty'),
    path('cart/remove/<int:item_id>/', views.remove_item, name='remove_item'),
    
]