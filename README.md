# Order-processing system — student starter

This application intentionally contains defects. Your assignment has three parts only:

1. Identify and correct at least 8 meaningful defects.
2. Write at least 12 automated unit tests with `pytest`.
3. Add `.github/workflows/tests.yml` to run tests on pushes and pull requests.

## Application files

- `models.py`: domain objects
- `cart.py`: shopping cart and discounts
- `repository.py`: SQLite products, saved carts, inventory and orders
- `checkout.py`: checkout workflow
- `payments.py`: simulated payment gateway
- `setup_db.py` and `demo.py`: demo database and execution
- `tests/test_smoke.py`: minimal smoke tests (not a solution)

## Running locally

```bash
python -m pip install -r requirements.txt
python -m pytest -q
python setup_db.py
python demo.py
```

Use temporary databases and fake payment tokens for unit tests. No real payment credentials are required.

---

# Order-Processing System: Defect Fixes and Unit Tests

This repository contains:

- fixes for 10 defects across `cart.py`, `repository.py`, `checkout.py` and `setup_db.py`
- 14 pytest unit tests in `tests/`
- a GitHub Actions workflow in `.github/workflows/tests.yml`

# Defects found and fixed

| 1 | `cart.py` `add_item` | Zero, and negative quantities were accepted. Quantities must be positive numbers.
| 2 | `cart.py` `add_item` | The stock check ignored items already in the cart. The check now compares stock with items already in the cart.
| 3 | `cart.py` `remove_item` | A negative quantity increased the line. Now Zero and negative quantities are rejected. 
| 4 | `cart.py` `apply_discount` | Discounts were calculated from self.total(), so coupons stacked. Adding or removing items after applying a coupon left the price unchanged. Now only the coupon code is stored. Now total() recalculates from the current subtotal every time, and a new coupon replaces the old one.
| 5 | `cart.py` `total` | `SAVE15` on a $9.99 cart gave a total of -$5.01. Had floating point errors. With the fix the total can't go below zero and is rounded to cents.
| 6 | `cart.py` `load` | load() appended saved items to existing lines, so loading twice doubled every quantity. Now load() clears the in memory cart first and the saved cart replaces it.
| 7 | `repository.py` `get_product`, `get_saved_cart` | SQL was built with f-strings, so SQL injection could occur. Now have paramaterized queries.
| 8 | `repository.py` `list_orders` | user_id was ignored, so every customer's orders were returned. Added WHERE user_id = ?. 
| 9 | `checkout.py`, `repository.py` | Stock was decremented before payment with no check, which means it could go negative. A declined or failed payment still used stock and emptied the cart. New reserve_stock() decrements every line in one transaction and rolls back entirely if any line is short. The cart is only cleared after a successful payment.
| 10 | `checkout.py`, `setup_db.py` | request_id was saved but never checked, so a retried checkout charged the customer twice and created two orders. Now request_id is required.

# Assumptions
- Applying a new valid code replaces the old one. An invalid code is rejected and the current coupon stays.
- A request_id identifies one checkout attempt. Repeating it returns the original result.
- Stock is checked twice. once when an item is added to the cart, and again at checkout.
- The order total is the discounted amount charged.

# Unit tests

14 unit tests:

| # | Test | Defect |
|---|
| 1 | `test_add_item_rejects_invalid_quantities` | 1 |
| 2 | `test_add_item_cannot_exceed_stock_across_multiple_adds` | 2 |
| 3 | `test_remove_item_rejects_negative_quantity` | 3 |
| 4 | `test_discounts_do_not_stack` | 4 |
| 5 | `test_total_updates_when_cart_edited_after_discount` | 4, 5 |
| 6 | `test_flat_discount_never_goes_negative` | 5 |
| 7 | `test_loading_saved_cart_twice_does_not_duplicate` | 6 |
| 8 | `test_get_product_is_not_vulnerable_to_sql_injection` | 7 |
| 9 | `test_list_orders_filters_by_user` | 8 |
| 10 | `test_successful_checkout_charges_discounted_total_and_clears_cart` | 4, 9 |
| 11 | `test_declined_payment_keeps_stock_and_cart` | 9 |
| 12 | `test_unexpected_payment_error_keeps_stock_and_cart` | 9 |
| 13 | `test_checkout_fails_when_stock_changed_since_adding` | 9 |
| 14 | `test_repeated_request_id_does_not_charge_twice` | 10 |

Tests 1–7 are in `tests/test_cart.py`, 8–9 in `tests/test_repository.py` and 10–14 in `tests/test_checkout.py`.

# Test results

python -m pytest -q
16 passed in 0.35s

# CI

GitHub Actions runs `python -m pytest -q` on every push and pull request (`.github/workflows/tests.yml`).
