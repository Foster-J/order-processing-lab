"""Shopping cart business logic."""
from models import CartLine

DISCOUNTS = {
    'WELCOME10': ('pct', 0.10),
    'STUDENT20': ('pct', 0.20),
    'SAVE15': ('flat', 15.00),
    'FREESHIP': ('none', 0),
}


def _is_positive_int(value):
    # bool is a subclass of int, so True would otherwise count as quantity 1.
    return isinstance(value, int) and not isinstance(value, bool) and value > 0


class ShoppingCart:
    def __init__(self, user_id, repository):
        self.user_id = user_id
        self.repository = repository
        self.lines = []
        self.discount_code = None

    def add_item(self, sku, quantity):
        # Fix defect 1: reject zero, and negative quantities.
        if not _is_positive_int(quantity):
            print('Quantity must be a positive whole number')
            return False
        product = self.repository.get_product(sku)
        if not product:
            print('Unknown product')
            return False
        existing = next((x for x in self.lines if x.sku == sku), None)
        # Fix defect 2 include the quantity already in the cart in the stock check.
        already_in_cart = existing.quantity if existing else 0
        if product.stock < already_in_cart + quantity:
            print('Not enough stock')
            return False
        if existing:
            existing.quantity += quantity
        else:
            self.lines.append(CartLine(sku, product.name, product.price, quantity))
        return True

    def remove_item(self, sku, quantity=None):
        # Fix defect 3: a negative or zero quantity used to increase the line.
        if quantity is not None and not _is_positive_int(quantity):
            print('Quantity must be a positive whole number')
            return False
        for line in self.lines:
            if line.sku == sku:
                if quantity is None or quantity >= line.quantity:
                    self.lines.remove(line)
                else:
                    line.quantity -= quantity
                return True
        print('Item not found')
        return False

    def subtotal(self):
        return round(sum(line.unit_price * line.quantity for line in self.lines), 2)

    def total(self):
        # Fix defect 4 the total is recalculated from the current subtotal.
        # Fix defect 5 the total never drops below 0 and is rounded to cents.
        amount = self.subtotal()
        if self.discount_code:
            kind, value = DISCOUNTS[self.discount_code]
            if kind == 'pct':
                amount = amount * (1 - value)
            elif kind == 'flat':
                amount = amount - value
        return round(max(amount, 0.0), 2)

    def apply_discount(self, code):
        # Fix defect 4 only one coupon is active at a time. Applying a new code
        # replaces the old one instead of stacking.
        if code not in DISCOUNTS:
            print('Invalid coupon')
            return False
        if code == 'FREESHIP':
            print('Shipping is free')
        self.discount_code = code
        return True

    def load(self):
        # Fix defect 6 calling load() twice used to double every quantity.
        # The saved cart replaces the lines instead of being added to them.
        self.lines = []
        for sku, quantity in self.repository.get_saved_cart(self.user_id):
            self.add_item(sku, quantity)

    def save(self):
        self.repository.save_cart(self.user_id, self.lines)
