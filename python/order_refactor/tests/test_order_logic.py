from app.order_logic import calc_total, calc_subtotal, apply_discount_if_any

SAMPLE_ITEMS = [
    {"name": "Book", "price": 30.0, "quantity": 2},  # 60
    {"name": "Pen", "price": 5.0, "quantity": 4},    # 20
    {"name": "Laptop Stand", "price": 60.0, "quantity": 1},  # 60
]
# subtotal = 140.0
# discount = 14.0  (10% over 100)
# after_discount = 126.0
# tax = 25.2 (20%)
# total = 151.2


def test_calc_subtotal():
    assert calc_subtotal(SAMPLE_ITEMS) == 140.0


def test_apply_discount_if_any():
    assert apply_discount_if_any(50.0) == 50.0  # below threshold
    assert apply_discount_if_any(140.0) == 126.0  # above threshold


def test_calc_total():
    assert calc_total(SAMPLE_ITEMS) == 151.2

