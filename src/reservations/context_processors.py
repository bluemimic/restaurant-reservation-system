from src.reservations.cart import get_cart_count


def cart(request):
    return {"cart_item_count": get_cart_count(request)}
