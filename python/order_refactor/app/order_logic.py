TAX_RATE = 0.2  # 20% VAT
DISCOUNT_THRESHOLD = 100.0
DISCOUNT_RATE = 0.1  # 10% discount over threshold


def calc_subtotal(items):
    total = 0.0
    for item in items:
        total += item["price"] * item.get("quantity", 1)
    return total


def apply_discount_if_any(total):
    if total > DISCOUNT_THRESHOLD:
        return total * (1.0 - DISCOUNT_RATE)
    return total


def calc_total(items):
    """
    Returns the final total including discount (if any) and tax.
    """
    subtotal = calc_subtotal(items)
    discounted = apply_discount_if_any(subtotal)
    total = discounted * (1.0 + TAX_RATE)
    return round(total, 2)

