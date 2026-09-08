"""
customers.py
Person 2 — Customer & Cart Owner
Mini E-Commerce Order System (SIC Chapter 3 Capstone)

This module is designed to plug into the rest of the team:
- Expects a Product-like object from Person 1's products.py with attributes:
  code (str), name (str), price (float), stock (int)
  and a method: reduce_stock(quantity) -> None (raises InsufficientStockError)
- Exposes Cart items in a simple, iterable structure so Person 3 (checkout)
  and Person 4 (reports) can consume it easily (see get_items()).
"""

import re


# ---------- Custom Exceptions ----------

class InvalidCustomerDataError(Exception):
    """Raised when customer name, email, or phone fails validation."""
    pass


class CartError(Exception):
    """Raised for invalid cart operations (bad quantity, empty product, etc.)."""
    pass


# ---------- Regex Validators ----------
# Kept as standalone functions so Person 1/3/4 can reuse them if needed.

EMAIL_PATTERN = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")
PHONE_PATTERN = re.compile(r"^01[0125][0-9]{8}$")  # Egyptian mobile format, adjust if needed


def validate_email(email: str) -> bool:
    return bool(EMAIL_PATTERN.match(email.strip()))


def validate_phone(phone: str) -> bool:
    return bool(PHONE_PATTERN.match(phone.strip()))


# ---------- Customer Classes (OOP: base + subclass, polymorphism) ----------

class Customer:
    """Base class for a regular customer."""

    def __init__(self, customer_id: str, name: str, email: str, phone: str):
        if not name or not name.strip():
            raise InvalidCustomerDataError("Customer name cannot be empty.")
        if not validate_email(email):
            raise InvalidCustomerDataError(f"Invalid email format: {email}")
        if not validate_phone(phone):
            raise InvalidCustomerDataError(f"Invalid phone format: {phone}")

        self.customer_id = customer_id
        self.name = name.strip()
        self.email = email.strip()
        self.phone = phone.strip()
        self.cart = Cart()

    def discount_rate(self) -> float:
        """Polymorphic hook — overridden by PremiumCustomer."""
        return 0.0

    def display_info(self) -> str:
        """Polymorphic display — PremiumCustomer overrides this too."""
        return (f"[Customer] ID: {self.customer_id} | Name: {self.name} | "
                f"Email: {self.email} | Phone: {self.phone}")

    def __str__(self):
        return self.display_info()


class PremiumCustomer(Customer):
    """Premium customer — gets a discount rate and a different display."""

    def __init__(self, customer_id: str, name: str, email: str, phone: str,
                 loyalty_points: int = 0):
        super().__init__(customer_id, name, email, phone)
        self.loyalty_points = loyalty_points

    def discount_rate(self) -> float:
        # Real behavioral difference, not just a renamed method
        if self.loyalty_points >= 500:
            return 0.15
        return 0.10

    def display_info(self) -> str:
        return (f"[Premium] ID: {self.customer_id} | Name: {self.name} | "
                f"Email: {self.email} | Phone: {self.phone} | "
                f"Points: {self.loyalty_points} | Discount: {self.discount_rate() * 100:.0f}%")


# ---------- Cart ----------

class CartItem:
    """Wraps a product with the quantity requested — keeps Cart iterable/clean."""

    def __init__(self, product, quantity: int):
        self.product = product
        self.quantity = quantity

    @property
    def subtotal(self) -> float:
        return self.product.price * self.quantity

    def __str__(self):
        return f"{self.product.name} x{self.quantity} = {self.subtotal:.2f}"


class Cart:
    """Holds CartItems for one customer. Iterable so Person 3/4 can loop over it."""

    def __init__(self):
        self._items = []  # list[CartItem]

    def add_item(self, product, quantity: int = 1):
        if quantity <= 0:
            raise CartError("Quantity must be greater than zero.")
        if product is None:
            raise CartError("Cannot add an empty product to the cart.")
        if hasattr(product, "stock") and quantity > product.stock:
            raise CartError(f"Not enough stock for '{product.name}'. "
                             f"Available: {product.stock}, requested: {quantity}")

        # If product already in cart, just increase quantity
        for item in self._items:
            if item.product.code == product.code:
                item.quantity += quantity
                return
        self._items.append(CartItem(product, quantity))

    def remove_item(self, product_code: str):
        before = len(self._items)
        self._items = [i for i in self._items if i.product.code != product_code]
        if len(self._items) == before:
            raise CartError(f"Product code '{product_code}' not found in cart.")

    def get_items(self):
        """Returns the list of CartItem objects — used by checkout/reports."""
        return list(self._items)

    def is_empty(self) -> bool:
        return len(self._items) == 0

    def clear(self):
        self._items = []

    # Makes `for item in cart` work directly (iterable requirement)
    def __iter__(self):
        return iter(self._items)

    def __len__(self):
        return len(self._items)


# ---------- Simple manual test (remove or guard with __main__ before final submission) ----------

if __name__ == "__main__":
    # Minimal fake product just to test this module in isolation.
    class FakeProduct:
        def __init__(self, code, name, price, stock):
            self.code, self.name, self.price, self.stock = code, name, price, stock

    try:
        c1 = Customer("C001", "Ali Farouk", "ali@example.com", "01012345678")
        p1 = PremiumCustomer("C002", "Sara", "sara@example.com", "01298765432", loyalty_points=600)

        print(c1)
        print(p1)

        prod = FakeProduct("P001", "Wireless Mouse", 250.0, 10)
        c1.cart.add_item(prod, 2)
        for item in c1.cart:
            print(item)

    except InvalidCustomerDataError as e:
        print("Customer error:", e)
    except CartError as e:
        print("Cart error:", e)
