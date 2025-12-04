from django.urls import path
from . import views

urlpatterns = [
    # Checkout
    path('checkout/', views.checkout_page, name='checkout_page'),
    path('checkout/action/', views.checkout_action, name='checkout_action'),
    
    # Buy Now
    path('buy-now/<int:product_id>/', views.buy_now, name='buy_now'),
    path('update-buy-now/<str:action>/', views.update_buy_now_quantity, name='update_buy_now_qty'),
    path('cancel-buy-now/', views.cancel_buy_now, name='cancel_buy_now'),
    
    # Orders
    path('orders/', views.order_list_page, name='order_list_page'),
    path('order/<str:order_id>/', views.order_detail_page, name='order_detail_page'),
    path('order/<str:order_id>/track/', views.track_order_page, name='track_order_page'),
    
    path('send-checkout-otp/', views.send_checkout_otp, name='send_checkout_otp'),
    path('verify-checkout-otp/', views.verify_checkout_otp, name='verify_checkout_otp'),
 
    # Cancel Order
    path('cancel/<str:order_id>/', views.cancel_order, name='cancel_order'),
    
    # Update Order
    path('update/<str:order_id>/', views.update_order, name='update_order'),

]