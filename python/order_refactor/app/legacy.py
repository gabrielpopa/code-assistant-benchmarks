from .order_logic import calc_total


def calc_total_price(items):
    # Legacy name kept for backward compatibility
    # but ideally we should use something more structured now.
    return calc_total(items)

