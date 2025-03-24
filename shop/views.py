from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.http import JsonResponse
from django.db.models import Sum, Count, Q
from django.utils import timezone
from datetime import timedelta

from cooperative.models import CooperativeProduce, Category
from .models import (
    Cart, CartItem, Order, OrderItem, 
    Address, PaymentMethod, Notification
)

def home(request):
    # Get featured products
    featured_products = CooperativeProduce.objects.filter(
        quantity__gt=0
    ).order_by('-created_at')[:8]
    
    # Get categories
    categories = Category.objects.all()[:6]
    
    # Get recent products
    recent_products = CooperativeProduce.objects.filter(
        quantity__gt=0
    ).order_by('-created_at')[:4]
    
    # Get fruit and vegetable products
    fruit_products = CooperativeProduce.objects.filter(
        quantity__gt=0,
        produce_type__category__name__icontains='fruit'
    ).order_by('-created_at')[:4]
    
    vegetable_products = CooperativeProduce.objects.filter(
        quantity__gt=0,
        produce_type__category__name__icontains='vegetable'
    ).order_by('-created_at')[:4]
    
    context = {
        'featured_products': featured_products,
        'categories': categories,
        'recent_products': recent_products,
        'fruit_products': fruit_products,
        'vegetable_products': vegetable_products,
    }
    return render(request, 'shop/home.html', context)

def product_list(request):
    products = CooperativeProduce.objects.filter(quantity__gt=0)
    
    # Filter by category if provided
    category_slug = request.GET.get('category')
    if category_slug:
        products = products.filter(produce_type__category__slug=category_slug)
    
    # Filter by search query if provided
    search_query = request.GET.get('q')
    if search_query:
        products = products.filter(
            Q(produce_type__name__icontains=search_query) | 
            Q(produce_type__description__icontains=search_query)
        )
    
    # Get all categories for the filter sidebar
    categories = Category.objects.all()
    
    context = {
        'products': products,
        'categories': categories,
        'selected_category': category_slug,
        'search_query': search_query,
    }
    return render(request, 'shop/product_list.html', context)

def product_detail(request, product_id):
    product = get_object_or_404(CooperativeProduce, id=product_id)
    
    # Get related products (same category)
    related_products = CooperativeProduce.objects.filter(
        produce_type__category=product.produce_type.category,
        quantity__gt=0
    ).exclude(id=product_id)[:4]
    
    context = {
        'product': product,
        'related_products': related_products,
    }
    return render(request, 'shop/product_detail.html', context)

def get_or_create_cart(request):
    """Helper function to get or create a cart for the current user/session"""
    if request.user.is_authenticated:
        cart, created = Cart.objects.get_or_create(user=request.user)
    else:
        cart_id = request.session.get('cart_id')
        if cart_id:
            try:
                cart = Cart.objects.get(id=cart_id)
            except Cart.DoesNotExist:
                cart = Cart.objects.create()
                request.session['cart_id'] = cart.id
        else:
            cart = Cart.objects.create()
            request.session['cart_id'] = cart.id
    return cart

@login_required
def add_to_cart(request, product_id):
    product = get_object_or_404(CooperativeProduce, id=product_id, quantity__gt=0)
    cart = get_or_create_cart(request)
    
    quantity = int(request.POST.get('quantity', 1))
    
    # Check if the product is already in the cart
    try:
        cart_item = CartItem.objects.get(cart=cart, product=product)
        cart_item.quantity += quantity
        cart_item.save()
    except CartItem.DoesNotExist:
        CartItem.objects.create(cart=cart, product=product, quantity=quantity)
    
    messages.success(request, f"{product.produce_type.name} added to your cart.")
    
    # If AJAX request, return JSON response
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'cart_count': cart.item_count,
        })
    
    # Otherwise redirect to the cart page
    return redirect('shop:cart')

@login_required
def cart(request):
    cart = get_or_create_cart(request)
    
    context = {
        'cart': cart,
        'cart_items': cart.items.all(),
    }
    return render(request, 'shop/cart.html', context)

@login_required
def update_cart(request, item_id):
    cart_item = get_object_or_404(CartItem, id=item_id)
    
    # Ensure the cart belongs to the current user
    if request.user.is_authenticated and cart_item.cart.user != request.user:
        messages.error(request, "You don't have permission to modify this cart.")
        return redirect('shop:cart')
    
    action = request.POST.get('action')
    
    if action == 'remove':
        cart_item.delete()
        messages.success(request, "Item removed from cart.")
    elif action == 'update':
        quantity = int(request.POST.get('quantity', 1))
        if quantity > 0:
            cart_item.quantity = quantity
            cart_item.save()
            messages.success(request, "Cart updated.")
        else:
            cart_item.delete()
            messages.success(request, "Item removed from cart.")
    
    # If AJAX request, return JSON response
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        cart = cart_item.cart
        return JsonResponse({
            'success': True,
            'cart_count': cart.item_count,
            'cart_total': float(cart.total),
        })
    
    return redirect('shop:cart')

@login_required
def checkout(request):
    cart = get_or_create_cart(request)
    
    # Check if cart is empty
    if cart.items.count() == 0:
        messages.warning(request, "Your cart is empty. Add some products before checkout.")
        return redirect('shop:product_list')
    
    # Get user's addresses and payment methods
    addresses = Address.objects.filter(user=request.user)
    payment_methods = PaymentMethod.objects.filter(user=request.user)
    
    # Get default address and payment method if available
    default_address = addresses.filter(is_default=True).first()
    default_payment = payment_methods.filter(is_default=True).first()
    
    if request.method == 'POST':
        # Process the order
        address_id = request.POST.get('address')
        payment_method_id = request.POST.get('payment_method')
        
        # Validate inputs
        if not address_id:
            messages.error(request, "Please select a shipping address.")
            return redirect('shop:checkout')
        
        if not payment_method_id and not request.POST.get('payment_type'):
            messages.error(request, "Please select a payment method.")
            return redirect('shop:checkout')
        
        # Get the selected address
        address = get_object_or_404(Address, id=address_id, user=request.user)
        
        # Create the order
        order = Order.objects.create(
            user=request.user,
            total_amount=cart.total,
            shipping_address=address.street_address,
            city=address.city,
            state=address.state,
            zip_code=address.zip_code,
            phone=address.phone,
            payment_method=request.POST.get('payment_type', 'Cash on Delivery'),
        )
        
        # Create order items
        for cart_item in cart.items.all():
            OrderItem.objects.create(
                order=order,
                product=cart_item.product,
                price=cart_item.product.produce_type.price_per_unit,
                quantity=cart_item.quantity,
            )
        
        # Create notification for the order
        Notification.objects.create(
            user=request.user,
            notification_type='order',
            title='Order Placed Successfully',
            message=f'Your order #{order.id} has been placed successfully and is now being processed.',
        )
        
        # Clear the cart
        cart.items.all().delete()
        
        # Redirect to order confirmation
        return redirect('shop:order_confirmation', order_id=order.id)
    
    context = {
        'cart': cart,
        'cart_items': cart.items.all(),
        'addresses': addresses,
        'payment_methods': payment_methods,
        'default_address': default_address,
        'default_payment': default_payment,
    }
    return render(request, 'shop/checkout.html', context)

@login_required
def order_confirmation(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    
    context = {
        'order': order,
        'order_items': order.items.all(),
    }
    return render(request, 'shop/order_confirmation.html', context)

@login_required
def order_history(request):
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    
    context = {
        'orders': orders,
    }
    return render(request, 'shop/order_history.html', context)

@login_required
def order_detail(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    
    context = {
        'order': order,
        'order_items': order.items.all(),
    }
    return render(request, 'shop/order_detail.html', context)

@login_required
def user_dashboard(request):
    # Get user's recent orders
    recent_orders = Order.objects.filter(user=request.user).order_by('-created_at')[:5]
    
    # Get total orders and spending
    total_orders = Order.objects.filter(user=request.user).count()
    total_spent = Order.objects.filter(user=request.user).aggregate(total=Sum('total_amount'))['total'] or 0
    
    # Get unread notifications count
    unread_notifications = Notification.objects.filter(user=request.user, is_read=False).count()
    
    context = {
        'recent_orders': recent_orders,
        'total_orders': total_orders,
        'total_spent': total_spent,
        'unread_notifications': unread_notifications,
    }
    return render(request, 'shop/user_dashboard.html', context)

@login_required
def user_settings(request):
    if request.method == 'POST':
        # Update user profile
        user = request.user
        user.first_name = request.POST.get('first_name', user.first_name)
        user.last_name = request.POST.get('last_name', user.last_name)
        user.email = request.POST.get('email', user.email)
        user.save()
        
        messages.success(request, "Your profile has been updated successfully.")
        return redirect('shop:user_settings')
    
    context = {}
    return render(request, 'shop/user_settings.html', context)

@login_required
def user_addresses(request):
    addresses = Address.objects.filter(user=request.user).order_by('-is_default', '-created_at')
    
    context = {
        'addresses': addresses,
    }
    return render(request, 'shop/user_addresses.html', context)

@login_required
def add_address(request):
    if request.method == 'POST':
        # Create new address
        address = Address.objects.create(
            user=request.user,
            name=request.POST.get('name'),
            recipient_name=request.POST.get('recipient_name'),
            street_address=request.POST.get('street_address'),
            city=request.POST.get('city'),
            state=request.POST.get('state'),
            zip_code=request.POST.get('zip_code'),
            phone=request.POST.get('phone'),
            is_default=request.POST.get('is_default') == 'on',
        )
        
        messages.success(request, "Address added successfully.")
        return redirect('shop:user_addresses')
    
    context = {}
    return render(request, 'shop/add_address.html', context)

@login_required
def edit_address(request, address_id):
    address = get_object_or_404(Address, id=address_id, user=request.user)
    
    if request.method == 'POST':
        # Update address
        address.name = request.POST.get('name')
        address.recipient_name = request.POST.get('recipient_name')
        address.street_address = request.POST.get('street_address')
        address.city = request.POST.get('city')
        address.state = request.POST.get('state')
        address.zip_code = request.POST.get('zip_code')
        address.phone = request.POST.get('phone')
        address.is_default = request.POST.get('is_default') == 'on'
        address.save()
        
        messages.success(request, "Address updated successfully.")
        return redirect('shop:user_addresses')
    
    context = {
        'address': address,
    }
    return render(request, 'shop/edit_address.html', context)

@login_required
def delete_address(request, address_id):
    address = get_object_or_404(Address, id=address_id, user=request.user)
    
    if request.method == 'POST':
        address.delete()
        messages.success(request, "Address deleted successfully.")
    
    return redirect('shop:user_addresses')

@login_required
def user_payment_methods(request):
    payment_methods = PaymentMethod.objects.filter(user=request.user).order_by('-is_default', '-created_at')
    
    context = {
        'payment_methods': payment_methods,
    }
    return render(request, 'shop/user_payment_methods.html', context)

@login_required
def add_payment_method(request):
    if request.method == 'POST':
        payment_type = request.POST.get('payment_type')
        name = request.POST.get('name')
        is_default = request.POST.get('is_default') == 'on'
        
        # Create details based on payment type
        details = {}
        if payment_type == 'mobile_money':
            details = {
                'provider': request.POST.get('provider'),
                'phone_number': request.POST.get('phone_number'),
            }
        elif payment_type == 'bank_account':
            details = {
                'bank_name': request.POST.get('bank_name'),
                'account_number': request.POST.get('account_number'),
                'account_name': request.POST.get('account_name'),
            }
        elif payment_type == 'credit_card':
            details = {
                'card_number': request.POST.get('card_number')[-4:],  # Store only last 4 digits
                'card_holder': request.POST.get('card_holder'),
                'expiry_month': request.POST.get('expiry_month'),
                'expiry_year': request.POST.get('expiry_year'),
            }
        
        # Create payment method
        PaymentMethod.objects.create(
            user=request.user,
            payment_type=payment_type,
            name=name,
            details=details,
            is_default=is_default,
        )
        
        messages.success(request, "Payment method added successfully.")
        return redirect('shop:user_payment_methods')
    
    context = {}
    return render(request, 'shop/add_payment_method.html', context)

@login_required
def delete_payment_method(request, payment_id):
    payment = get_object_or_404(PaymentMethod, id=payment_id, user=request.user)
    
    if request.method == 'POST':
        payment.delete()
        messages.success(request, "Payment method deleted successfully.")
    
    return redirect('shop:user_payment_methods')

@login_required
def set_default_payment(request, payment_id):
    payment = get_object_or_404(PaymentMethod, id=payment_id, user=request.user)
    
    payment.is_default = True
    payment.save()
    
    messages.success(request, f"{payment.name} set as default payment method.")
    return redirect('shop:user_payment_methods')

@login_required
def user_notifications(request):
    notifications = Notification.objects.filter(user=request.user).order_by('-created_at')
    
    # Mark all as read if requested
    if request.GET.get('mark_all_read'):
        notifications.update(is_read=True)
        messages.success(request, "All notifications marked as read.")
        return redirect('shop:user_notifications')
    
    context = {
        'notifications': notifications,
    }
    return render(request, 'shop/user_notifications.html', context)

@login_required
def mark_notification_read(request, notification_id):
    notification = get_object_or_404(Notification, id=notification_id, user=request.user)
    
    notification.is_read = True
    notification.save()
    
    # If AJAX request, return JSON response
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'success': True})
    
    return redirect('shop:user_notifications')


def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f"Welcome back, {username}!")
                return redirect('shop:home')
            else:
                messages.error(request, "Invalid username or password.")
        else:
            messages.error(request, "Invalid username or password.")
    else:
        form = AuthenticationForm()
    
    context = {
        'form': form
    }
    return render(request, 'shop/login.html', context)

def register_view(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f"Account created successfully. Welcome, {user.username}!")
            return redirect('shop:home')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        form = UserCreationForm()
    
    context = {
        'form': form
    }
    return render(request, 'shop/register.html', context)

def logout_view(request):
    logout(request)
    messages.success(request, "You have been logged out successfully.")
    return redirect('shop:home')

