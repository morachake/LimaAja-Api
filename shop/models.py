from django.db import models
from django.conf import settings
from django.utils import timezone
from cooperative.models import CooperativeProduce, ProduceType, ProduceVariant
from django.contrib.auth import get_user_model

User = get_user_model()

class ShopCustomer(models.Model):
    """Customer model for shop users (buyers)"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='shop_customer')
    default_shipping_address = models.ForeignKey('ShippingAddress', on_delete=models.SET_NULL, 
                                               null=True, blank=True, related_name='default_for_customers')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Customer: {self.user.full_name}"
    
    @property
    def full_name(self):
        return self.user.full_name
    
    @property
    def email(self):
        return self.user.email
    
    @property
    def phone_number(self):
        return self.user.phone_number

class ShippingAddress(models.Model):
    """Shipping address for orders"""
    customer = models.ForeignKey(ShopCustomer, on_delete=models.CASCADE, related_name='addresses')
    address_line1 = models.CharField(max_length=255)
    address_line2 = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=100)
    province = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20)
    country = models.CharField(max_length=100, default="Rwanda")
    is_default = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.address_line1}, {self.city}, {self.province}"
    
    def save(self, *args, **kwargs):
        # If this address is set as default, unset others
        if self.is_default:
            ShippingAddress.objects.filter(
                customer=self.customer, 
                is_default=True
            ).exclude(id=self.id).update(is_default=False)
            
            # Update customer's default shipping address
            self.customer.default_shipping_address = self
            self.customer.save()
            
        super().save(*args, **kwargs)

class ShoppingCart(models.Model):
    """Shopping cart model"""
    customer = models.OneToOneField(ShopCustomer, on_delete=models.CASCADE, related_name='cart')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Cart for {self.customer.user.full_name}"
    
    @property
    def total_items(self):
        return sum(item.quantity for item in self.items.all())
    
    @property
    def total_price(self):
        return sum(item.subtotal for item in self.items.all())
    
    def clear(self):
        self.items.all().delete()
        self.save()

class CartItem(models.Model):
    """Items in the shopping cart"""
    cart = models.ForeignKey(ShoppingCart, on_delete=models.CASCADE, related_name='items')
    produce = models.ForeignKey(CooperativeProduce, on_delete=models.CASCADE)
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    added_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('cart', 'produce')
    
    def __str__(self):
        return f"{self.quantity} of {self.produce}"
    
    @property
    def unit_price(self):
        # Get the price from the produce
        return self.produce.produce_type.price_per_unit
    
    @property
    def subtotal(self):
        return self.quantity * self.unit_price

class ShopOrder(models.Model):
    """Order model for shop customers"""
    STATUS_CHOICES = [
        ('pending', 'Pending Payment'),
        ('paid', 'Paid'),
        ('processing', 'Processing'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
        ('refunded', 'Refunded'),
    ]
    
    PAYMENT_METHOD_CHOICES = [
        ('credit_card', 'Credit Card'),
        ('mobile_money', 'Mobile Money'),
        ('bank_transfer', 'Bank Transfer'),
        ('cash_on_delivery', 'Cash on Delivery'),
    ]
    
    customer = models.ForeignKey(ShopCustomer, on_delete=models.CASCADE, related_name='orders')
    order_number = models.CharField(max_length=20, unique=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    shipping_address = models.ForeignKey(ShippingAddress, on_delete=models.SET_NULL, null=True)
    shipping_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2)
    total = models.DecimalField(max_digits=12, decimal_places=2)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES)
    payment_details = models.JSONField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Order #{self.order_number}"
    
    def save(self, *args, **kwargs):
        # Generate order number if not provided
        if not self.order_number:
            last_order = ShopOrder.objects.order_by('-id').first()
            if last_order:
                last_id = last_order.id
            else:
                last_id = 0
            self.order_number = f"SO-{last_id + 1:06d}"
        
        # Calculate total if not set
        if not self.total:
            self.total = self.subtotal + self.shipping_fee
            
        super().save(*args, **kwargs)

class ShopOrderItem(models.Model):
    """Items in a shop order"""
    order = models.ForeignKey(ShopOrder, on_delete=models.CASCADE, related_name='items')
    produce = models.ForeignKey(CooperativeProduce, on_delete=models.CASCADE)
    cooperative = models.ForeignKey(User, on_delete=models.CASCADE)
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2)
    
    def __str__(self):
        return f"{self.quantity} of {self.produce}"
    
    def save(self, *args, **kwargs):
        # Calculate subtotal if not set
        if not self.subtotal:
            self.subtotal = self.quantity * self.unit_price
            
        super().save(*args, **kwargs)

class ShopPayment(models.Model):
    """Payment model for shop orders"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    ]
    
    order = models.OneToOneField(ShopOrder, on_delete=models.CASCADE, related_name='payment')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    payment_method = models.CharField(max_length=20)
    transaction_id = models.CharField(max_length=100, blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    payment_details = models.JSONField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Payment for {self.order}"

