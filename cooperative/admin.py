from django.contrib import admin
from .models import (
    Farmer, Product, ProduceType, ProduceVariant, CooperativeProduce,
    Customer, Order, OrderItem, OrderReview,
    Transaction, BankAccount
)

# Register basic models
admin.site.register(Farmer)
admin.site.register(Product)
admin.site.register(ProduceType)
admin.site.register(ProduceVariant)
admin.site.register(CooperativeProduce)

# Order admin
class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0

class OrderReviewInline(admin.StackedInline):
    model = OrderReview
    extra = 0

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('order_number', 'cooperative', 'customer', 'status', 'total_price', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('order_number', 'customer__full_name', 'cooperative__full_name')
    inlines = [OrderItemInline, OrderReviewInline]

@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'email', 'phone_number', 'role')
    list_filter = ('role',)
    search_fields = ('full_name', 'email', 'phone_number')

# Finance admin
@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('cooperative', 'transaction_type', 'amount', 'payment_method', 'status', 'party_name', 'created_at')
    list_filter = ('transaction_type', 'status', 'payment_method', 'created_at')
    search_fields = ('party_name', 'description', 'reference_number')

@admin.register(BankAccount)
class BankAccountAdmin(admin.ModelAdmin):
    list_display = ('cooperative', 'bank_name', 'account_number', 'account_holder_name', 'is_primary')
    list_filter = ('bank_name', 'is_primary')
    search_fields = ('account_holder_name', 'account_number')

@admin.register(Category)