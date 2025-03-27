from django.urls import path
from . import views

app_name = 'shop'

urlpatterns = [
    # Main shop pages
    path('', views.home, name='home'),
    path('products/', views.product_list, name='product_list'),
    path('product/<int:product_id>/', views.product_detail, name='product_detail'),
    
    # Cart and checkout
    path('cart/', views.cart, name='cart'),
    path('add-to-cart/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('update-cart/<int:item_id>/', views.update_cart, name='update_cart'),
    path('checkout/', views.checkout, name='checkout'),
    path('remove-from-cart/<int:item_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('order-confirmation/<int:order_id>/', views.order_confirmation, name='order_confirmation'),
    
    # User account
    path('dashboard/', views.user_dashboard, name='user_dashboard'),
    path('orders/', views.order_history, name='order_history'),
    path('order/<int:order_id>/', views.order_detail, name='order_detail'),
    path('settings/', views.user_settings, name='user_settings'),
    
    # Addresses
    path('addresses/', views.user_addresses, name='user_addresses'),
    path('addresses/add/', views.add_address, name='add_address'),
    path('addresses/edit/<int:address_id>/', views.edit_address, name='edit_address'),
    path('addresses/delete/<int:address_id>/', views.delete_address, name='delete_address'),
    
    # Payment methods
    path('payment-methods/', views.user_payment_methods, name='user_payment_methods'),
    path('payment-methods/add/', views.add_payment_method, name='add_payment_method'),
    path('payment-methods/delete/<int:payment_id>/', views.delete_payment_method, name='delete_payment_method'),
    path('payment-methods/set-default/<int:payment_id>/', views.set_default_payment, name='set_default_payment'),
    
    # Notifications
    path('notifications/', views.user_notifications, name='user_notifications'),
    path('notifications/mark-read/<int:notification_id>/', views.mark_notification_read, name='mark_notification_read'),
    
    # Authentication
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
]

