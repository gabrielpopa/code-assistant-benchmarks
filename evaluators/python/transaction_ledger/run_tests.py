"""Hidden evaluator for the transaction_ledger benchmark.

Run from the repository root with:
    python3 evaluators/python/transaction_ledger/run_tests.py python/transaction_ledger

In an actual benchmark, mount only the task directory into the model harness. This
evaluator deliberately lives outside that directory and should be run afterward by
the benchmark operator.
"""

from __future__ import annotations

import importlib.util
import inspect
import json
import sys
import tempfile
from decimal import Decimal
from pathlib import Path
from typing import Callable


CandidateFactory = Callable[..., object]
TESTS: list[tuple[str, Callable[[CandidateFactory], None]]] = []


def test(name: str):
    def register(fn: Callable[[CandidateFactory], None]):
        TESTS.append((name, fn))
        return fn

    return register


def assert_decimal(value, expected: str) -> None:
    assert isinstance(value, Decimal), f"expected Decimal, got {type(value).__name__}"
    assert value == Decimal(expected), f"expected {expected}, got {value}"
    assert value.as_tuple().exponent == -2, f"{value!r} is not quantized to 2 places"


def assert_raises(exception_type, fn, *args) -> Exception:
    try:
        fn(*args)
    except exception_type as exc:
        return exc
    except Exception as exc:  # pragma: no cover - diagnostic path
        raise AssertionError(
            f"expected {exception_type.__name__}, got {type(exc).__name__}: {exc}"
        ) from exc
    raise AssertionError(f"expected {exception_type.__name__} to be raised")


@test("public API and empty ledger")
def _(Ledger):
    ledger = Ledger()
    assert ledger.snapshot() == {}
    for method in ("create_account", "deposit", "withdraw", "transfer", "balance", "snapshot"):
        assert callable(getattr(ledger, method, None)), f"missing method: {method}"


@test("create account normalizes name and balance")
def _(Ledger):
    ledger = Ledger()
    assert_decimal(ledger.create_account("  Alice  ", "12.3"), "12.30")
    assert_decimal(ledger.balance(" Alice "), "12.30")
    assert ledger.snapshot() == {"Alice": Decimal("12.30")}


@test("duplicate and invalid account names")
def _(Ledger):
    ledger = Ledger()
    ledger.create_account("Alice")
    assert_raises(ValueError, ledger.create_account, " Alice ")
    for bad_name in ("", "   ", None, 123):
        assert_raises(ValueError, ledger.create_account, bad_name)


@test("unknown accounts raise KeyError")
def _(Ledger):
    ledger = Ledger()
    assert_raises(KeyError, ledger.balance, "missing")
    assert_raises(KeyError, ledger.deposit, "missing", "1.00", "d1")
    assert_raises(KeyError, ledger.withdraw, "missing", "1.00", "w1")


@test("accepted money representations")
def _(Ledger):
    ledger = Ledger()
    assert_decimal(ledger.create_account("a", 2), "2.00")
    assert_decimal(ledger.deposit("a", Decimal("0.10"), "d1"), "2.10")
    assert_decimal(ledger.deposit("a", " .20 ", "d2"), "2.30")


@test("invalid money representations")
def _(Ledger):
    invalid = (True, False, 1.0, "", "abc", "1.001", Decimal("0.001"), "NaN", "Infinity")
    for index, amount in enumerate(invalid):
        ledger = Ledger()
        assert_raises(ValueError, ledger.create_account, f"a{index}", amount)
        ledger.create_account("valid")
        assert_raises(ValueError, ledger.deposit, "valid", amount, f"tx{index}")


@test("opening and transaction amount bounds")
def _(Ledger):
    ledger = Ledger()
    assert_raises(ValueError, ledger.create_account, "negative", "-0.01")
    ledger.create_account("a", 1)
    for index, amount in enumerate((0, "0.00", "-1.00")):
        assert_raises(ValueError, ledger.deposit, "a", amount, f"d{index}")
        assert_raises(ValueError, ledger.withdraw, "a", amount, f"w{index}")


@test("deposit and withdraw arithmetic")
def _(Ledger):
    ledger = Ledger()
    ledger.create_account("a", "10.00")
    assert_decimal(ledger.deposit("a", "2.35", " d1 "), "12.35")
    assert_decimal(ledger.withdraw("a", Decimal("1.10"), "w1"), "11.25")
    assert_decimal(ledger.balance("a"), "11.25")


@test("insufficient withdrawal is atomic")
def _(Ledger):
    ledger = Ledger()
    ledger.create_account("a", 3)
    assert_raises(ValueError, ledger.withdraw, "a", 4, "try")
    assert_decimal(ledger.balance("a"), "3.00")
    assert_decimal(ledger.deposit("a", 1, "try"), "4.00")


@test("transfer updates both accounts")
def _(Ledger):
    ledger = Ledger()
    ledger.create_account("source", "9.00")
    ledger.create_account("destination", "1.00")
    result = ledger.transfer(" source ", " destination ", "2.25", "t1")
    assert isinstance(result, tuple)
    assert_decimal(result[0], "6.75")
    assert_decimal(result[1], "3.25")


@test("invalid transfer is atomic")
def _(Ledger):
    ledger = Ledger()
    ledger.create_account("a", 5)
    ledger.create_account("b", 2)
    assert_raises(ValueError, ledger.transfer, "a", "a", 1, "same")
    assert_raises(ValueError, ledger.transfer, "a", "b", 6, "large")
    assert_raises(KeyError, ledger.transfer, "a", "missing", 1, "missing")
    assert ledger.snapshot() == {"a": Decimal("5.00"), "b": Decimal("2.00")}
    assert_decimal(ledger.transfer("a", "b", 1, "large")[0], "4.00")


@test("transaction IDs are validated and normalized")
def _(Ledger):
    ledger = Ledger()
    ledger.create_account("a")
    for transaction_id in ("", "   ", None, 3):
        assert_raises(ValueError, ledger.deposit, "a", 1, transaction_id)
    assert_decimal(ledger.deposit("a", 1, " tx "), "1.00")
    assert_decimal(ledger.deposit("a", Decimal("1.00"), "tx"), "1.00")


@test("deposit retry is idempotent")
def _(Ledger):
    ledger = Ledger()
    ledger.create_account("a")
    first = ledger.deposit("a", "1.20", "id")
    second = ledger.deposit(" a ", Decimal("1.2"), " id ")
    assert first == second
    assert_decimal(ledger.balance("a"), "1.20")


@test("withdraw and transfer retries are idempotent")
def _(Ledger):
    ledger = Ledger()
    ledger.create_account("a", 10)
    ledger.create_account("b")
    first_withdrawal = ledger.withdraw("a", 2, "w")
    assert ledger.withdraw("a", "2.00", "w") == first_withdrawal
    first_transfer = ledger.transfer("a", "b", 3, "t")
    assert ledger.transfer("a", "b", Decimal("3.0"), "t") == first_transfer
    assert ledger.snapshot() == {"a": Decimal("5.00"), "b": Decimal("3.00")}


@test("conflicting transaction ID does not mutate")
def _(Ledger):
    ledger = Ledger()
    ledger.create_account("a", 10)
    ledger.create_account("b")
    ledger.deposit("a", 1, "used")
    before = ledger.snapshot()
    assert_raises(ValueError, ledger.deposit, "a", 2, "used")
    assert_raises(ValueError, ledger.withdraw, "a", 1, "used")
    assert_raises(ValueError, ledger.transfer, "a", "b", 1, "used")
    assert ledger.snapshot() == before


@test("snapshot is defensive")
def _(Ledger):
    ledger = Ledger()
    ledger.create_account("a", 4)
    copy = ledger.snapshot()
    copy["a"] = Decimal("999.00")
    copy["new"] = Decimal("1.00")
    assert ledger.snapshot() == {"a": Decimal("4.00")}


@test("missing persistence file starts empty and saves")
def _(Ledger):
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "ledger.json"
        ledger = Ledger(str(path))
        assert ledger.snapshot() == {}
        assert not path.exists()
        ledger.create_account("a", "1.25")
        assert path.exists()
        document = json.loads(path.read_text(encoding="utf-8"))
        assert "1.25" in path.read_text(encoding="utf-8")
        assert isinstance(document, dict)


@test("persistence reloads accounts")
def _(Ledger):
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "ledger.json"
        first = Ledger(str(path))
        first.create_account("a", 5)
        first.create_account("b")
        first.transfer("a", "b", "1.50", "move")
        second = Ledger(str(path))
        assert second.snapshot() == {"a": Decimal("3.50"), "b": Decimal("1.50")}


@test("persistence restores idempotency")
def _(Ledger):
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "ledger.json"
        first = Ledger(str(path))
        first.create_account("a")
        assert_decimal(first.deposit("a", 2, "once"), "2.00")
        second = Ledger(str(path))
        assert_decimal(second.deposit("a", "2.00", "once"), "2.00")
        assert_raises(ValueError, second.deposit, "a", 3, "once")
        assert_decimal(second.balance("a"), "2.00")


@test("every successful change is saved immediately")
def _(Ledger):
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "ledger.json"
        ledger = Ledger(str(path))
        ledger.create_account("a", 10)
        assert_decimal(Ledger(str(path)).balance("a"), "10.00")
        ledger.deposit("a", 2, "d")
        assert_decimal(Ledger(str(path)).balance("a"), "12.00")
        ledger.withdraw("a", 1, "w")
        assert_decimal(Ledger(str(path)).balance("a"), "11.00")


@test("invalid persisted JSON is wrapped as ValueError")
def _(Ledger):
    invalid_documents = ("{not json", "[]", "null", '"text"', "123")
    with tempfile.TemporaryDirectory() as directory:
        for index, document in enumerate(invalid_documents):
            path = Path(directory) / f"bad-{index}.json"
            path.write_text(document, encoding="utf-8")
            assert_raises(ValueError, Ledger, str(path))


@test("corrupt money in persisted data raises ValueError")
def _(Ledger):
    def corrupt_money(value):
        if value == "1.00":
            return "NaN"
        if isinstance(value, dict):
            return {key: corrupt_money(item) for key, item in value.items()}
        if isinstance(value, list):
            return [corrupt_money(item) for item in value]
        return value

    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "ledger.json"
        ledger = Ledger(str(path))
        ledger.create_account("a", "1.00")
        document = json.loads(path.read_text(encoding="utf-8"))
        corrupted = corrupt_money(document)
        assert corrupted != document, "persisted money must use two-place decimal strings"
        path.write_text(json.dumps(corrupted), encoding="utf-8")
        assert_raises(ValueError, Ledger, str(path))


@test("failed persistent transaction leaves file unchanged")
def _(Ledger):
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "ledger.json"
        ledger = Ledger(str(path))
        ledger.create_account("a", 1)
        before = path.read_bytes()
        assert_raises(ValueError, ledger.withdraw, "a", 2, "failed")
        assert path.read_bytes() == before


@test("implementation has class documentation and type hints")
def _(Ledger):
    assert inspect.getdoc(Ledger), "Ledger needs a docstring"
    public = (Ledger.__init__, Ledger.create_account, Ledger.deposit, Ledger.withdraw,
              Ledger.transfer, Ledger.balance, Ledger.snapshot)
    for method in public:
        assert inspect.signature(method).return_annotation is not inspect.Signature.empty, (
            f"{method.__name__} needs a return type hint"
        )


def load_candidate(candidate_directory: Path):
    module_path = candidate_directory / "ledger.py"
    if not module_path.is_file():
        raise FileNotFoundError(f"candidate module not found: {module_path}")
    spec = importlib.util.spec_from_file_location("benchmark_candidate_ledger", module_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {module_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    ledger_class = getattr(module, "Ledger", None)
    if not isinstance(ledger_class, type):
        raise TypeError("ledger.py must export a Ledger class")
    return ledger_class


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: python run_tests.py PATH_TO_CANDIDATE_DIRECTORY")
        return 2

    try:
        Ledger = load_candidate(Path(sys.argv[1]).resolve())
    except Exception as exc:
        print(f"Could not load candidate: {type(exc).__name__}: {exc}")
        print(f"0/{len(TESTS)} tests passed")
        return 1

    failures: list[tuple[str, str]] = []
    for name, fn in TESTS:
        try:
            fn(Ledger)
        except Exception as exc:
            failures.append((name, f"{type(exc).__name__}: {exc}"))

    passed = len(TESTS) - len(failures)
    print(f"{passed}/{len(TESTS)} tests passed")
    if failures:
        print("Failures:")
        for name, detail in failures:
            print(f"- {name}: {detail}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
