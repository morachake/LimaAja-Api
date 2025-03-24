from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q, Sum, F, ExpressionWrapper, DecimalField
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.urls import reverse

from .models import (
    ShopCustomer, ShippingAddress, ShoppingCart, CartItem,
    ShopOrder, ShopOrderItem, ShopPayment
)
from cooperative.models import (
    CooperativeProduce, ProduceType, ProduceVariant, Category
)

def shop_home(request):
    """Home page for the shop"""
    # Get all active produce items
    produce_items = CooperativeProduce.objects.filter(
        produce_type__is_active=True
    ).select_related('produce_type', 'cooperative').order_by('-created_at')
    
    # Get all categories
    categories = Category.objects.all().order_by('display_order')
    
    # Get featured items (newest 4 items)
    featured_items = produce_items[:4]
    
    # Get items by category
    items_by_category = {}
    for category in categories:
        category_items = produce_items.filter(produce_type__category=category)[:8]
        if category_items.exists():
            items_by_category[category] = category_items
    
    context = {
        'produce_items': produce_items,
        'categories': categories,
        'featured_items': featured_items,
        'items_by_category': items_by_category,
    }
    
    return render(request, 'shop/home.html', context)

def product_detail(request, produce_id):
    """Product detail page"""
    produce = get_object_or_404(
        CooperativeProduce, 
        id=produce_id,
        produce_type__is_active=True
    )
    
    # Get related products (same category)
    related_products = CooperativeProduce.objects.filter(
        produce_type__category=produce.produce_type.category
    ).exclude(id=produce_id)[:4]
    
    context = {
        'produce': produce,
        'related_products': related_products,
    }
    
    return render(request, 'shop/product_detail.html', context)

def category_products(request, category_slug):
    """View products by category"""
    category = get_object_or_404(Category, slug=category_slug)
    
    produce_items = CooperativeProduce.objects.filter(
        produce_type__category=category,
        produce_type__is_active=True
    ).select_related('produce_type', 'cooperative')
    
    context = {
        'category': category,
        'produce_items': produce_items,
    }
    
    return render(request, 'shop/category_products.html', context)

def search_products(request):
    """Search for products"""
    query = request.GET.get('q', '')
    
    if query:
        produce_items = CooperativeProduce.objects.filter(
            Q(produce_type__name__icontains=query) |
            Q(produce_type__description__icontains=query) |
            Q(produce_type__category__name__icontains=query)
        ).filter(produce_type__is_active=True).select_related('produce_type', 'cooperative')
    else:
        produce_items = CooperativeProduce.objects.none()
    
    context = {
        'query': query,
        'produce_items': produce_items,
    }
    
    return render(request, 'shop/search_results.html', context)

@login_required
def view_cart(request):
    """View shopping cart"""
    # Get or create customer
    customer, created = ShopCustomer.objects.get_or_create(user=request.user)
    
    # Get or create cart
    cart, created = ShoppingCart.objects.get_or_create(customer=customer)
    
    context = {
        'cart': cart,
    }
    
    return render(request, 'shop/cart.html', context)

@login_required
@require_POST
def add_to_cart(request):
    """Add item to cart"""
    produce_id = request.POST.get('produce_id')
    quantity = request.POST.get('quantity', 1)
    
    try:
        quantity = float(quantity)
        if quantity <= 0:
            return JsonResponse({'error': 'Quantity must be positive'}, status=400)
    except ValueError:
        return JsonResponse({'error': 'Invalid quantity'}, status=400)
    
    # Get produce
    produce = get_object_or_404(CooperativeProduce, id=produce_id)
    
    # Check if enough stock
    if produce.quantity < quantity:
        return JsonResponse({'error': 'Not enough stock available'}, status=400)
    
    # Get or create customer
    customer, created = ShopCustomer.objects.get_or_create(user=request.user)
    
    # Get or create cart
    cart, created = ShoppingCart.objects.get_or_create(customer=customer)
    
    # Add item to cart
    cart_item, created = CartItem.objects.get_or_create(
        cart=cart,
        produce=produce,
        defaults={'quantity': quantity}
    )
    
    # If item already exists, update quantity
    if not created:
        cart_item.quantity += quantity
        cart_item.save()
    
    return JsonResponse({
        'success': True,
        'message': f'Added {quantity} {produce.produce_type.name} to cart',
        'cart_total': cart.total_items
    })

@login_required
@require_POST
def update_cart(request):
    """Update cart item quantity"""
    item_id = request.POST.get('item_id')
    quantity = request.POST.get('quantity')
    
    try:
        quantity = float(quantity)
        if quantity <= 0:
            return JsonResponse({'error': 'Quantity must be positive'}, status=400)
    except ValueError:
        return JsonResponse({'error': 'Invalid quantity'}, status=400)
    
    # Get cart item
    cart_item = get_object_or_404(CartItem, id=item_id)
    
    # Check if user owns this cart item
    if cart_item.cart.customer.user != request.user:
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    # Check if enough stock
    if cart_item.produce.quantity < quantity:
        return JsonResponse({'error': 'Not enough stock available'}, status=400)
    
    # Update quantity
    cart_item.quantity = quantity
    cart_item.save()
    
    return JsonResponse({
        'success': True,
        'message': 'Cart updated',
        'item_subtotal': cart_item.subtotal,
        'cart_total': cart_item.cart.total_price
    })

@login_required
@require_POST
def remove_from_cart(request):
    """Remove item from cart"""
    item_id = request.POST.get('item_id')
    
    # Get cart item
    cart_item = get_object_or_404(CartItem, id=item_id)
    
    # Check if user owns this cart item
    if cart_item.cart.customer.user != request.user:
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    # Remove item
    cart_item.delete()
    
    return JsonResponse({
        'success': True,
        'message': 'Item removed from cart',
        'cart_total': cart_item.cart.total_price
    })

@login_required
def checkout(request):
    """Checkout page"""
    # Get customer
    customer, created = ShopCustomer.objects.get_or_create(user=request.user)
    
    # Get cart
    cart = get_object_or_404(ShoppingCart, customer=customer)
    
    # Check if cart is empty
    if cart.items.count() == 0:
        messages.error(request, 'Your cart is empty')
        return redirect('shop_cart')
    
    # Get shipping addresses
    addresses = ShippingAddress.objects.filter(customer=customer)
    
    # Calculate shipping fee (simplified)
    shipping_fee = 1000  # Fixed fee of 1000 RWF
    
    context = {
        'cart': cart,
        'addresses': addresses,
        'shipping_fee': shipping_fee,
        'total': cart.total_price + shipping_fee
    }
    
    return render(request, 'shop/checkout.html', context)

@login_required
@require_POST
def place_order(request):
    """Place an order"""
    # Get customer
    customer, created = ShopCustomer.objects.get_or_create(user=request.user)
    
    # Get cart
    cart = get_object_or_404(ShoppingCart, customer=customer)
    
    # Check if cart is empty
    if cart.items.count() == 0:
        messages.error(request, 'Your cart is empty')
        return redirect('shop_cart')
    
    # Get form data
    address_id = request.POST.get('address_id')
    payment_method = request.POST.get('payment_method')
    notes = request.POST.get('notes', '')
    
    # Get shipping address
    if address_id:
        shipping_address = get_object_or_404(ShippingAddress, id=address_id, customer=customer)
    else:
        # Create new address
        shipping_address = ShippingAddress.objects.create(
            customer=customer,
            address_line1=request.POST.get('address_line1'),
            address_line2=request.POST.get('address_line2', ''),
            city=request.POST.get('city'),
            province=request.POST.get('province'),
            postal_code=request.POST.get('postal_code'),
            country=request.POST.get('country', 'Rwanda'),
            is_default=request.POST.get('set_default', False)
        )
    
    # Calculate shipping fee (simplified)
    shipping_fee = 1000  # Fixed fee of 1000 RWF
    
    # Create order
    order = ShopOrder.objects.create(
        customer=customer,
        shipping_address=shipping_address,
        shipping_fee=shipping_fee,
        subtotal=cart.total_price,
        total=cart.total_price + shipping_fee,
        payment_method=payment_method,
        notes=notes
    )
    
    # Create order items
    for cart_item in cart.items.all():
        ShopOrderItem.objects.create(
            order=order,
            produce=cart_item.produce,
            cooperative=cart_item.produce.cooperative,
            quantity=cart_item.quantity,
            unit_price=cart_item.unit_price,
            subtotal=cart_item.subtotal
        )
    
    # Create payment record
    payment = ShopPayment.objects.create(
        order=order,
        amount=order.total,
        payment_method=payment_method,
        status='pending'
    )
    
    # Clear cart
    cart.clear()
    
    # Redirect to order confirmation
    return redirect('order_confirmation', order_id=order.id)

@login_required
def order_confirmation(request, order_id):
    """Order confirmation page"""
    # Get order
    order = get_object_or_404(ShopOrder, id=order_id)
    
    # Check if user owns this order
    if order.customer.user != request.user:
        messages.error(request, 'Unauthorized')
        return redirect('shop_home')
    
    context = {
        'order': order,
    }
    
    return render(request, 'shop/order_confirmation.html', context)

@login_required
def order_history(request):
    """Order history page"""
    # Get customer
    customer, created = ShopCustomer.objects.get_or_create(user=request.user)
    
    # Get orders
    orders = ShopOrder.objects.filter(customer=customer).order_by('-created_at')
    
    context = {
        'orders': orders,
    }
    
    return render(request, 'shop/order_history.html', context)

@login_required
def order_detail(request, order_id):
    """Order detail page"""
    # Get order
    order = get_object_or_404(ShopOrder, id=order_id)
    
    # Check if user owns this order
    if order.customer.user != request.user:
        messages.error(request, 'Unauthorized')
        return redirect('shop_home')
    
    context = {
        'order': order,
    }
    
    return render(request, 'shop/order_detail.html', context)

