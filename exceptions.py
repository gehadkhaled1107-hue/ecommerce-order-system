"""
exceptions.py
Person 4 — Reports & Integration Owner

Collects every custom exception defined across the team's modules into one
place, so main.py can do a single clean import instead of three scattered
ones. This module RE-EXPORTS the real exception classes (does not redefine
them), so `except InsufficientStockError` still correctly catches whatever
person1.py's Product.reduce_stock() actually raises — isinstance checks stay
valid because these are the same class objects, just imported here too.

Usage:
    from exceptions import *
    # or
    from exceptions import InsufficientStockError, InvalidCustomerDataError
"""

# ---- Product & inventory errors (Ahmed — person1.py) ----
from person1 import (
    ProductError,
    InvalidProductCodeError,
    InsufficientStockError,
    ProductNotFoundError,
    InvalidQuantityError,
)

# ---- Customer & cart errors (Ali — customers.py) ----
from customers import (
    InvalidCustomerDataError,
    CartError,
)

# ---- Checkout & order errors (Gehad — checkout.py) ----
from checkout import (
    ECommerceError,
    InvalidOrderStateError,
    InvalidPaymentError,
    EmptyCartError,
    OrderNotFoundError,
)

__all__ = [
    # products
    "ProductError",
    "InvalidProductCodeError",
    "InsufficientStockError",
    "ProductNotFoundError",
    "InvalidQuantityError",
    # customers/cart
    "InvalidCustomerDataError",
    "CartError",
    # checkout/orders
    "ECommerceError",
    "InvalidOrderStateError",
    "InvalidPaymentError",
    "EmptyCartError",
    "OrderNotFoundError",
]
