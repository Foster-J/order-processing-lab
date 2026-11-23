"""Unit tests for CheckoutService (defects 9 and 10)."""
import pytest
from checkout import CheckoutService
from payments import FakePaymentGateway


def test_successful_checkout_charges_discounted_total_and_clears_cart(repo, cart):
    cart.add_item('USB-01', 10)
    cart.apply_discount('WELCOME10')
    gateway = FakePaymentGateway()
    result = CheckoutService(repo, gateway).checkout(cart, 'TEST_TOKEN', 'req-1')
    assert result.status == 'paid'
    assert gateway.calls == [(89.91, 'TEST_TOKEN')]
    assert repo.get_product('USB-01').stock == 40
    assert cart.lines == []


# Defect 9: a declined payment must not consume stock or empty the cart
def test_declined_payment_keeps_stock_and_cart(repo, cart):
    cart.add_item('USB-01', 3)
    result = CheckoutService(repo, FakePaymentGateway(should_approve=False)).checkout(
        cart, 'TEST_TOKEN', 'req-1')
    assert result.status == 'declined'
    assert repo.get_product('USB-01').stock == 50
    assert cart.lines[0].quantity == 3


# Defect 9: an unexpected gateway error is handled the same way
def test_unexpected_payment_error_keeps_stock_and_cart(repo, cart, exploding_gateway):
    cart.add_item('MOU-01', 2)
    result = CheckoutService(repo, exploding_gateway).checkout(cart, 'TEST_TOKEN', 'req-1')
    assert result.status == 'payment_error'
    assert repo.get_product('MOU-01').stock == 20
    assert len(cart.lines) == 1


# Defect 9: stock that ran out after adding to the cart is caught before charging
def test_checkout_fails_when_stock_changed_since_adding(repo, cart):
    cart.add_item('LAP-01', 5)
    repo.update_stock('LAP-01', 3)                 
    gateway = FakePaymentGateway()
    result = CheckoutService(repo, gateway).checkout(cart, 'TEST_TOKEN', 'req-1')
    assert result.status == 'out_of_stock'
    assert gateway.calls == []                     
    assert repo.get_product('LAP-01').stock == 2   


# Defect 10: a repeated request must not charge twice
def test_repeated_request_id_does_not_charge_twice(repo, cart):
    gateway = FakePaymentGateway()
    service = CheckoutService(repo, gateway)
    cart.add_item('USB-01', 1)
    first = service.checkout(cart, 'TEST_TOKEN', 'req-dup')
    cart.add_item('USB-01', 1)                     
    second = service.checkout(cart, 'TEST_TOKEN', 'req-dup')
    assert second.order_id == first.order_id
    assert len(gateway.calls) == 1
    assert repo.get_product('USB-01').stock == 49
