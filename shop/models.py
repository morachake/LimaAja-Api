from django.db import models
from django.conf import settings
from cooperative.models import CooperativeProduce

class Cart(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True,
        related_name='shopping_carts'  # Added related_name
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        if self.user:
            return f"Cart for {self.user.username}"
        return f"Anonymous Cart {self.id}"
    
    @property
    def total(self):
        """Calculate the total price of all items in the cart"""
        return sum(item.subtotal for item in self.items.all())
    
    @property
    def item_count(self):
        """Count the number of items in the cart"""
        return self.items.count()

class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(CooperativeProduce, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)  # Changed from added_at to created_at
    updated_at = models.DateTimeField(auto_now=True)  # Added updated_at
    
    def __str__(self):
        return f"{self.quantity} x {self.product.produce_type.name}"
    
    @property
    def subtotal(self):
        """Calculate the subtotal for this item"""
        return self.product.produce_type.price_per_unit * self.quantity

class Order(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    )
    
    PAYMENT_CHOICES = (
        ('credit_card', 'Credit Card'),
        ('paypal', 'PayPal'),
        ('bank_transfer', 'Bank Transfer'),
        ('mobile_money', 'Mobile Money'),
        ('cash_on_delivery', 'Cash on Delivery'),
    )
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='shop_orders'  # Changed from 'orders' to 'shop_orders'
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    shipping_address = models.TextField()
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    zip_code = models.CharField(max_length=20)
    phone = models.CharField(max_length=20)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_CHOICES)
    payment_status = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Order #{self.id} - {self.user.username}"
    
    @property
    def item_count(self):
        """Count the number of items in the order"""
        return self.items.count()

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(CooperativeProduce, on_delete=models.CASCADE)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1)
    
    def __str__(self):
        return f"{self.quantity} x {self.product.produce_type.name}"
    
    @property
    def subtotal(self):
        """Calculate the subtotal for this item"""
        return self.price * self.quantity

