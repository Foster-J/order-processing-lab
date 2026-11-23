"""Unit tests for ShoppingCart (defects 1-6)."""
import pytest
from cart import ShoppingCart


# Defect 1: quantity validation
def test_add_item_rejects_invalid_quantities(cart):
    assert cart.add_item('USB-01', 0) is False
    assert cart.add_item('USB-01', -5) is False
    assert cart.lines == []


# Defect 2: stock check includes what is already in the cart
def test_add_item_cannot_exceed_stock_across_multiple_adds(cart):
    assert cart.add_item('LAP-01', 4)
    assert cart.add_item('LAP-01', 2) is False
    assert cart.lines[0].quantity == 4


# Defect 3: remove_item must not accept negative quantities
def test_remove_item_rejects_negative_quantity(cart):
    cart.add_item('USB-01', 2)
    assert cart.remove_item('USB-01', -3) is False
    assert cart.lines[0].quantity == 2         


# Defect 4: coupons must not stack
def test_discounts_do_not_stack(cart):
    cart.add_item('USB-01', 10)                
    cart.apply_discount('STUDENT20')
    cart.apply_discount('WELCOME10')          
    assert cart.discount_code == 'WELCOME10'
    assert cart.total() == pytest.approx(89.91)


# Defect 4: total must follow cart edits made after a discount (and Defect 5: rounding)
def test_total_updates_when_cart_edited_after_discount(cart):
    cart.add_item('USB-01', 1)                 
    cart.apply_discount('WELCOME10')
    cart.add_item('MOU-01', 1)                 
    assert cart.total() == 35.95               


# Defect 5: flat discount must not produce a negative total
def test_flat_discount_never_goes_negative(cart):
    cart.add_item('USB-01', 1)                 
    cart.apply_discount('SAVE15')
    assert cart.total() == 0.0


# Defect 6: repeated loads must not duplicate quantities
def test_loading_saved_cart_twice_does_not_duplicate(repo):
    c = ShoppingCart('alice', repo)
    c.add_item('USB-01', 3)
    c.save()
    c.load()
    c.load()
    assert len(c.lines) == 1
    assert c.lines[0].quantity == 3
