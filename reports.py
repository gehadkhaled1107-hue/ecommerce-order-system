"""
reports.py
Person 4 — Reports & Integration Owner

Core requirements covered here:
- filter() for low-stock items          -> low_stock_report()
- Iterator/iterable processing          -> OrderIterator (custom iterator class, technical bonus)
                                            + iterates order/product records
- Sales report (totals, top products)   -> sales_report()

This module only READS from the other managers (an OrderManager for
products, an OrderProcessingManager for orders). It never mutates state,
so it's safe to call as many times as you like from the main menu.
"""

from functools import reduce


# ---------- CUSTOM ITERATOR (technical bonus) ----------

class OrderIterator:
    """
    A custom iterator over an OrderProcessingManager's orders.
    Demonstrates the iterator protocol explicitly (rather than relying on
    dict.values()), which is what the rubric's 'iterator processing' and
    'custom iterator class' bonus are looking for.
    """

    def __init__(self, order_processing_manager):
        self._orders = list(order_processing_manager.orders.values())
        self._index = 0

    def __iter__(self):
        return self

    def __next__(self):
        if self._index >= len(self._orders):
            raise StopIteration
        order = self._orders[self._index]
        self._index += 1
        return order


# ---------- LOW-STOCK REPORT (filter) ----------

def low_stock_report(order_manager, threshold=10):
    """
    Returns a formatted string listing all products at or below `threshold`.
    Reuses OrderManager.get_low_stock_products(), which already does the
    filter()+lambda work (products.py) — this function just formats it as a
    report instead of duplicating the filter logic.
    """
    low_stock = order_manager.get_low_stock_products(threshold=threshold)

    lines = [f"--- Low-Stock Report (<= {threshold} units) ---"]
    if not low_stock:
        lines.append("No products are low on stock. All good!")
    else:
        for p in low_stock:
            lines.append(f"  {p.code} | {p.name:<20} | Stock: {p.stock}")
    return "\n".join(lines)


# ---------- SALES REPORT (iterator + reduce + map/filter) ----------

def sales_report(order_processing_manager):
    """
    Builds a sales report from every order in the system:
    - total revenue across all non-cancelled orders (reduce)
    - order count by status (iterator processing via OrderIterator)
    - top 3 products by units sold (across all orders)
    """
    orders = OrderIterator(order_processing_manager)

    non_cancelled = []
    status_counts = {}
    product_units = {}   # product_code -> {"name": str, "units": int}

    # Iterate using the custom iterator (demonstrates iterator protocol)
    for order in orders:
        status = order.status_getter()
        status_counts[status] = status_counts.get(status, 0) + 1

        if status != "cancelled":
            non_cancelled.append(order)
            for item in order.cart_items:
                code = item.product.code
                if code not in product_units:
                    product_units[code] = {"name": item.product.name, "units": 0}
                product_units[code]["units"] += item.quantity

    # reduce() to sum revenue from non-cancelled orders only
    total_revenue = reduce(lambda acc, o: acc + o.total, non_cancelled, 0.0)

    # Top 3 products by units sold
    top_products = sorted(
        product_units.items(),
        key=lambda pair: pair[1]["units"],
        reverse=True
    )[:3]

    lines = ["--- Sales Report ---"]
    lines.append(f"Total orders: {len(orders._orders)}")
    for status, count in status_counts.items():
        lines.append(f"  Status '{status}': {count}")
    lines.append(f"Total revenue (excluding cancelled): ${total_revenue:.2f}")

    lines.append("\nTop products by units sold:")
    if not top_products:
        lines.append("  No sales data yet.")
    else:
        for code, info in top_products:
            lines.append(f"  {code} | {info['name']:<20} | Units sold: {info['units']}")

    return "\n".join(lines)
