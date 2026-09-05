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

class Customer:
    """Base customer class."""

    def __init__(self, name, email, phone, level="Regular"):
        self.name = name
        self.email = email      # validation done by Student 3
        self.phone = phone      # validation done by Student 3
        self.level = level      # "Regular" or "Premium"

    def __str__(self):
        return f"{self.name} ({self.email}) – {self.level}"


class PremiumCustomer(Customer):
    """Premium customers get extra discounts and loyalty points."""

    def __init__(self, name, email, phone, discount_rate=0.15, loyalty_points=0):
        super().__init__(name, email, phone, level="Premium")
        self.discount_rate = discount_rate
        self.loyalty_points = loyalty_points

    def add_loyalty_points(self, points):
        self.loyalty_points += points


# ---------- ORDER CLASS ----------

class Order:
    """Represents a customer order."""

    def __init__(self, order_id, customer, items, total, status="Pending", created_at=None):
        self.order_id = order_id          # e.g., "ORD-ABCD-1234" (validated by Student 3)
        self.customer = customer          # Customer object
        self.items = items                # list of dict: [{"product": Product, "quantity": int}, ...]
        self.total = total                # final total after discounts
        self.status = status              # "Pending", "Shipped", "Delivered", "Cancelled"
        # Restore created_at if provided, otherwise use current time
        self.created_at = created_at if created_at else datetime.now().isoformat()

    def __str__(self):
        return f"Order {self.order_id} – {self.customer.name} – ${self.total:.2f} – {self.status}"


# ---------- ORDER MANAGER (CONTAINER + ITERATOR) ----------

class OrderManager:
    """
    Main data container for the entire application.
    Owns all collections and provides an iterator for the product catalog.
    """

    def __init__(self):
        self.products = []          # list of Product objects
        self.customers = []         # list of Customer objects
        self.orders = []            # list of Order objects
        self.current_cart = []      # temporary cart (will be used by Student 2)

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

    # ---------- Order management ----------
    def add_order(self, order):
        self.orders.append(order)

    # Add this method to OrderManager
    def create_discount_engine(self, customer_level):
        base_rate = {"Premium": 0.15, "Regular": 0.05}.get(customer_level, 0.0)
        total_discount_given = 0.0          # real state that persists across calls

        def apply_discount(price):
            nonlocal total_discount_given
            discount = price * base_rate
            total_discount_given += discount   # actually changes between calls
            return price - discount

        return apply_discount

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
        self.orders.clear()
        self.current_cart.clear()


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

def _customer_to_dict(customer):
    return {
        "class": customer.__class__.__name__,
        "name": customer.name,
        "email": customer.email,
        "phone": customer.phone,
        "level": customer.level,
        "discount_rate": getattr(customer, "discount_rate", 0.0),
        "loyalty_points": getattr(customer, "loyalty_points", 0),
    }

def _dict_to_customer(data):
    class_name = data.get("class")
    if class_name == "PremiumCustomer":
        return PremiumCustomer(
            name=data["name"],
            email=data["email"],
            phone=data["phone"],
            discount_rate=data.get("discount_rate", 0.15),
            loyalty_points=data.get("loyalty_points", 0)
        )
    else:  # Regular Customer
        return Customer(
            name=data["name"],
            email=data["email"],
            phone=data["phone"],
            level=data.get("level", "Regular")
        )

def _order_to_dict(order, manager):
    # We store customer email as reference, and product codes in items
    return {
        "order_id": order.order_id,
        "customer_email": order.customer.email,
        "items": [{"product_code": item["product"].code, "quantity": item["quantity"]} for item in order.items],
        "total": order.total,
        "status": order.status,
        "created_at": order.created_at,   # <--- store timestamp
    }

def _dict_to_order(data, manager):
    customer = manager.find_customer_by_email(data["customer_email"])
    if customer is None:
        raise ValueError(f"Customer {data['customer_email']} not found when loading order.")
    items = []
    for item_data in data["items"]:
        product = manager.find_product_by_code(item_data["product_code"])
        if product is None:
            raise ValueError(f"Product {item_data['product_code']} not found when loading order.")
        items.append({"product": product, "quantity": item_data["quantity"]})
    # Pass created_at to constructor
    return Order(
        order_id=data["order_id"],
        customer=customer,
        items=items,
        total=data["total"],
        status=data.get("status", "Pending"),
        created_at=data.get("created_at")   # <--- restore timestamp
    )


# ---------- SAVE & LOAD ----------

def save_data(manager, filename="data.json"):
    """Save all data to a JSON file."""
    data = {
        "products": [_product_to_dict(p) for p in manager.products],
        "customers": [_customer_to_dict(c) for c in manager.customers],
        "orders": [_order_to_dict(o, manager) for o in manager.orders],
    }
    with open(filename, "w") as f:
        json.dump(data, f, indent=2)
    print(f"[Persistence] Data saved to {filename}")

def load_data(manager, filename="data.json"):
    """
    Load data from JSON file. If file doesn't exist or is corrupted,
    fall back to sample data and save it immediately.
    """
    if not os.path.exists(filename):
        print(f"[Persistence] {filename} not found. Loading sample data instead.")
        load_sample_data(manager)
        save_data(manager, filename)   
        return

    try:
        with open(filename, "r") as f:
            data = json.load(f)

        # Clear existing data
        manager.clear_all_data()

        # Load products
        for p_data in data.get("products", []):
            manager.add_product(_dict_to_product(p_data))

        # Load customers
        for c_data in data.get("customers", []):
            manager.add_customer(_dict_to_customer(c_data))

        # Load orders (need manager to resolve product/customer references)
        for o_data in data.get("orders", []):
            manager.add_order(_dict_to_order(o_data, manager))

        print(f"[Persistence] Data loaded from {filename}")

    except (json.JSONDecodeError, KeyError, ValueError) as e:
        print(f"[Persistence] Error loading {filename}: {e}. Falling back to sample data.")
        load_sample_data(manager)
        save_data(manager, filename)   

# ---------- SAMPLE DATA (shared across all students) ----------

def load_sample_data(manager):
    """Populate the manager with sample data for demos."""
    print("[Persistence] Loading sample data...")

    # Clear first
    manager.clear_all_data()

    # ---- Products ----
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

    # ---- Customers ----
    c1 = Customer("Alice Johnson", "alice@example.com", "+1234567890", "Regular")
    c2 = PremiumCustomer("Bob Smith", "bob@example.com", "+1987654321", 0.15, 120)
    c3 = Customer("Carol White", "carol@example.com", "+1122334455", "Regular")

    manager.add_customer(c1)
    manager.add_customer(c2)
    manager.add_customer(c3)

    # ---- Orders (for report demos) ----
    order1 = Order(
        order_id="ORD-ABCD-1234",
        customer=c2,
        items=[{"product": p1, "quantity": 1}, {"product": p3, "quantity": 2}],
        total=999.99 + 2 * 19.99,
        status="Shipped",
        created_at="2026-09-01T10:30:00"   # fixed timestamp for demo
    )
    order2 = Order(
        order_id="ORD-EFGH-5678",
        customer=c1,
        items=[{"product": p2, "quantity": 5}],
        total=5 * 29.99,
        status="Delivered",
        created_at="2026-09-02T14:15:00"
    )
    order3 = Order(
        order_id="ORD-IJKL-9012",
        customer=c2,
        items=[{"product": p4, "quantity": 1}, {"product": p5, "quantity": 3}],
        total=49.99 + 3 * 75.00,
        status="Pending",
        created_at="2026-09-03T09:00:00"
    )

    manager.add_order(order1)
    manager.add_order(order2)
    manager.add_order(order3)

    # Reduce stock to reflect past orders
    p1.reduce_stock(1)
    p3.reduce_stock(2)
    p2.reduce_stock(5)
    p4.reduce_stock(1)
    p5.reduce_stock(3)

    print("[Persistence] Sample data loaded: 5 products, 3 customers, 3 orders.")


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

    # Test JSON persistence with created_at
    print("\n--- Testing JSON Persistence ---")
    save_data(manager, "test_data.json")
    manager.clear_all_data()
    print("Manager cleared. Reloading from JSON...")
    load_data(manager, "test_data.json")
    print(f"After reload: {len(manager.products)} products, {len(manager.customers)} customers, {len(manager.orders)} orders")

    # Verify created_at restored
    print("\n--- Verifying created_at restoration ---")
    for o in manager.orders:
        print(f"  {o.order_id} created at {o.created_at}")

    print("\n" + "=" * 60)
    print("ALL TESTS PASSED – Person 1's code is ready for integration!")
    print("=" * 60)


# ============================================================
# SECTION 6: MAIN ENTRY POINT (calls load_data on startup)
# ============================================================

def main():
    """Main application entry point – loads data and loops until quit."""
    print("=" * 60)
    print("PERSON 1 – PRODUCT & INVENTORY MODULE")
    print("=" * 60)

    manager = OrderManager()
    try:
        load_data(manager, "data.json")
    except OSError as e:
        print(f"[Persistence] Could not read data.json ({e}). Starting with sample data instead.")
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
                save_data(manager, "data.json")
            except OSError as e:
                print(f"[Persistence] Could not write data.json ({e})")
                
        elif choice == "5":
            print("\nSaving data before exit...")
            try:
                save_data(manager, "data.json")
            except OSError as e:
                print(f"[Persistence] Could not write data.json ({e})")
            print("Goodbye!")
            break
        else:
            print("Invalid option. Please try again.")


    
    # Demo closure test ,, and it works so i commeted it 
    # print("\n--- Closure Demo (Discount Engine) ---")
    # regular_discount = manager.create_discount_engine("Regular")
    # premium_discount = manager.create_discount_engine("Premium")
    # print(f"Regular pays: ${regular_discount(100.00):.2f}")
    # print(f"Premium pays: ${premium_discount(100.00):.2f}")
    # print(f"Regular pays again: ${regular_discount(50.00):.2f}")
    
    

    print("\nApplication ready.")
    print("=" * 60)




if __name__ == "__main__":

    # test_person1()
    main()