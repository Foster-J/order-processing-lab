"""Unit tests for StoreRepository (defects 7 and 8)."""


# Defect 7: SQL injection
def test_get_product_is_not_vulnerable_to_sql_injection(repo):
    assert repo.get_product("x' OR '1'='1") is None
    assert repo.get_product('USB-01').name == 'USB cable'


# Defect 8: list_orders only returns the requested user's orders
def test_list_orders_filters_by_user(repo):
    repo.save_order('alice', 10.0, 'paid', 'req-a')
    repo.save_order('bob', 20.0, 'paid', 'req-b')
    orders = repo.list_orders('alice')
    assert len(orders) == 1
    assert orders[0][1] == 'alice'
