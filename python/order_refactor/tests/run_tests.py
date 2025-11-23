from tests.test_order_logic import (
    test_calc_subtotal,
    test_apply_discount_if_any,
    test_calc_total,
)


def run():
    tests = [
        ("test_calc_subtotal", test_calc_subtotal),
        ("test_apply_discount_if_any", test_apply_discount_if_any),
        ("test_calc_total", test_calc_total),
    ]

    failed = []
    for name, fn in tests:
        try:
            fn()
        except AssertionError:
            failed.append(name)

    if failed:
        print("Tests failed:", ", ".join(failed))
        raise SystemExit(1)

    print("All tests passed!")


if __name__ == "__main__":
    run()

