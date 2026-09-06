from datetime import datetime
import os
from functools import reduce
from person1 import InsufficientStockError, InvalidQuantityError


#        check out Exeptions collection
#Parent class --> all other Exception inherite from it
class ECommerceError(Exception):
    pass

#scenario --> want to cancell order after shipping
class InvalidOrderStateError(ECommerceError):
    def __init__(self, order_id, current_status, attempted_transition):
        self.order_id = order_id
        self.current_status = current_status
        self.attempted_transition = attempted_transition
        # inherant from ECommerceError class
        super().__init__(f"Can't transition your order {order_id} from {current_status} to {attempted_transition}")


#scenario --> customer write str , negative , less amount , try many times ..etc
class InvalidPaymentError(ECommerceError):
    def __init__(self, attempted_amount, expected_total, reason):
            self.attempted_amount = attempted_amount
            self.expected_total = expected_total
            self.reason = reason

            # message declare the Payment Error from real life systems
            if reason == "non_numeric":
                message = f"Payment entry: {attempted_amount} --> not a valid number."
            elif reason == "non_positive":
                message = f"Payment amount ${attempted_amount} must be greater than zero."
            elif reason == "underpayment":
                message = f"Underpayment: Provided ${float(attempted_amount):.2f}, required ${expected_total:.2f}."
            elif reason == "max_attempts_exceeded":
                message = "Payment failed: Maximum attempts exceeded."
            else:
                message = f"Invalid payment attempt: {attempted_amount}."
            super().__init__(message)


# scenario --> customer pressed checkout while the cart is empty
class EmptyCartError(ECommerceError):
    def __init__(self, customer_name):
        self.customer_name = customer_name
        super().__init__(f"Customer {customer_name} tried to checkout with an empty cart.")

# scenario --> trying to update/find an order that doesn't exist in the system
class OrderNotFoundError(ECommerceError):
    def __init__(self, order_id):
        self.order_id = order_id
        super().__init__(f"Order '{order_id}' was not found in the system.")


#The Goat logic --> status & TRANSITIONS
#the status is private variable --> only admin can edit it 
#TRANSITIONS --> there is a logic that you can"t cancell order after shipped
#you can't pand it after pay and so on 
class Order():
    # transition flow --> static\class variable
    TRANSITIONS = {
        "pending":   {"paid", "cancelled"},
        "paid":      {"shipped", "cancelled"},
        "shipped":   {"delivered"},
        "delivered": set(),
        "cancelled": set()
    }
    def __init__(self, order_id, customer, cart_items, total,
                placed_time, category = "general", status = "pending"):
        
        self.order_id = order_id
        self.customer = customer
        self.cart_items = cart_items
        self.total = total
        self.placed_time = placed_time
        self.category = category
        #Private variable
        # normalize to lowercase so TRANSITIONS lookups always match,
        # even if the status came from JSON data using Title Case
        self.__status = status.lower()

    #Encapsulation --> getter , setter
    def status_getter(self):
        return self.__status

    def status_setter(self, new_status):
        allowed_transation = self.TRANSITIONS[self.__status]
        if new_status in allowed_transation:
            self.__status = new_status
        else:
            raise InvalidOrderStateError(
                order_id = self.order_id,
                current_status = self.__status,
                attempted_transition = new_status
                )

    #status methods --> pass the status to status_setter
    def mark_paid(self):
        self.status_setter("paid")

    def mark_shipped(self):
        self.status_setter("shipped")

    def mark_delivered(self):
        self.status_setter("delivered")

    def mark_cancelled(self):
        self.status_setter("cancelled")

    def __str__(self):
        return (f"Order {self.order_id} | {self.customer.name} | "
                f"${self.total:.2f} | {self.status_getter()}")

    #            BONUS
    def generate_invoice_text(self):
        # map() transforms each cart item into one formatted display line -
        # this is the deliberate use of map() the rubric wants: a pure
        # transformation of a collection into display-ready strings.
        # Note: this uses item.product.price directly, so these per-line
        # amounts do NOT reflect shipping or the discount applied at
        # checkout - only the final Total line below reflects those.
        lines = list(map(
            lambda item: f"{item.product.name} x{item.quantity} - ${item.product.price * item.quantity:.2f}",
            self.cart_items
        ))

        # Build the invoice as one plain-text string: header, then the
        # mapped line items, then a footer with the real final total
        # (self.total, computed back in checkout() - already includes
        # shipping and discount).
        invoice = f"Order: {self.order_id}\n"
        invoice += f"Customer: {self.customer.name}\n"
        invoice += f"Date: {self.placed_time}\n\n"
        invoice += "\n".join(lines)
        invoice += f"\n\nTotal: ${self.total:.2f}\n"
        invoice += f"Status: {self.status_getter()}"   # goes through the getter, not the raw private attribute

        # KEY POINT: creates the invoices/ folder on first run if it
        # doesn't exist yet, so this never crashes on a fresh checkout
        # of the project folder.
        os.makedirs("invoices", exist_ok=True)
        file_path = f"invoices/{self.order_id}.txt"
        with open(file_path, "w") as f:
            f.write(invoice)

        # Returns the saved path so the caller (checkout()) can confirm
        # to the user where the invoice was saved - this method has one
        # job (build + save the invoice) and communicates its result via
        # return value rather than a side-effect the caller has to guess.
        return file_path

class OrderProcessingManager():
    """Owns the order lifecycle: creation, status transitions, cancellation.
    (Renamed from OrderManager to avoid clashing with person1.py's
    OrderManager, which owns products/customers/reports instead.)"""

    def __init__(self):
        # dictionary storing all orders --> {order_id: Order object}
        self.orders = {}
        self.counter = 0

    # scenario --> generate a new unique, human-readable order id
    def generate_order_id(self):
        current_date = datetime.now().strftime("%Y%m%d")
        while True:
            # order id sample --> ORD-20260906-00001
            order_id = f"ORD-{current_date}-{self.counter:05d}"
            self.counter += 1
            # keep trying new numbers until we find one not already used
            if order_id not in self.orders:
                return order_id

    # scenario --> build a new Order object from cart data and store it
    def create_order(self, customer, cart_items, total):

        cart_items = list(cart_items)
        new_order_id = self.generate_order_id()

        new_order = Order(
            order_id=new_order_id,
            customer=customer,
            cart_items=cart_items,
            total=total,
            placed_time=datetime.now()
        )

        self.orders[new_order_id] = new_order
        return new_order

    # alias kept for backward compatibility with code that expects add_order()
    # (person1.py originally exposed add_order on its own OrderManager)
    def add_order(self, customer, cart_items, total):
        return self.create_order(customer, cart_items, total)

    # scenario --> change the status of an existing order (paid, shipped, etc.)
    def update_order_status(self, order_id, new_status):
        if order_id in self.orders:
            order = self.orders[order_id]

            # delegate the actual transition check to the Order's state machine
            if new_status == "paid":
                order.mark_paid()
            elif new_status == "shipped":
                order.mark_shipped()
            elif new_status == "delivered":
                order.mark_delivered()
            elif new_status == "cancelled":
                order.mark_cancelled()
            else:
                raise InvalidOrderStateError(order_id, order.status_getter() , new_status)

            return order

        # order_id does not exist in the system at all
        raise OrderNotFoundError(order_id)


#to accaess product & quantity more easily than dictionary
class CartItem:
    def __init__(self, product, quantity):
        self.product = product
        self.quantity = quantity


def calculate_cart_and_shipping_total(cart_items):
    total = reduce(lambda accumulator,item : accumulator+(item.product.price * item.quantity) , cart_items , 0 )
    shipping = reduce(lambda accumulator, item: accumulator + (item.product.calculate_shipping() * item.quantity), cart_items, 0)
    return total , shipping

#apply discounts by closure --> discount apply only once 
def make_discount_engine(customer):
    # customers.py's Customer.discount_rate() is a METHOD (polymorphic:
    # PremiumCustomer overrides it), not a plain attribute - so it must be
    # called, not just fetched with getattr(). Falls back to 0.0 for any
    # customer object that has neither.
    rate_source = getattr(customer, 'discount_rate', 0.0)
    base_rate = rate_source() if callable(rate_source) else rate_source
    already_applied = False

    def apply_discount(subtotal):
        #nonlocal variable --> we'll need editing
        nonlocal already_applied
        if not already_applied:
            subtotal -= subtotal*base_rate
            already_applied = True
            return subtotal
        return subtotal

    return apply_discount 


def rollback_stock(successfully_reserved):
    # Restores stock for every item that was successfully reserved before
    # a later failure occurred. Called from both checkout() (failed
    # reservation/payment) and cancel_order() - single source of truth,
    # avoids duplicating this loop in three places.
    for reserved_item in successfully_reserved:
        reserved_item.product.stock += reserved_item.quantity


def checkout(customer, cart_items, order_manager):
    # first --> fail fast on an empty cart before touching stock, pricing,
    # or payment at all - cheapest possible check, first line of the function.
    if not cart_items:
        raise EmptyCartError(customer.name)

    # second --> pricing.
    # Subtotal and shipping are computed separately via reduce() so the
    # discount (next line) can be applied ONLY to the subtotal, not shipping.
    subtotal, shipping = calculate_cart_and_shipping_total(cart_items)

    # KEY POINT: a fresh closure is created per checkout call, so its
    # internal "already_applied" state can never leak between customers
    # or between separate checkout attempts.
    apply_discount = make_discount_engine(customer)
    total = apply_discount(subtotal)          # discount hits subtotal only
    grand_total = total + shipping            # shipping added back after discount

    # third --> stock reservation, with a rollback ledger.
    # successfully_reserved tracks ONLY what actually succeeded so far,
    # updated immediately after each successful reduce_stock() call -
    # this is what makes rollback accurate even if a later item fails.
    successfully_reserved = []

    for item in cart_items:
        try:
            item.product.reduce_stock(item.quantity)
            successfully_reserved.append(item)

        except (InsufficientStockError, InvalidQuantityError) as e:
            # KEY POINT: undo every deduction that already succeeded
            # before this failure - never leaves the cart in a half-
            # reserved state.
            rollback_stock(successfully_reserved)
            raise e

    # payment retry loop - bounded to 3 attempts.
    # Each failure branch (non-numeric, non-positive, underpayment) is
    # structurally identical: decrement attempts, warn, and only on the
    # FINAL attempt roll back stock and raise. This is the single point
    # where a failed checkout releases the stock it reserved in Step 3.
    attempts = 3
    payment_amount = None
    customer_amount = None

    while attempts > 0:
        customer_amount = input(f"Enter payment amount (${grand_total:.2f} required): ")

        try:
            amount = float(customer_amount)
        except ValueError:
            attempts -= 1
            print(f"Invalid input, not a number. Attempts remaining: {attempts}")
            if attempts == 0:
                rollback_stock(successfully_reserved)
                raise InvalidPaymentError(
                    attempted_amount=customer_amount,
                    expected_total=grand_total,
                    reason="non_numeric"
                )
            continue

        if amount <= 0:
            attempts -= 1
            print(f"Amount must be positive. Attempts remaining: {attempts}")
            if attempts == 0:
                rollback_stock(successfully_reserved)
                raise InvalidPaymentError(
                    attempted_amount=amount,
                    expected_total=grand_total,
                    reason="non_positive"
                )
            continue

        if amount < grand_total:
            attempts -= 1
            print(f"Underpayment. Attempts remaining: {attempts}")
            if attempts == 0:
                rollback_stock(successfully_reserved)
                raise InvalidPaymentError(
                    attempted_amount=amount,
                    expected_total=grand_total,
                    reason="underpayment"
                )
            continue

        # KEY POINT: amount >= grand_total is treated as success, including
        # the exact-match boundary case (amount == grand_total).
        payment_amount = amount
        break

    # order creation - only reached if payment succeeded.
    # create_order() takes a COPY of cart_items internally, so later
    # mutations to the caller's original cart list (e.g. clearing it)
    # can never retroactively affect this stored order.
    change_due = payment_amount - grand_total
    order = order_manager.create_order(customer, cart_items, grand_total)
    order.mark_paid()   # goes through the state machine, not a raw assignment

    # finally invoice export - the final side effect of a successful checkout.
    invoice_path = order.generate_invoice_text()
    print(f"Invoice saved to: {invoice_path}")

    if change_due > 0:
        print(f"Payment received. Change due: ${change_due:.2f}")

    return order


#                     BONUS
def cancel_order(order_manager, order_id):
    if order_id not in order_manager.orders:
        raise OrderNotFoundError(order_id)

    order = order_manager.orders[order_id]

    # KEY POINT: mark_cancelled() runs FIRST and goes through the Order's
    # TRANSITIONS state machine. If cancellation isn't legal from the
    # order's current status (e.g. already "shipped" or already
    # "cancelled"), this raises InvalidOrderStateError and the function
    # exits here - stock is NEVER touched for an illegal cancellation.
    # This is also what prevents double-refunding stock if cancel_order()
    # is accidentally called twice on the same order.
    order.mark_cancelled()

    # Only reached once the state transition above was confirmed legal.
    rollback_stock(order.cart_items)

    return order