from django.db import models
from django.conf import settings
from django.utils import timezone
from decimal import Decimal
from django.contrib.auth import get_user_model
User = get_user_model()

class Farmer(models.Model):
    PROVINCE_CHOICES = [
        ('Kigali City', 'Kigali City'),
        ('Northern Province', 'Northern Province'),
        ('Southern Province', 'Southern Province'),
        ('Eastern Province', 'Eastern Province'),
        ('Western Province', 'Western Province'),
    ]
    
    cooperative = models.ForeignKey(User, on_delete=models.CASCADE, related_name='farmers')
    name = models.CharField(max_length=100, default='')
    phone_number = models.CharField(max_length=20, default='')
    location = models.CharField(max_length=100, default='', choices=PROVINCE_CHOICES, help_text="Province in Rwanda")
    created_at = models.DateTimeField(default=timezone.now)  # Changed from auto_now_add
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name

class Product(models.Model):
    CATEGORY_CHOICES = [
        ('vegetables', 'Vegetables'),
        ('fruits', 'Fruits'),
        ('nuts', 'Nuts'),
        ('herbs', 'Herbs'),
        ('grains', 'Grains'),
    ]
    
    cooperative = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='products')
    farmer = models.ForeignKey(Farmer, on_delete=models.CASCADE, related_name='products')
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.IntegerField(default=0)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='vegetables')
    image = models.ImageField(upload_to='products/', blank=True, null=True)
    variants_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name
    
    
class Category(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True, null=True)
    icon = models.CharField(max_length=50, blank=True, null=True, help_text="Font Awesome icon class")
    color = models.CharField(max_length=20, blank=True, null=True, help_text="Color code for the category")
    display_order = models.PositiveIntegerField(default=0, help_text="Order to display categories")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name_plural = "Categories"
        ordering = ['display_order', 'name']
    
    def __str__(self):
        return self.name
    
    def get_produce_count(self, cooperative=None):
        """Get count of produce items in this category for a cooperative"""
        query = self.produce_types.all()
        if cooperative:
            return CooperativeProduce.objects.filter(
                produce_type__category=self.slug,
                cooperative=cooperative
            ).count()
        return query.count()
    
    def get_total_quantity(self, cooperative=None):
        """Get total quantity of produce items in this category for a cooperative"""
        if cooperative:
            return CooperativeProduce.objects.filter(
                produce_type__category=self.slug,
                cooperative=cooperative
            ).aggregate(total=models.Sum('quantity'))['total'] or 0
        return 0
    
# New models for produce management
class ProduceType(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE, 
        related_name='produce_types'
    )
    unit = models.CharField(max_length=20, default='kg')
    price_per_unit = models.DecimalField(max_digits=10, decimal_places=2)
    image = models.ImageField(upload_to='produce_types/', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True,blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True,blank=True, null=True)
    
    def __str__(self):
        return f"{self.name} ({self.category.name})"



    
    
class ProduceVariant(models.Model):
    produce_type = models.ForeignKey(ProduceType, on_delete=models.CASCADE, related_name='variants')
    grade = models.CharField(max_length=10)  # e.g., "A", "B", "C"
    price_multiplier = models.DecimalField(max_digits=5, decimal_places=2, default=1.0)
    
    def __str__(self):
        return f"{self.produce_type.name} - Grade {self.grade}"

class CooperativeProduce(models.Model):
    cooperative = models.ForeignKey(User, on_delete=models.CASCADE, related_name='produce_items')
    produce_type = models.ForeignKey(ProduceType, on_delete=models.CASCADE, related_name='cooperative_items')
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    location = models.CharField(max_length=100)
    grade = models.CharField(max_length=1, choices=[
        ('A', 'Grade A'),
        ('B', 'Grade B'),
        ('C', 'Grade C'),
        ('D', 'Grade D'),
        ('E', 'Grade E'),
    ], default='A')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.produce_type.name} - {self.quantity} {self.produce_type.unit} ({self.location})"
    
    class Meta:
        ordering = ['-created_at']

# Order models
class Customer(models.Model):
    ROLE_CHOICES = [
        ('individual', 'Individual'),
        ('business', 'Business'),
        ('government', 'Government'),
        ('ngo', 'NGO'),
    ]
    
    full_name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=15)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='individual')
    address = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.full_name
    
    def get_role_display(self):
        return dict(self.ROLE_CHOICES).get(self.role, self.role)

class Order(models.Model):
    STATUS_CHOICES = [
        ('new', 'New Order'),
        ('processing', 'Order Processing'),
        ('delivery', 'On Delivery'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    ]
    
    cooperative = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='orders')
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='orders')
    order_number = models.CharField(max_length=20, unique=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new')
    total_price = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    shipping_address = models.TextField()
    payment_method = models.CharField(max_length=50, default='Cash on Delivery')
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Order #{self.order_number}"
    
    def get_status_display(self):
        return dict(self.STATUS_CHOICES).get(self.status, self.status)
    
    def save(self, *args, **kwargs):
        # Generate order number if not provided
        if not self.order_number:
            last_order = Order.objects.order_by('-id').first()
            if last_order:
                last_id = last_order.id
            else:
                last_id = 0
            self.order_number = f"ORD-{last_id + 1:06d}"
        
        # Calculate total price if not set and if the order already exists
        if self.total_price == 0 and self.pk is not None:
            self.total_price = sum(item.subtotal for item in self.items.all())
            
        super().save(*args, **kwargs)

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    produce_type = models.ForeignKey(ProduceType, on_delete=models.CASCADE)
    variant = models.ForeignKey(ProduceVariant, on_delete=models.CASCADE)
    quantity = models.DecimalField(max_digits=10, decimal_places=2)  # in tons
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2)
    
    def __str__(self):
        return f"{self.produce_type.name} - {self.quantity} tons"
    
    def save(self, *args, **kwargs):
        # Calculate unit price and subtotal if not set
        if not self.unit_price:
            self.unit_price = self.produce_type.base_price * self.variant.price_multiplier
        
        self.subtotal = self.quantity * self.unit_price
        super().save(*args, **kwargs)
        
        # Update order total
        self.order.save()

class OrderReview(models.Model):
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name='review')
    rating = models.IntegerField(choices=[(i, i) for i in range(1, 6)])
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Review for {self.order}"

# Finance models
class Transaction(models.Model):
    TYPE_CHOICES = [
        ('sent', 'Sent'),
        ('received', 'Received'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('success', 'Success'),
        ('failed', 'Failed'),
    ]
    
    PAYMENT_METHOD_CHOICES = [
        ('credit_card', 'Credit Card'),
        ('wire_transfer', 'Wire Transfer'),
        ('mobile_money', 'Mobile Money'),
        ('cash', 'Cash'),
    ]
    
    cooperative = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='transactions')
    transaction_type = models.CharField(max_length=10, choices=TYPE_CHOICES)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    party_name = models.CharField(max_length=100)  # Name of the sender/receiver
    description = models.TextField(blank=True, null=True)
    reference_number = models.CharField(max_length=50, blank=True, null=True)
    order = models.ForeignKey(Order, on_delete=models.SET_NULL, null=True, blank=True, related_name='transactions')
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.get_transaction_type_display()} - RWF {self.amount}"
    
    def get_transaction_type_display(self):
        return dict(self.TYPE_CHOICES).get(self.transaction_type, self.transaction_type)
    
    def get_status_display(self):
        return dict(self.STATUS_CHOICES).get(self.status, self.status)
    
    def get_payment_method_display(self):
        return dict(self.PAYMENT_METHOD_CHOICES).get(self.payment_method, self.payment_method)

class BankAccount(models.Model):
    cooperative = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='bank_accounts')
    bank_name = models.CharField(max_length=100)
    account_number = models.CharField(max_length=50)
    account_holder_name = models.CharField(max_length=100)
    is_primary = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.bank_name} - {self.account_number[-4:]}"
    
    def save(self, *args, **kwargs):
        # If this account is set as primary, unset others
        if self.is_primary:
            BankAccount.objects.filter(
                cooperative=self.cooperative, 
                is_primary=True
            ).exclude(id=self.id).update(is_primary=False)
            
        super().save(*args, **kwargs)

