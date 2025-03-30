from django.contrib import admin
from .models import Cart, CartItem, Order, OrderItem, Address, PaymentMethod, Notification

class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0
    readonly_fields = ['subtotal']

@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'item_count', 'total', 'created_at']
    inlines = [CartItemInline]
    readonly_fields = ['total', 'item_count']

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ['subtotal']

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'total_amount', 'status', 'payment_method', 'created_at']
    list_filter = ['status', 'payment_method', 'created_at']
    search_fields = ['user__email', 'shipping_address']
    inlines = [OrderItemInline]

@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ['user', 'name', 'recipient_name', 'city', 'is_default']
    list_filter = ['is_default', 'city', 'state']
    search_fields = ['user__email', 'recipient_name', 'street_address']

@admin.register(PaymentMethod)
class PaymentMethodAdmin(admin.ModelAdmin):
    list_display = ['user', 'payment_type', 'name', 'is_default']
    list_filter = ['payment_type', 'is_default']
    search_fields = ['user__email', 'name']

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['user', 'notification_type', 'title', 'is_read', 'created_at']
    list_filter = ['notification_type', 'is_read', 'created_at']
    search_fields = ['user__email', 'title', 'message']

