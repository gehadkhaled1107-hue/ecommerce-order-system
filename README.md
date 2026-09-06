# Mini E-Commerce Order System
SIC Chapter 3 Capstone — Option 2

## Team
- **Ahmed Mekawy** — Products & Inventory (`person1.py`)
- **Ali** — Customers & Cart (`customers.py`)
- **Gehad Khaled** — Checkout & Orders (`checkout.py`)
- **Moaz Maged** — Reports & Integration (`reports.py`, `exceptions.py`, `main.py`)

## How to Run
```
python main.py
```
On first run it loads `data.json`. If missing/corrupted, it falls back to built-in sample data and writes a fresh `data.json`.

## Files
| File | Owner | Contents |
|---|---|---|
| `person1.py` | Ahmed | `Product` (ABC) → `PhysicalProduct`, `DigitalProduct`, `Service`; `OrderManager` (products/customers container, iterator, `filter`-based low-stock); product-code regex; product exceptions |
| `customers.py` | Ali | `Customer` → `PremiumCustomer`; `Cart`/`CartItem`; email/phone regex; customer/cart exceptions |
| `checkout.py` | Gehad | `Order` (status state machine), `OrderProcessingManager` (create/update/cancel), `checkout()`, discount closure, `reduce`-based totals, invoice export |
| `reports.py` | Moaz | `OrderIterator` (custom iterator class), `low_stock_report()`, `sales_report()` |
| `exceptions.py` | Moaz | Single collected import point for every custom exception across the three modules |
| `main.py` | Moaz | Final integration: main menu, JSON save/load for customers & orders, wiring between all modules |
| `data.json` | shared | Sample products, customers, orders |

## Main Features
1. Add product (Physical / Digital / Service)
2. Register customer (Regular / Premium)
3. Add to cart
4. Checkout (stock reservation → discount → shipping → payment → invoice)
5. Update order status (pending → paid → shipped → delivered, or → cancelled)
6. Sales report (total revenue, status breakdown, top 3 products)
7. Low-stock report
8. Cancel order (bonus — rolls back stock)
9. Save data / Quit (auto-saves)

## Class Structure Summary
- **Base + subclasses (OOP):** `Product` → `PhysicalProduct`, `DigitalProduct`, `Service` (polymorphic `get_description()`, `calculate_shipping()`); `Customer` → `PremiumCustomer` (polymorphic `discount_rate()`, `display_info()`)
- **Order lifecycle:** `Order` (private `__status` + `TRANSITIONS` state machine), `OrderProcessingManager`
- **Containers:** `OrderManager` (products/customers, iterable, `filter`-based reporting), `Cart` (iterable)

## Concept Mapping Table
| Concept | Where | Why |
|---|---|---|
| Closure + `nonlocal` | `make_discount_engine()` in `checkout.py` | Remembers whether a discount was already applied to a given checkout, across calls |
| Regex | `validate_product_code()` (person1), `validate_email()` / `validate_phone()` (customers) | Validates product codes, emails, phone numbers |
| `lambda` / `map` | `Order.generate_invoice_text()` | Formats each cart line for the invoice |
| `filter` | `OrderManager.get_low_stock_products()` | Selects products at/below a stock threshold |
| `reduce` | `calculate_cart_and_shipping_total()` | Sums cart subtotal and shipping cost |
| Custom iterator | `OrderIterator` in `reports.py` | Iterates orders for the sales report |
| Iterable | `OrderManager.__iter__`, `Cart.__iter__` | Lets `for product in manager` / `for item in cart` work directly |
| Exceptions | `exceptions.py` (collected) | Invalid product code, insufficient stock, invalid customer data, empty cart, invalid payment, invalid order transition, order not found |

## Integration Notes (conflicts resolved during merge)
- **Duplicate `Order`/`OrderManager`:** `checkout.py`'s `Order` (with the status state machine) is the single source of truth for orders; `person1.py`'s `OrderManager` was trimmed to only own products/customers.
- **Duplicate `Customer`/`PremiumCustomer`:** `customers.py`'s versions (with real regex validation) are the single source of truth; `person1.py`'s copies were removed.
- **Duplicate class name `OrderManager`:** `checkout.py`'s order-lifecycle manager was renamed `OrderProcessingManager`.
- **`add_order` vs `create_order`:** `create_order()` is now the primary method; `add_order()` is kept as a thin alias for compatibility.
- **Duplicate discount closure:** `checkout.py`'s `make_discount_engine(customer)` is used; `person1.py`'s `create_discount_engine(level)` was removed. Bug fixed: `customer.discount_rate` is a **method** on `customers.py`'s classes, not a plain attribute — the closure now calls it instead of treating it as a number.
- **Status casing:** sample data's `Pending/Shipped/Delivered` were lowercased to match `checkout.py`'s `TRANSITIONS` state machine (`pending → paid → shipped → delivered`, or `→ cancelled`).

## Known Limitations
- Payment is collected via a blocked `input()` call inside `checkout()`, so it can't be automated/tested without piping stdin.
- Sample phone numbers follow the Egyptian mobile format enforced by `customers.py`'s regex (`01[0125]XXXXXXXX`).
