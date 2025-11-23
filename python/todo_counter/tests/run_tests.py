from tests.test_todo_utils import test_count_todos


def run():
    results = [
        test_count_todos(),
    ]

    failed = [r for r in results if not r["pass"]]
    if failed:
        print("Tests failed:")
        for case in failed:
            print(f"- {case['name']}: got {case['result']}")
        raise SystemExit(1)

    print("All tests passed!")


if __name__ == "__main__":
    run()

