def cart_processor(request):
    """
    Context processor to add cart count, items and total to all templates
    """
    cart_count = 0
    cart_items = []
    cart_total = 0
    
    if request.user.is_authenticated:
        # Get cart count from session to avoid database queries on every request
        if 'cart_count' in request.session:
            cart_count = request.session.get('cart_count', 0)
        else:
            # If not in session, calculate it (this should be updated when cart is modified)
            from shop.models import Cart, CartItem
            
            # Get the user's cart
            try:
                cart = Cart.objects.get(user=request.user)
                # Count items in the cart
                cart_items = CartItem.objects.filter(cart=cart).select_related('product', 'product__produce_type')
                cart_count = sum(item.quantity for item in cart_items)
                cart_total = sum(item.subtotal for item in cart_items)
                request.session['cart_count'] = cart_count
                request.session['cart_total'] = float(cart_total)
            except Cart.DoesNotExist:
                # User doesn't have a cart yet
                cart_count = 0
                request.session['cart_count'] = 0
                request.session['cart_total'] = 0
    
    # Add cart items to the request object for use in templates
    request.cart_items = cart_items
    
    return {
        'cart_count': cart_count,
        'cart_total': request.session.get('cart_total', 0)
    }

