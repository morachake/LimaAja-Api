from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from cooperative.models import CooperativeProduce, Category, ProduceType
from .models import Cart, CartItem, Order, OrderItem

def home(request):
    """
    Home page view showing featured products, categories, and promotions
    """
    # Get products with quantity > 0
    featured_products = CooperativeProduce.objects.filter(quantity__gt=0)[:8]
    categories = Category.objects.all()[:6]
    
    context = {
        'featured_products': featured_products,
        'categories': categories,
    }
    return render(request, 'shop/home.html', context)

def product_list(request):
    """
    View for listing all products with filtering options
    """
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
    
    # Sort products
    sort_by = request.GET.get('sort')
    if sort_by == 'price_low':
        products = products.order_by('produce_type__price_per_unit')
    elif sort_by == 'price_high':
        products = products.order_by('-produce_type__price_per_unit')
    elif sort_by == 'newest':
        products = products.order_by('-created_at')
    
    categories = Category.objects.all()
    
    context = {
        'products': products,
        'categories': categories,
        'current_category': category_slug,
        'current_sort': sort_by,
        'search_query': search_query,
    }
    return render(request, 'shop/product_list.html', context)

def product_detail(request, product_id):
    """
    View for showing product details
    """
    product = get_object_or_404(CooperativeProduce, id=product_id)
    related_products = CooperativeProduce.objects.filter(
        produce_type__category=product.produce_type.category
    ).exclude(id=product.id)[:4]
    
    context = {
        'product': product,
        'related_products': related_products,
    }
    return render(request, 'shop/product_detail.html', context)

def get_or_create_cart(request):
    """
    Helper function to get or create a cart for the current user/session
    """
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
    """
    View for adding a product to the cart
    """
    product = get_object_or_404(CooperativeProduce, id=product_id)
    cart = get_or_create_cart(request)
    
    quantity = int(request.POST.get('quantity', 1))
    
    # Check if the product is already in the cart
    try:
        cart_item = CartItem.objects.get(cart=cart, product=product)
        cart_item.quantity += quantity
        cart_item.save()
        messages.success(request, f'Updated quantity of {product.produce_type.name} in your cart.')
    except CartItem.DoesNotExist:
        CartItem.objects.create(cart=cart, product=product, quantity=quantity)
        messages.success(request, f'Added {product.produce_type.name} to your cart.')
    
    return redirect('shop:cart')

def cart(request):
    """
    View for showing the cart contents
    """
    cart = get_or_create_cart(request)
    
    context = {
        'cart': cart,
    }
    return render(request, 'shop/cart.html', context)

def update_cart(request, item_id):
    """
    View for updating cart item quantity
    """
    cart_item = get_object_or_404(CartItem, id=item_id)
    
    # Check if the user owns this cart item
    if request.user.is_authenticated:
        if cart_item.cart.user != request.user:
            messages.error(request, 'You do not have permission to modify this cart.')
            return redirect('shop:cart')
    else:
        cart_id = request.session.get('cart_id')
        if cart_item.cart.id != cart_id:
            messages.error(request, 'You do not have permission to modify this cart.')
            return redirect('shop:cart')
    
    quantity = int(request.POST.get('quantity', 1))
    
    if quantity > 0:
        cart_item.quantity = quantity
        cart_item.save()
        messages.success(request, 'Cart updated successfully.')
    else:
        cart_item.delete()
        messages.success(request, 'Item removed from cart.')
    
    return redirect('shop:cart')

def remove_from_cart(request, item_id):
    """
    View for removing an item from the cart
    """
    cart_item = get_object_or_404(CartItem, id=item_id)
    
    # Check if the user owns this cart item
    if request.user.is_authenticated:
        if cart_item.cart.user != request.user:
            messages.error(request, 'You do not have permission to modify this cart.')
            return redirect('shop:cart')
    else:
        cart_id = request.session.get('cart_id')
        if cart_item.cart.id != cart_id:
            messages.error(request, 'You do not have permission to modify this cart.')
            return redirect('shop:cart')
    
    cart_item.delete()
    messages.success(request, 'Item removed from cart.')
    
    return redirect('shop:cart')

@login_required
def checkout(request):
    """
    View for checkout process
    """
    cart = get_or_create_cart(request)
    
    if cart.item_count == 0:
        messages.error(request, 'Your cart is empty. Add some products before checkout.')
        return redirect('shop:cart')
    
    if request.method == 'POST':
        # Process the order
        shipping_address = request.POST.get('shipping_address')
        city = request.POST.get('city')
        state = request.POST.get('state')
        zip_code = request.POST.get('zip_code')
        phone = request.POST.get('phone')
        payment_method = request.POST.get('payment_method')
        
        # Create the order
        order = Order.objects.create(
            user=request.user,
            total_amount=cart.total,
            shipping_address=shipping_address,
            city=city,
            state=state,
            zip_code=zip_code,
            phone=phone,
            payment_method=payment_method,
        )
        
        # Create order items
        for cart_item in cart.items.all():
            OrderItem.objects.create(
                order=order,
                product=cart_item.product,
                price=cart_item.product.produce_type.price_per_unit,
                quantity=cart_item.quantity,
            )
        
        # Clear the cart
        cart.items.all().delete()
        
        messages.success(request, 'Your order has been placed successfully!')
        return redirect('shop:order_confirmation', order_id=order.id)
    
    context = {
        'cart': cart,
    }
    return render(request, 'shop/checkout.html', context)

@login_required
def order_confirmation(request, order_id):
    """
    View for order confirmation
    """
    order = get_object_or_404(Order, id=order_id, user=request.user)
    
    context = {
        'order': order,
    }
    return render(request, 'shop/order_confirmation.html', context)

@login_required
def order_history(request):
    """
    View for showing order history
    """
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    
    context = {
        'orders': orders,
    }
    return render(request, 'shop/order_history.html', context)

@login_required
def order_detail(request, order_id):
    """
    View for showing order details
    """
    order = get_object_or_404(Order, id=order_id, user=request.user)
    
    context = {
        'order': order,
    }
    return render(request, 'shop/order_detail.html', context)

