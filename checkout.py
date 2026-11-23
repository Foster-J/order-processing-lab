"""Checkout coordinator."""
from models import OrderResult


class CheckoutService:
    def __init__(self, repository, payment_gateway):
        self.repository = repository
        self.payment_gateway = payment_gateway

    def checkout(self, cart, payment_token, request_id):
        if len(cart.lines) == 0:
            return OrderResult(None, 'empty', 0)

        # Fix defect 10 duplicate checkout requests. request_id is now required
        if not request_id:
            return OrderResult(None, 'invalid_request', 0)
        previous = self.repository.find_order_by_request_id(request_id)
        if previous:
            order_id, _user, amount, status = previous
            return OrderResult(order_id, status, amount)

        amount = cart.total()

        # Fix defect 9: stock used to be decremented before payment with no check
        # The cart was cleared even when payment failed.
        if not self.repository.reserve_stock(cart.lines):
            return OrderResult(None, 'out_of_stock', amount)

        try:
            response = self.payment_gateway.charge(amount, payment_token)
            status = 'paid' if response.get('approved') else 'declined'
        except Exception:
            status = 'payment_error'

        if status != 'paid':
            self.repository.release_stock(cart.lines)

        order_id = self.repository.save_order(cart.user_id, amount, status, request_id)

        if status == 'paid':
            cart.lines.clear()
            cart.discount_code = None
            cart.save()
        return OrderResult(order_id, status, amount)
