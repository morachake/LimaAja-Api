from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.urls import reverse
from cooperative.models import CooperativeProduce, Category
from .models import Cart, CartItem, Order, OrderItem, Address, PaymentMethod, Notification
from django.db.models import Sum, F, Count
from django.utils import timezone
from django.http import JsonResponse
from .forms import CustomUserCreationForm, CustomAuthenticationForm

def home(request):
    # Get categories that have products
    categories_with_products = Category.objects.filter(
        produce_types__cooperative_items__isnull=False
    ).distinct()
    
    # Get featured products (most recent)
    featured_products = CooperativeProduce.objects.all().order_by('-created_at')[:8]
    
    # Get new arrivals
    new_arrivals = CooperativeProduce.objects.all().order_by('-created_at')[:4]
    
    # Get products by category for display
    fruits = CooperativeProduce.objects.filter(
        produce_type__category__slug='fruits'
    ).order_by('-created_at')[:4]
    
    vegetables = CooperativeProduce.objects.filter(
        produce_type__category__slug='vegetables'
    ).order_by('-created_at')[:4]
    
    context = {
        'categories': categories_with_products,
        'featured_products': featured_products,
        'new_arrivals': new_arrivals,
        'fruit_products': fruits,
        'vegetable_products': vegetables,
    }
    return render(request, 'shop/home.html', context)

def product_list(request):
    category_slug = request.GET.get('category')  # Changed from category_id to category_slug
    search_query = request.GET.get('search')
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    sort_by = request.GET.get('sort_by', 'id')
    
    products = CooperativeProduce.objects.all()
    
    if category_slug:
        # Filter by category slug instead of ID
        products = products.filter(produce_type__category__slug=category_slug)
    
    if search_query:
        products = products.filter(produce_type__name__icontains=search_query)
    
    if min_price:
        products = products.filter(produce_type__price_per_unit__gte=min_price)
    
    if max_price:
        products = products.filter(produce_type__price_per_unit__lte=max_price)
    
    if sort_by == 'price_low':
        products = products.order_by('produce_type__price_per_unit')
    elif sort_by == 'price_high':
        products = products.order_by('-produce_type__price_per_unit')
    elif sort_by == 'newest':
        products = products.order_by('-created_at')
    else:
        products = products.order_by('id')
    
    categories = Category.objects.all()
    
    context = {
        'products': products,
        'categories': categories,
        'selected_category': category_slug,
        'search_query': search_query,
        'min_price': min_price,
        'max_price': max_price,
        'sort_by': sort_by,
    }
    return render(request, 'shop/product_list.html', context)

def product_detail(request, product_id):
    product = get_object_or_404(CooperativeProduce, id=product_id)
    related_products = CooperativeProduce.objects.filter(
        produce_type__category=product.produce_type.category
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
            'message': f"{product.produce_type.name} added to your cart."
        })
    
    # Get the referring page if available
    referer = request.META.get('HTTP_REFERER')
    if referer:
        return redirect(referer)
    
    # Otherwise redirect to the product list page
    return redirect('shop:product_list')

def cart(request):
    cart = get_or_create_cart(request)
    
    context = {
        'cart': cart,
        'cart_items': cart.items.all(),
    }
    return render(request, 'shop/cart.html', context)

def update_cart(request, item_id):
    cart_item = get_object_or_404(CartItem, id=item_id)
    
    # For logged-in users, ensure the cart belongs to them
    if request.user.is_authenticated and cart_item.cart.user and cart_item.cart.user != request.user:
        messages.error(request, "You don't have permission to modify this cart.")
        return redirect('shop:cart')
    
    # For anonymous users, ensure the cart belongs to their session
    if not request.user.is_authenticated:
        cart_id = request.session.get('cart_id')
        if not cart_id or cart_item.cart.id != cart_id:
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

def remove_from_cart(request, item_id):
    cart_item = get_object_or_404(CartItem, id=item_id)
    
    # For logged-in users, ensure the cart belongs to them
    if request.user.is_authenticated and cart_item.cart.user and cart_item.cart.user != request.user:
        messages.error(request, "You don't have permission to modify this cart.")
        return redirect('shop:cart')
    
    # For anonymous users, ensure the cart belongs to their session
    if not request.user.is_authenticated:
        cart_id = request.session.get('cart_id')
        if not cart_id or cart_item.cart.id != cart_id:
            messages.error(request, "You don't have permission to modify this cart.")
            return redirect('shop:cart')
    
    # Remove the item
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

def checkout(request):
    cart = get_or_create_cart(request)
    
    # Check if cart is empty
    if cart.items.count() == 0:
        messages.warning(request, "Your cart is empty. Add some products before checkout.")
        return redirect('shop:product_list')
    
    # Check if user is authenticated
    if not request.user.is_authenticated:
        # Store the next URL in the session
        request.session['next'] = reverse('shop:checkout')
        messages.info(request, "Please log in to complete your checkout.")
        return redirect('shop:login')
    
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
        form = CustomAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            email = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=email, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f"Welcome back, {user.full_name}!")
                
                # Check if there's a next URL in the session
                next_url = request.session.get('next')
                if next_url:
                    del request.session['next']
                    return redirect(next_url)
                
                # Transfer session cart to user cart if needed
                session_cart_id = request.session.get('cart_id')
                if session_cart_id:
                    try:
                        session_cart = Cart.objects.get(id=session_cart_id)
                        user_cart, created = Cart.objects.get_or_create(user=user)
                        
                        # Transfer items from session cart to user cart
                        for item in session_cart.items.all():
                            try:
                                user_item = CartItem.objects.get(cart=user_cart, product=item.product)
                                user_item.quantity += item.quantity
                                user_item.save()
                            except CartItem.DoesNotExist:
                                item.cart = user_cart
                                item.save()
                        
                        # Delete the session cart
                        session_cart.delete()
                        del request.session['cart_id']
                    except Cart.DoesNotExist:
                        pass
                
                return redirect('shop:home')
            else:
                messages.error(request, "Invalid email or password.")
        else:
            messages.error(request, "Invalid email or password.")
    else:
        form = CustomAuthenticationForm()
    
    context = {
        'form': form
    }
    return render(request, 'shop/login.html', context)

def register_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f"Account created successfully. Welcome, {user.full_name}!")
            
            # Transfer session cart to user cart if needed
            session_cart_id = request.session.get('cart_id')
            if session_cart_id:
                try:
                    session_cart = Cart.objects.get(id=session_cart_id)
                    user_cart, created = Cart.objects.get_or_create(user=user)
                    
                    # Transfer items from session cart to user cart
                    for item in session_cart.items.all():
                        try:
                            user_item = CartItem.objects.get(cart=user_cart, product=item.product)
                            user_item.quantity += item.quantity
                            user_item.save()
                        except CartItem.DoesNotExist:
                            item.cart = user_cart
                            item.save()
                    
                    # Delete the session cart
                    session_cart.delete()
                    del request.session['cart_id']
                except Cart.DoesNotExist:
                    pass
            
            # Check if there's a next URL in the session
            next_url = request.session.get('next')
            if next_url:
                del request.session['next']
                return redirect(next_url)
                
            return redirect('shop:home')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        form = CustomUserCreationForm()
    
    context = {
        'form': form
    }
    return render(request, 'shop/register.html', context)

def logout_view(request):
    logout(request)
    messages.success(request, "You have been logged out successfully.")
    return redirect('shop:home')

