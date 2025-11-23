from .order_logic import calc_total
from .printer import format_receipt


def get_sample_order():
    return [
        {"name": "Book", "price": 30.0, "quantity": 2},
        {"name": "Pen", "price": 5.0, "quantity": 4},
        {"name": "Laptop Stand", "price": 60.0, "quantity": 1},
    ]


def main():
    items = get_sample_order()
    total = calc_total(items)
    print("Final total (with tax and discount if any):", total)
    print()
    print("Receipt:")
    print(format_receipt(items))


if __name__ == "__main__":
    main()

