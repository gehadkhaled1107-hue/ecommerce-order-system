# person1.py
# ============================================================
# PERSON 1 – PRODUCTS & INVENTORY OWNER (Complete Module)
# All code combined into one file for easy testing.
# ============================================================

import re
import json
import os
from abc import ABC, abstractmethod
from datetime import datetime


# ============================================================
# SECTION 1: CUSTOM EXCEPTIONS
# ============================================================

class ProductError(Exception):
    """Base exception for product-related errors."""
    pass

class InvalidProductCodeError(ProductError):
    """Raised when product code format is invalid."""
    pass

class InsufficientStockError(ProductError):
    """Raised when trying to purchase more than available stock."""
    pass

class ProductNotFoundError(ProductError):
    """Raised when a product code doesn't exist in inventory."""
    pass

class InvalidQuantityError(ProductError):
    """Raised when a quantity for stock/cart operations is not a positive number."""
    pass


# ============================================================
# SECTION 2: PRODUCT CODE VALIDATION (REGEX)
# ============================================================

def validate_product_code(code):
    """
    Validates product code format: must start with a capital letter,
    followed by a dash, followed by exactly 4 digits.
    Examples: P-1234, D-2001, S-3001, X-9999
    Returns True if valid, False otherwise.
    """
    pattern = r'^[A-Z]-\d{4}$'   # Accepts any capital letter (P, D, S, etc.)
    return bool(re.match(pattern, code))


# ============================================================
# SECTION 3: CLASSES (MODELS)
# ============================================================

# ---------- PRODUCT HIERARCHY ----------

class Product(ABC):
    """Abstract base class for all products."""

    def __init__(self, code, name, price, stock, product_type):
        # Validate product code format using the regex above
        if not validate_product_code(code):
            raise InvalidProductCodeError(f"Invalid product code format: {code}")

        self.code = code
        self.name = name
        self.price = price
        self.stock = stock
        self.product_type = product_type  # "Physical", "Digital", "Service"

    @abstractmethod
    def get_description(self):
        """Polymorphic method – returns product-specific description."""
        pass

    @abstractmethod
    def calculate_shipping(self):
        """Polymorphic method – returns shipping cost (0 for digital/service)."""
        pass

    def reduce_stock(self, quantity):
        """
        Core inventory logic – decreases stock, raises error if insufficient.
        Also prevents negative/zero quantities.
        """
        if quantity <= 0:
            raise InvalidQuantityError(f"Quantity must be positive, got {quantity}.")
        if quantity > self.stock:
            raise InsufficientStockError(
                f"Not enough stock for {self.code}. Available: {self.stock}, Requested: {quantity}"
            )
        self.stock -= quantity

    def __str__(self):
        return f"{self.code} | {self.name} | ${self.price:.2f} | Stock: {self.stock}"


class PhysicalProduct(Product):
    """Physical goods with weight-based shipping."""

    def __init__(self, code, name, price, stock, weight, shipping_cost_per_kg=5.0):
        super().__init__(code, name, price, stock, "Physical")
        self.weight = weight
        self.shipping_cost_per_kg = shipping_cost_per_kg

    def get_description(self):
        return f"Physical item – {self.name}. Weighs {self.weight}kg. Ships in 3-5 days."

    def calculate_shipping(self):
        return self.weight * self.shipping_cost_per_kg


class DigitalProduct(Product):
    """Digital goods – no shipping, instant delivery."""

    def __init__(self, code, name, price, stock, download_link, file_size_mb):
        super().__init__(code, name, price, stock, "Digital")
        self.download_link = download_link
        self.file_size_mb = file_size_mb

    def get_description(self):
        return f"Digital item – {self.name}. Instant download ({self.file_size_mb} MB)."

    def calculate_shipping(self):
        return 0.0  # Digital products have no shipping cost


class Service(Product):
    """Service products – no shipping, time-based."""

    def __init__(self, code, name, price, stock, duration_hours, provider):
        super().__init__(code, name, price, stock, "Service")
        self.duration_hours = duration_hours
        self.provider = provider

    def get_description(self):
        return f"Service – {self.name} by {self.provider}. Duration: {self.duration_hours}h."

    def calculate_shipping(self):
        return 0.0  # Services have no shipping cost


# ---------- CUSTOMER HIERARCHY ----------
# NOTE: Customer / PremiumCustomer are no longer defined here.
# The team decided customers.py (Ali) is the single source of truth for
# customers, since it has the real regex validation for email/phone.
# They are imported below in the integration import block.

# NOTE: Order is no longer defined here either. checkout.py (Gehad) owns
# Order (with its status state machine) and OrderProcessingManager (order
# creation/lifecycle) as the single source of truth for orders, per the
# team's integration decision. Imported below.


# ---------- ORDER MANAGER (CONTAINER + ITERATOR) ----------

class OrderManager:
    """
    Main data container for the entire application.
    Owns all collections and provides an iterator for the product catalog.
    """

    def __init__(self):
        self.products = []          # list of Product objects
        self.customers = []         # list of Customer objects
        # NOTE: orders are NOT stored here anymore. They live inside
        # OrderProcessingManager.orders (checkout.py), keyed by order_id.
        # NOTE: cart is NOT stored here either - each Customer object
        # (customers.py) owns its own .cart (a Cart instance).

    # ---------- Product management ----------
    def add_product(self, product):
        """Add a product to the catalog. Prevent negative stock."""
        if product.stock < 0:
            raise ValueError("Stock cannot be negative.")
        if self.find_product_by_code(product.code):
            raise ValueError(f"Product with code {product.code} already exists.")
        self.products.append(product)

    def find_product_by_code(self, code):
        """Return a product object or None."""
        for p in self.products:
            if p.code == code:
                return p
        return None

    def get_product_or_raise(self, code):
        """Return a product or raise ProductNotFoundError."""
        product = self.find_product_by_code(code)
        if product is None:
            raise ProductNotFoundError(f"Product '{code}' not found in inventory.")
        return product

    # ---------- Stock management ----------
    def reduce_stock(self, product_code, quantity):
        """Decrease stock for a product (used during checkout)."""
        product = self.get_product_or_raise(product_code)
        product.reduce_stock(quantity)

    # ---------- Customer management ----------
    def add_customer(self, customer):
        self.customers.append(customer)

    def find_customer_by_email(self, email):
        for c in self.customers:
            if c.email == email:
                return c
        return None

    # NOTE: order storage/creation now lives in checkout.py's
    # OrderProcessingManager (self.orders there is keyed by order_id).
    # This manager no longer keeps its own self.orders list; reports.py
    # instead reads orders directly from the OrderProcessingManager.
    #
    # NOTE: create_discount_engine() removed from here — the team decided
    # to use checkout.py's make_discount_engine(customer) as the single
    # discount-engine closure, since it works against a real customer
    # object (and thus each PremiumCustomer's own discount_rate) rather
    # than a hardcoded {"Premium":..., "Regular":...} table.

    # ---------- ITERATOR (REQUIRED CONCEPT) ----------
    # This makes the product catalog iterable:  for product in store:
    def __iter__(self):
        self._index = 0
        return self

    def __next__(self):
        if self._index < len(self.products):
            result = self.products[self._index]
            self._index += 1
            return result
        else:
            raise StopIteration

    # ---------- FUNCTIONAL PYTHON: filter (REQUIRED CONCEPT) ----------
    def get_low_stock_products(self, threshold=10):
        """
        Return products whose stock is at or below `threshold`, sorted from
        lowest stock to highest. Uses filter() to select the items and a
        lambda as the sort key -- both required Chapter 3 concepts, and this
        lives here (not in the reporting module) because low-stock detection
        is inventory logic, not a report-formatting concern.
        """
        low_stock = list(filter(lambda p: p.stock <= threshold, self.products))
        low_stock.sort(key=lambda p: p.stock)
        return low_stock

    # ---------- Utility ----------
    def clear_all_data(self):
        """Used before loading from JSON."""
        self.products.clear()
        self.customers.clear()
        # orders live in OrderProcessingManager.orders now; that dict is
        # cleared separately wherever this manager's data is reloaded.


# ============================================================
# SECTION 4: JSON PERSISTENCE + SAMPLE DATA
# ============================================================

# ---------- CONVERSION HELPERS (dict ↔ object) ----------

def _product_to_dict(product):
    """Convert any Product subclass to a dictionary for JSON."""
    base = {
        "class": product.__class__.__name__,
        "code": product.code,
        "name": product.name,
        "price": product.price,
        "stock": product.stock,
        "product_type": product.product_type,
    }
    # Add subclass-specific fields
    if isinstance(product, PhysicalProduct):
        base.update({
            "weight": product.weight,
            "shipping_cost_per_kg": product.shipping_cost_per_kg,
        })
    elif isinstance(product, DigitalProduct):
        base.update({
            "download_link": product.download_link,
            "file_size_mb": product.file_size_mb,
        })
    elif isinstance(product, Service):
        base.update({
            "duration_hours": product.duration_hours,
            "provider": product.provider,
        })
    return base

def _dict_to_product(data):
    """Recreate a Product subclass from a dictionary."""
    class_name = data.get("class")
    if class_name == "PhysicalProduct":
        return PhysicalProduct(
            code=data["code"],
            name=data["name"],
            price=data["price"],
            stock=data["stock"],
            weight=data["weight"],
            shipping_cost_per_kg=data.get("shipping_cost_per_kg", 5.0)
        )
    elif class_name == "DigitalProduct":
        return DigitalProduct(
            code=data["code"],
            name=data["name"],
            price=data["price"],
            stock=data["stock"],
            download_link=data["download_link"],
            file_size_mb=data["file_size_mb"]
        )
    elif class_name == "Service":
        return Service(
            code=data["code"],
            name=data["name"],
            price=data["price"],
            stock=data["stock"],
            duration_hours=data["duration_hours"],
            provider=data["provider"]
        )
    else:
        raise ValueError(f"Unknown product class: {class_name}")

# ---------- SAVE & LOAD (products/customers only) ----------
# NOTE: customer and order (de)serialization moved to main.py. Reason:
# main.py is the only place that can safely import BOTH customers.py
# (Customer/PremiumCustomer) AND checkout.py (Order/OrderProcessingManager)
# at once. person1.py cannot import from checkout.py itself, because
# checkout.py already does `from person1 import ...` - importing back
# would create a circular import.

def save_products(manager, filename="data.json"):
    """Save just the products portion (used internally / for standalone testing)."""
    data = {"products": [_product_to_dict(p) for p in manager.products]}
    with open(filename, "w") as f:
        json.dump(data, f, indent=2)
    print(f"[Persistence] Products saved to {filename}")

def load_sample_data(manager):
    """Populate the manager with sample PRODUCTS only for standalone demos.
    Customers and orders are added separately in main.py, which owns the
    full sample dataset shared across all four modules."""
    print("[Persistence] Loading sample product data...")
    manager.clear_all_data()

    p1 = PhysicalProduct("P-1001", "Laptop", 999.99, 10, 2.5, 5.0)
    p2 = PhysicalProduct("P-1002", "Mouse", 29.99, 50, 0.2, 5.0)
    p3 = DigitalProduct("D-2001", "Python E-Book", 19.99, 999, "https://dl.example.com/python.pdf", 5)
    p4 = DigitalProduct("D-2002", "Video Course", 49.99, 200, "https://dl.example.com/course.mp4", 1024)
    p5 = Service("S-3001", "Tech Support", 75.00, 100, 2, "TechCo")

    manager.add_product(p1)
    manager.add_product(p2)
    manager.add_product(p3)
    manager.add_product(p4)
    manager.add_product(p5)

    print("[Persistence] Sample data loaded: 5 products.")


# ============================================================
# SECTION 4B: CLI MENU HANDLER FOR "ADD PRODUCT"
# ============================================================
# This is Student 1's own required menu action. It is written as a
# standalone function so Student 4 can import and call it directly from
# the shared main menu loop, but it also runs on its own for demoing.

PRODUCT_TYPE_BUILDERS = {
    "1": ("Physical", PhysicalProduct),
    "2": ("Digital", DigitalProduct),
    "3": ("Service", Service),
}

def _prompt_float(label):
    while True:
        try:
            return float(input(label))
        except ValueError:
            print("  Please enter a valid number.")

def _prompt_int(label):
    while True:
        try:
            return int(input(label))
        except ValueError:
            print("  Please enter a whole number.")

def add_product_interactive(manager):
    """
    Prompt the user for product details, validate them, and add the product
    to the manager. Demonstrates the product-code regex and every product
    exception live against real (possibly bad) user input.
    """
    print("\n--- Add Product ---")
    print("1) Physical  2) Digital  3) Service")
    choice = input("Product type: ").strip()

    if choice not in PRODUCT_TYPE_BUILDERS:
        print("  Invalid choice. Returning to menu.")
        return

    type_label, builder = PRODUCT_TYPE_BUILDERS[choice]
    code = input("Product code (e.g. P-1234): ").strip().upper()
    name = input("Product name: ").strip()
    price = _prompt_float("Price: ")
    stock = _prompt_int("Initial stock: ")

    try:
        if builder is PhysicalProduct:
            weight = _prompt_float("Weight (kg): ")
            product = PhysicalProduct(code, name, price, stock, weight)
        elif builder is DigitalProduct:
            link = input("Download link: ").strip()
            size = _prompt_float("File size (MB): ")
            product = DigitalProduct(code, name, price, stock, link, size)
        else:  # Service
            duration = _prompt_float("Duration (hours): ")
            provider = input("Provider: ").strip()
            product = Service(code, name, price, stock, duration, provider)

        manager.add_product(product)
        print(f"Added: {product}")

    except InvalidProductCodeError as e:
        print(f"Invalid product code: {e}")
    except ValueError as e:
        # add_product() itself raises ValueError for negative/duplicate stock
        print(f"Could not add product: {e}")


# ============================================================
# SECTION 5: TEST SUITE (optional)
# ============================================================

def test_person1():
    print("=" * 60)
    print("PERSON 1 – VALIDATION TEST SUITE")
    print("=" * 60)

    manager = OrderManager()
    load_sample_data(manager)
    print("\nSample data loaded.")

    # Test regex
    print("\n--- Testing Regex Validation ---")
    print(f"P-1234 is valid: {validate_product_code('P-1234')}")
    print(f"P-ABC is invalid: {validate_product_code('P-ABC')}")
    print(f"1234 is invalid: {validate_product_code('1234')}")
    try:
        invalid = PhysicalProduct("P-ABC", "Bad", 10, 5, 1.0)
    except InvalidProductCodeError as e:
        print(f"Caught invalid code: {e}")

    # Test polymorphism
    print("\n--- Testing Polymorphism (shipping) ---")
    for product in manager.products:
        print(f"{product.code} – Shipping: ${product.calculate_shipping():.2f} | {product.get_description()[:50]}...")

    # Test iterator
    print("\n--- Testing Iterator (Product Catalog) ---")
    print("Iterating over products:")
    for idx, product in enumerate(manager):
        print(f"  {idx+1}. {product.name}")

    # Test stock reduction and exceptions
    print("\n--- Testing Stock & Exceptions ---")
    laptop = manager.find_product_by_code("P-1001")
    print(f"Laptop stock before: {laptop.stock}")
    manager.reduce_stock("P-1001", 2)
    print(f"Laptop stock after reducing 2: {laptop.stock}")

    try:
        manager.reduce_stock("P-1001", 20)
    except InsufficientStockError as e:
        print(f"Caught insufficient stock: {e}")

    try:
        manager.get_product_or_raise("P-9999")
    except ProductNotFoundError as e:
        print(f"Caught product not found: {e}")

    # Test negative stock prevention
    try:
        manager.add_product(PhysicalProduct("P-9999", "Neg", 10, -5, 1.0))
    except ValueError as e:
        print(f"Caught negative stock: {e}")

    # Test zero quantity reduction
    try:
        laptop.reduce_stock(0)
    except InvalidQuantityError as e:
        print(f"Caught zero quantity: {e}")

    # Test low-stock filter
    print("\n--- Testing Low-Stock Filter ---")
    low_stock = manager.get_low_stock_products(threshold=10)
    print(f"Products at or below 10 units: {[p.code for p in low_stock]}")
    assert all(p.stock <= 10 for p in low_stock), "Filter returned an item above threshold!"
    print("Low-stock filter returns only qualifying products")

    # Test JSON persistence (products only - full save/load with
    # customers/orders lives in main.py now)
    print("\n--- Testing JSON Persistence (products) ---")
    save_products(manager, "test_data.json")
    manager.clear_all_data()
    print("Manager cleared. Reloading products from JSON...")
    with open("test_data.json") as f:
        reloaded = json.load(f)
    for p_data in reloaded.get("products", []):
        manager.add_product(_dict_to_product(p_data))
    print(f"After reload: {len(manager.products)} products")

    print("\n" + "=" * 60)
    print("ALL TESTS PASSED – Person 1's code is ready for integration!")
    print("=" * 60)


# ============================================================
# SECTION 6: MAIN ENTRY POINT (calls load_data on startup)
# ============================================================

def main():
    """Standalone entry point for Person 1's module only (products/inventory).
    The full app with customers, checkout, and reports lives in main.py."""
    print("=" * 60)
    print("PERSON 1 – PRODUCT & INVENTORY MODULE (standalone)")
    print("=" * 60)

    manager = OrderManager()
    load_sample_data(manager)

    while True:  # <--- ADD LOOP
        print("\nInventory Management")
        print("1. View all products")
        print("2. Add a product")
        print("3. View low-stock products")
        print("4. Save data")
        print("5. Quit")
        
        choice = input("Choose option (1-5): ").strip()
        
        if choice == "1":
            print("\nCurrent Inventory:")
            for p in manager.products:
                print(f"  {p}")
                
        elif choice == "2":
            add_product_interactive(manager)
            
        elif choice == "3":
            low_stock = manager.get_low_stock_products(threshold=10)
            print(f"\nLow-stock products (<=10): {len(low_stock)}")
            for p in low_stock:
                print(f"  {p.code} – {p.name}: {p.stock} left")
                
        elif choice == "4":
            try:
                save_products(manager, "data.json")
            except OSError as e:
                print(f"[Persistence] Could not write data.json ({e})")
                
        elif choice == "5":
            print("\nSaving data before exit...")
            try:
                save_products(manager, "data.json")
            except OSError as e:
                print(f"[Persistence] Could not write data.json ({e})")
            print("Goodbye!")
            break
        else:
            print("Invalid option. Please try again.")


    print("\nApplication ready.")
    print("=" * 60)




if __name__ == "__main__":

    # test_person1()
    main()