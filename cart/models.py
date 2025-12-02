from django.db import models
from django.contrib.auth.models import User
from products.models import Product

class Cart(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='cart', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def get_subtotal(self):
        return sum(item.total_price for item in self.items.all())

    def __str__(self):
        return f"Cart {self.id} for {self.user.username if self.user else 'Anonymous'}"
    
    @property
    def get_total(self):
        return self.get_subtotal  # shipping illa enkil same

class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    @property
    def total_price(self):
        return self.product.price * self.quantity



