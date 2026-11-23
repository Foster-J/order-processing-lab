"""Shared fixtures: every test gets its own temporary SQLite database."""
import pytest
from setup_db import initialize
from repository import StoreRepository
from cart import ShoppingCart


@pytest.fixture
def repo(tmp_path):
    db = tmp_path / 'test.db'
    initialize(str(db))
    return StoreRepository(str(db))


@pytest.fixture
def cart(repo):
    return ShoppingCart('student', repo)


class ExplodingGateway:
    """Fake gateway that simulates an unexpected payment failure."""
    def __init__(self):
        self.calls = []

    def charge(self, amount, payment_token):
        self.calls.append((amount, payment_token))
        raise ConnectionError('gateway timeout')


@pytest.fixture
def exploding_gateway():
    return ExplodingGateway()
