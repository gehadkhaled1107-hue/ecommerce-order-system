"""
main.py
Person 4 — Reports & Integration Owner
Mini E-Commerce Order System (SIC Chapter 3 Capstone)

Final integration point. Combines:
  products.py   -> Product hierarchy (PhysicalProduct/DigitalProduct/Service),
                  OrderManager (products/customers container + iterator + filter)
  customers.py -> Customer/PremiumCustomer, Cart/CartItem, regex validation
  checkout.py  -> Order, OrderProcessingManager, checkout(), cancel_order(),
                  discount engine closure
  reports.py   -> low_stock_report(), sales_report(), OrderIterator
  exceptions.py-> single collected import point for every custom exception

Run:  python main.py
"""

import json
import os
from datetime import datetime

from products import (
    OrderManager,
    PhysicalProduct,
    DigitalProduct,
    Service,
    validate_product_code,
    add_product_interactive,
    _product_to_dict,
    _dict_to_product,
    load_sample_data as load_sample_products,
)
from customers import Customer, PremiumCustomer, Cart, validate_email, validate_phone
from checkout import (
    Order,
    OrderProcessingManager,
    CartItem,
    checkout,
    cancel_order,
    calculate_cart_and_shipping_total,
    make_discount_engine,
    action_history,
)
from reports import low_stock_report, sales_report
from exceptions import (
    InvalidProductCodeError,
    InsufficientStockError,
    ProductNotFoundError,
    InvalidQuantityError,
    InvalidCustomerDataError,
    CartError,
    InvalidOrderStateError,
    InvalidPaymentError,
    EmptyCartError,
    OrderNotFoundError,
)

DATA_FILE = "data.json"


# ============================================================
# JSON <-> object conversion for customers & orders
# (lives here, not in products.py, to avoid a circular import:
#  checkout.py already imports FROM products.py)
# ============================================================

def _customer_to_dict(customer):
    return {
        "class": customer.__class__.__name__,
        "customer_id": customer.customer_id,
        "name": customer.name,
        "email": customer.email,
        "phone": customer.phone,
        "loyalty_points": getattr(customer, "loyalty_points", 0),
    }


def _dict_to_customer(data):
    if data.get("class") == "PremiumCustomer":
        return PremiumCustomer(
            customer_id=data["customer_id"],
            name=data["name"],
            email=data["email"],
            phone=data["phone"],
            loyalty_points=data.get("loyalty_points", 0),
        )
    return Customer(
        customer_id=data["customer_id"],
        name=data["name"],
        email=data["email"],
        phone=data["phone"],
    )


def _find_customer_by_email(customers, email):
    for c in customers:
        if c.email == email:
            return c
    return None


def _order_to_dict(order):
    return {
        "order_id": order.order_id,
        "customer_email": order.customer.email,
        "items": [
            {"product_code": item.product.code, "quantity": item.quantity}
            for item in order.cart_items
        ],
        "total": order.total,
        "status": order.status_getter(),
        "created_at": order.placed_time.isoformat()
            if isinstance(order.placed_time, datetime) else str(order.placed_time),
    }


def _dict_to_order(data, product_manager, customers):
    customer = _find_customer_by_email(customers, data["customer_email"])
    if customer is None:
        raise ValueError(f"Customer {data['customer_email']} not found when loading order.")

    cart_items = []
    for item_data in data["items"]:
        product = product_manager.find_product_by_code(item_data["product_code"])
        if product is None:
            raise ValueError(f"Product {item_data['product_code']} not found when loading order.")
        cart_items.append(CartItem(product, item_data["quantity"]))

    placed_time = data.get("created_at", datetime.now().isoformat())

    order = Order(
        order_id=data["order_id"],
        customer=customer,
        cart_items=cart_items,
        total=data["total"],
        placed_time=placed_time,
        status="pending",  # always start at 'pending', then fast-forward below
    )

    # Fast-forward the state machine to the saved status so TRANSITIONS
    # stays consistent (rather than writing directly to the private field).
    target = data.get("status", "pending").lower()
    path = {
        "pending": [],
        "paid": ["paid"],
        "shipped": ["paid", "shipped"],
        "delivered": ["paid", "shipped", "delivered"],
        "cancelled": ["cancelled"],
    }.get(target, [])
    for step in path:
        order.status_setter(step)

    return order


# ============================================================
# SAVE / LOAD full application state
# ============================================================

def save_all(product_manager, customers, order_processing_manager, filename=DATA_FILE):
    data = {
        "products": [_product_to_dict(p) for p in product_manager.products],
        "customers": [_customer_to_dict(c) for c in customers],
        "orders": [_order_to_dict(o) for o in order_processing_manager.orders.values()],
    }
    with open(filename, "w") as f:
        json.dump(data, f, indent=2)
    print(f"[Persistence] Data saved to {filename}")


def load_all(product_manager, order_processing_manager, filename=DATA_FILE):
    """Loads products, customers, and orders. Returns the customers list
    (product_manager and order_processing_manager are filled in-place).
    Falls back to bundled sample data if the file is missing/corrupted."""
    customers = []

    if not os.path.exists(filename):
        print(f"[Persistence] {filename} not found. Loading sample data instead.")
        customers = load_sample_data(product_manager, order_processing_manager)
        save_all(product_manager, customers, order_processing_manager, filename)
        return customers

    try:
        with open(filename, "r") as f:
            data = json.load(f)

        product_manager.clear_all_data()
        order_processing_manager.orders.clear()

        for p_data in data.get("products", []):
            product_manager.add_product(_dict_to_product(p_data))

        for c_data in data.get("customers", []):
            customers.append(_dict_to_customer(c_data))

        for o_data in data.get("orders", []):
            order = _dict_to_order(o_data, product_manager, customers)
            order_processing_manager.orders[order.order_id] = order

        print(f"[Persistence] Data loaded from {filename}")
        return customers

    except (json.JSONDecodeError, KeyError, ValueError) as e:
        print(f"[Persistence] Error loading {filename}: {e}. Falling back to sample data.")
        customers = load_sample_data(product_manager, order_processing_manager)
        save_all(product_manager, customers, order_processing_manager, filename)
        return customers


def load_sample_data(product_manager, order_processing_manager):
    """Bundled sample dataset shared across the whole app (used when no
    data.json is present)."""
    load_sample_products(product_manager)  # from products.py: 5 sample products

    c1 = Customer("C001", "Alice Johnson", "alice@example.com", "01234567890")
    c2 = PremiumCustomer("C002", "Bob Smith", "bob@example.com", "01087654321", loyalty_points=120)
    c3 = Customer("C003", "Carol White", "carol@example.com", "01122334455")
    customers = [c1, c2, c3]

    return customers


# ============================================================
# Helpers bridging Cart <-> CartItem (checkout.py's CartItem)
# ============================================================

def cart_to_checkout_items(cart):
    """Convert Ali's Cart (holding his own CartItem) into the CartItem
    objects checkout.py expects. Both have .product/.quantity, so this is
    a thin adapter rather than a real transformation."""
    return [CartItem(ci.product, ci.quantity) for ci in cart.get_items()]


# ============================================================
# MAIN MENU
# ============================================================

def find_customer(customers, email):
    return _find_customer_by_email(customers, email)


def view_all_products_interactive(product_manager):
    print("\n--- All Products ---")
    for product in product_manager:
        print(f"  {product}")

def view_action_history_interactive():
    print("\n--- Action History ---")
    if not action_history:
        print("No actions recorded yet.")
    else:
        for entry in action_history:
            timestamp = entry["timestamp"].strftime("%H:%M:%S")
            print(f"  [{timestamp}] {entry['action']}: {entry['details']}")

def print_menu():
    print("\n" + "=" * 60)
    print("MINI E-COMMERCE ORDER SYSTEM")
    print("=" * 60)
    print("1. Show products")
    print("2. Add product")
    print("3. Register customer")
    print("4. Add to cart")
    print("5. Checkout order")
    print("6. Update order status")
    print("7. Sales report")
    print("8. Low-stock report")
    print("9. Cancel order (bonus)")
    print("10. Save data")
    print("11. View action history (bonus)")
    print("0. Quit")


def register_customer_interactive(customers):
    print("\n--- Register Customer ---")
    name = input("Name: ").strip()
    email = input("Email: ").strip()
    phone = input("Phone (e.g. 01012345678): ").strip()
    is_premium = input("Premium customer? (y/n): ").strip().lower() == "y"

    customer_id = f"C{len(customers) + 1:03d}"
    try:
        if is_premium:
            points = int(input("Starting loyalty points: ").strip() or "0")
            customer = PremiumCustomer(customer_id, name, email, phone, loyalty_points=points)
        else:
            customer = Customer(customer_id, name, email, phone)
        customers.append(customer)
        print(f"Registered: {customer}")
    except InvalidCustomerDataError as e:
        print(f"Could not register customer: {e}")


def add_to_cart_interactive(customers, product_manager):
    print("\n--- Add to Cart ---")
    email = input("Customer email: ").strip()
    customer = find_customer(customers, email)
    if customer is None:
        print("Customer not found.")
        return

    code = input("Product code: ").strip().upper()
    product = product_manager.find_product_by_code(code)
    if product is None:
        print(f"Product '{code}' not found.")
        return

    try:
        quantity = int(input("Quantity: ").strip())
        customer.cart.add_item(product, quantity)
        print(f"Added {quantity} x {product.name} to {customer.name}'s cart.")
    except (ValueError, CartError) as e:
        print(f"Could not add to cart: {e}")


def checkout_interactive(customers, order_processing_manager):
    print("\n--- Checkout ---")
    email = input("Customer email: ").strip()
    customer = find_customer(customers, email)
    if customer is None:
        print("Customer not found.")
        return

    checkout_items = cart_to_checkout_items(customer.cart)
    try:
        order = checkout(customer, checkout_items, order_processing_manager)
        customer.cart.clear()
        print(f"Order placed: {order}")
    except EmptyCartError as e:
        print(f"Checkout failed: {e}")
    except (InsufficientStockError, InvalidQuantityError) as e:
        print(f"Checkout failed (stock issue): {e}")
    except InvalidPaymentError as e:
        print(f"Checkout failed (payment issue): {e}")


def update_order_status_interactive(order_processing_manager):
    print("\n--- Update Order Status ---")
    order_id = input("Order ID: ").strip()
    new_status = input("New status (paid/shipped/delivered/cancelled): ").strip().lower()
    try:
        order = order_processing_manager.update_order_status(order_id, new_status)
        print(f"Updated: {order}")
    except OrderNotFoundError as e:
        print(f"Update failed: {e}")
    except InvalidOrderStateError as e:
        print(f"Update failed: {e}")


def cancel_order_interactive(order_processing_manager):
    print("\n--- Cancel Order (bonus) ---")
    order_id = input("Order ID: ").strip()

    confirm = input(f"Are you sure you want to cancel order '{order_id}'? (y/n): ").strip().lower()
    if confirm != "y":
        print("Cancellation aborted.")
        return

    try:
        order = cancel_order(order_processing_manager, order_id)
        print(f"Cancelled: {order}")
    except OrderNotFoundError as e:
        print(f"Cancel failed: {e}")
    except InvalidOrderStateError as e:
        print(f"Cancel failed: {e}")


def main():
    product_manager = OrderManager()          # products + customers container (products.py)
    order_processing_manager = OrderProcessingManager()  # orders (checkout.py)

    customers = load_all(product_manager, order_processing_manager, DATA_FILE)

    while True:
        print_menu()
        choice = input("Choose option: ").strip()

        if choice == "1":
            view_all_products_interactive(product_manager)

        elif choice == "2":
            add_product_interactive(product_manager)

        elif choice == "3":
            register_customer_interactive(customers)

        elif choice == "4":
            add_to_cart_interactive(customers, product_manager)

        elif choice == "5":
            checkout_interactive(customers, order_processing_manager)

        elif choice == "6":
            update_order_status_interactive(order_processing_manager)

        elif choice == "7":
            print("\n" + sales_report(order_processing_manager))

        elif choice == "8":
            print("\n" + low_stock_report(product_manager))

        elif choice == "9":
            cancel_order_interactive(order_processing_manager)

        elif choice == "10":
            save_all(product_manager, customers, order_processing_manager, DATA_FILE)

        elif choice == "11":
            view_action_history_interactive()

        elif choice == "0":
            print("\nSaving before exit...")
            save_all(product_manager, customers, order_processing_manager, DATA_FILE)
            print("Goodbye!")
            break

        else:
            print("Invalid option. Please try again.")


if __name__ == "__main__":
    main()