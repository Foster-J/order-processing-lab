"""SQLite persistence."""
import sqlite3
from contextlib import closing
from models import Product


class StoreRepository:
    def __init__(self, db_path='shop.db'):
        self.db_path = db_path

    def connect(self):
        return sqlite3.connect(self.db_path, timeout=2)

    def get_product(self, sku):
        # Fix defect 7 parameterized query instead of an f-string, prevents SQL injection.
        with closing(self.connect()) as conn:
            row = conn.execute('SELECT sku, name, price, stock FROM products WHERE sku = ?',
                               (sku,)).fetchone()
        return Product(*row) if row else None

    def get_saved_cart(self, user_id):
        # Fix defect 7 parameterized query instead of an f-string, prevents SQL injection.
        with closing(self.connect()) as conn:
            return conn.execute('SELECT sku, quantity FROM saved_cart WHERE user_id = ?',
                                (user_id,)).fetchall()

    def save_cart(self, user_id, lines):
        with closing(self.connect()) as conn, conn:
            conn.execute('DELETE FROM saved_cart WHERE user_id = ?', (user_id,))
            conn.executemany('INSERT INTO saved_cart VALUES (?, ?, ?)',
                             [(user_id, line.sku, line.quantity) for line in lines])

    def reserve_stock(self, lines):
        """Decrement stock for every line in a single transaction.

        Returns True if every line had enough stock. If any line is short,
        nothing is changed and False is returned (stock can never go negative).
        """
        with closing(self.connect()) as conn:
            try:
                for line in lines:
                    cur = conn.execute(
                        'UPDATE products SET stock = stock - ? WHERE sku = ? AND stock >= ?',
                        (line.quantity, line.sku, line.quantity))
                    if cur.rowcount != 1:
                        conn.rollback()
                        return False
                conn.commit()
                return True
            except sqlite3.Error:
                conn.rollback()
                raise

    def release_stock(self, lines):
        """Return previously reserved stock (used when payment fails)."""
        with closing(self.connect()) as conn, conn:
            for line in lines:
                conn.execute('UPDATE products SET stock = stock + ? WHERE sku = ?',
                             (line.quantity, line.sku))

    def update_stock(self, sku, quantity):
        """Kept for compatibility; refuses to push stock below zero."""
        with closing(self.connect()) as conn, conn:
            cur = conn.execute('UPDATE products SET stock = stock - ? WHERE sku = ? AND stock >= ?',
                               (quantity, sku, quantity))
            return cur.rowcount == 1

    def save_order(self, user_id, amount, status, request_id):
        with closing(self.connect()) as conn, conn:
            cur = conn.execute('INSERT INTO orders(user_id, amount, status, request_id) VALUES (?, ?, ?, ?)',
                               (user_id, amount, status, request_id))
            return cur.lastrowid

    def find_order_by_request_id(self, request_id):
        """Return (id, user_id, amount, status) for an earlier order with this request id, or None."""
        with closing(self.connect()) as conn:
            return conn.execute('SELECT id, user_id, amount, status FROM orders WHERE request_id = ?',
                                (request_id,)).fetchone()

    def list_orders(self, user_id):
        # Fix defect 8 the query ignored user_id and returned every customer's orders.
        with closing(self.connect()) as conn:
            return conn.execute('SELECT id, user_id, amount, status FROM orders '
                                'WHERE user_id = ? ORDER BY id DESC', (user_id,)).fetchall()
