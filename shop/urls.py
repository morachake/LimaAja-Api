from django.urls import path
from . import views

urlpatterns = [
    # Shop pages
    path('', views.shop_home, name='shop_home'),
    path('product/<int:produce_id>/', views.product_detail, name='product_detail'),
    path('category/<slug:category_slug>/', views.category_products, name='category_products'),
    path('search/', views.search_products, name='search_products'),
    
    # Cart
    path('cart/', views.view_cart, name='shop_cart'),
    path('cart/add/', views.add_to_cart, name='add_to_cart'),
    path('cart/update/', views.update_cart, name='update_cart'),
    path('cart/remove/', views.remove_from_cart, name='remove_from_cart'),
    
    # Checkout
    path('checkout/', views.checkout, name='checkout'),
    path('place-order/', views.place_order, name='place_order'),
    path('order-confirmation/<int:order_id>/', views.order_confirmation, name='order_confirmation'),
    
    # Orders
    path('orders/', views.order_history, name='order_history'),
    path('orders/<int:order_id>/', views.order_detail, name='order_detail'),
]

