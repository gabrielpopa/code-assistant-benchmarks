# Transaction ledger evaluator

This directory is operator-only. Do not expose or mount it when the model is
working on `python/transaction_ledger`.

After the model finishes, run from the repository root:

```bash
python3 evaluators/python/transaction_ledger/run_tests.py python/transaction_ledger
```

The runner uses only the Python standard library, executes each check separately,
prints a `passed/total` score, lists failed behaviors, and exits non-zero unless all
checks pass.
