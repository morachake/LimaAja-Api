from django.db import models
from django.conf import settings
from django.utils import timezone

class Farmer(models.Model):
    cooperative = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='farmers')
    name = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=15)
    address = models.TextField(blank=True, null=True)
    joining_date = models.DateField(default=timezone.now)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return self.name

class Product(models.Model):
    cooperative = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='products')
    farmer = models.ForeignKey(Farmer, on_delete=models.CASCADE, related_name='products')
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name

# New models for produce management
class ProduceType(models.Model):
    CATEGORY_CHOICES = [
        ('vegetables', 'Vegetables'),
        ('fruits', 'Fruits'),
        ('nuts', 'Nuts'),
        ('herbs', 'Herbs'),
        ('grains', 'Grains'),
        ('other', 'Other'),
    ]
    
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='other')
    base_price = models.DecimalField(max_digits=10, decimal_places=2)
    image = models.ImageField(upload_to='produce/', blank=True, null=True)
    
    def __str__(self):
        return self.name

class ProduceVariant(models.Model):
    produce_type = models.ForeignKey(ProduceType, on_delete=models.CASCADE, related_name='variants')
    grade = models.CharField(max_length=10)  # e.g., "A", "B", "C"
    price_multiplier = models.DecimalField(max_digits=5, decimal_places=2, default=1.0)
    
    def __str__(self):
        return f"{self.produce_type.name} - Grade {self.grade}"

class CooperativeProduce(models.Model):
    cooperative = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='cooperative_produce')
    produce_type = models.ForeignKey(ProduceType, on_delete=models.CASCADE)
    variant = models.ForeignKey(ProduceVariant, on_delete=models.CASCADE)
    quantity = models.DecimalField(max_digits=10, decimal_places=2)  # in tons
    province = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.produce_type.name} - {self.quantity} tons"

