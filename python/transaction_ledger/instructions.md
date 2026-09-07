# Python benchmark: transaction ledger

Create a single module named `ledger.py` in this directory. Do not create tests and
do not use third-party dependencies.

Implement a persistent, idempotent transaction ledger with this public API:

```python
from decimal import Decimal

class Ledger:
    def __init__(self, storage_path: str | None = None): ...
    def create_account(self, name: str, opening_balance=0) -> Decimal: ...
    def deposit(self, name: str, amount, transaction_id: str) -> Decimal: ...
    def withdraw(self, name: str, amount, transaction_id: str) -> Decimal: ...
    def transfer(
        self,
        source: str,
        destination: str,
        amount,
        transaction_id: str,
    ) -> tuple[Decimal, Decimal]: ...
    def balance(self, name: str) -> Decimal: ...
    def snapshot(self) -> dict[str, Decimal]: ...
```

## Accounts

- Account names must be strings. Strip surrounding whitespace before using them.
- A name that is empty after stripping is invalid and raises `ValueError`.
- `create_account` raises `ValueError` when the normalized name already exists.
- `balance` and all transaction methods raise `KeyError` for an unknown account.
- `create_account` returns the account's opening balance.
- `snapshot` returns all balances keyed by normalized account name. Mutating the
  returned dictionary must not affect the ledger.

## Money

- Monetary arguments accept `Decimal`, `int`, or a base-10 string such as
  `"12.30"`. An `int` represents whole currency units, not cents.
- Reject booleans, floats, malformed strings, NaN, infinity, and values with more
  than two fractional decimal places by raising `ValueError`.
- Opening balances may be zero but not negative. Transaction amounts must be
  strictly greater than zero.
- All returned balances must be `Decimal` values quantized to exactly two decimal
  places (for example, `Decimal("12.30")`). Do not perform arithmetic using floats.

## Transactions

- Transaction IDs must be non-empty strings after stripping. Use the stripped ID.
- `deposit` adds funds and returns the new account balance.
- `withdraw` subtracts funds and returns the new account balance. If funds are
  insufficient, raise `ValueError` without changing any state.
- `transfer` moves funds atomically and returns
  `(new_source_balance, new_destination_balance)`. Both accounts must exist,
  source and destination must differ, and the source must have sufficient funds.
  Any failure must leave both balances unchanged.

Transaction IDs are globally idempotent:

- Repeating a successful transaction with the same ID, operation, normalized
  account name(s), and normalized amount must return the original result without
  applying it again.
- Reusing an ID for different transaction details raises `ValueError` without
  changing state.
- Failed transactions do not consume their transaction ID.

## Optional JSON persistence

- With no `storage_path`, keep state in memory only.
- If a storage path is supplied and the file does not exist, start empty.
- After every successful state-changing call, save accounts and idempotency data
  immediately. A successful idempotent retry need not rewrite the file.
- Reloading a `Ledger` from that file must restore balances and idempotent retry
  behavior.
- Store money as decimal strings in JSON. The exact JSON object layout is your
  choice.
- If the file cannot be decoded as JSON or does not contain valid ledger data,
  construction must raise `ValueError` (not leak a JSON decoding, decimal, or
  type-related exception).
- Persist safely by writing a temporary file in the same directory and replacing
  the destination, so an interrupted write cannot leave a partially written file.

Keep the implementation readable and include useful type hints and docstrings.

