from django.db import models
from django.contrib.auth.models import User
from products.models import Product
import secrets
from django.utils import timezone

class Order(models.Model):
    STATUS_CHOICES = [
        ('processing', 'Processing'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
    ]
    
    order_id = models.CharField(max_length=20, unique=True, null=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='processing'
    )
    
    # NEW FIELDS for tracking status changes
    delivered_at = models.DateTimeField(null=True, blank=True)
    shipped_at = models.DateTimeField(null=True, blank=True)
    
    def save(self, *args, **kwargs):
        # Generate order_id if not exists
        if not self.order_id:
            self.order_id = self.generate_order_id()
        
        # Track status changes
        if self.pk:  # Only for existing orders
            old_order = Order.objects.get(pk=self.pk)
            
            # If status changed to 'delivered', set delivered_at
            if old_order.status != 'delivered' and self.status == 'delivered':
                self.delivered_at = timezone.now()
            
            # If status changed to 'shipped', set shipped_at
            if old_order.status != 'shipped' and self.status == 'shipped':
                self.shipped_at = timezone.now()
        
        super().save(*args, **kwargs)
    
    def generate_order_id(self):
        code = ''.join(secrets.choice('ABCDEFGHJKLMNPQRSTUVWXYZ23456789') for _ in range(8))
        return f"RZ-{code}"
    
    def __str__(self):
        return self.order_id
    
    @property
    def total_quantity(self):
        return sum(item.quantity for item in self.items.all())


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True)
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    
    @property
    def total_price(self):
        """Calculate total price for this order item"""
        return self.quantity * self.price
    
    def get_total(self):
        return self.quantity * self.price
    
    def __str__(self):
        return f"{self.product} x {self.quantity}"


class ShippingAddress(models.Model):
    order = models.OneToOneField(Order, on_delete=models.CASCADE)
    full_name = models.CharField(max_length=100)
    address_line = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20)
    country = models.CharField(max_length=50)
    phone = models.CharField(max_length=20)
    delivery_latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    delivery_longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    
    def __str__(self):
        return f"Shipping for Order #{self.order.id}"
