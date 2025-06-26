from .models import Cart

def cart(request):
    cart_obj = None
    if request.user.is_authenticated:
        try:
            cart_obj = Cart.objects.get(user=request.user)
        except Cart.DoesNotExist:
            pass
    else:
        session_key = request.session.session_key
        if session_key:
            try:
                cart_obj = Cart.objects.get(session_key=session_key)
            except Cart.DoesNotExist:
                pass
    
    return {
        'cart': cart_obj,
        'cart_total_items': cart_obj.total_items if cart_obj else 0,
        'cart_total_price': cart_obj.total_price if cart_obj else 0,
    }