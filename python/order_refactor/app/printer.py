from .order_logic import TAX_RATE, DISCOUNT_THRESHOLD, DISCOUNT_RATE


def _calc_subtotal_for_receipt(items):
    total = 0.0
    for item in items:
        total += item["price"] * item.get("quantity", 1)
    return total


def _calc_discount_amount(subtotal):
    if subtotal > DISCOUNT_THRESHOLD:
        return subtotal * DISCOUNT_RATE
    return 0.0


def _calc_tax_amount(after_discount):
    return after_discount * TAX_RATE


def format_receipt(items):
    """
    Returns a multi-line string with:
      Subtotal
      Discount
      Tax
      Total
    """
    subtotal = _calc_subtotal_for_receipt(items)
    discount = _calc_discount_amount(subtotal)
    after_discount = subtotal - discount
    tax = _calc_tax_amount(after_discount)
    total = after_discount + tax

    lines = [
        f"Subtotal: {subtotal:.2f}",
        f"Discount: {discount:.2f}",
        f"Tax: {tax:.2f}",
        f"Total: {total:.2f}",
    ]
    return "\n".join(lines)

