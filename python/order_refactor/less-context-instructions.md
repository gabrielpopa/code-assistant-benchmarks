REFACTOR the code to a cleaner design, while preserving behavior.

Perform ALL the steps below:

1. Introduce a proper domain model

Implement classes that represent:

- an order (items and their structure)
- a calculator (responsible for subtotal, discount, tax, and total)
- These classes should replace the current free-function implementation and duplicated logic.

2. Unify the calculation logic

- All pricing/discount/tax logic should live in one place, with a single clear public API.
- The rest of the project should depend on this API rather than re-implementing behavior.

3. Remove duplication

- app/printer.py currently re-calculates subtotal, discount, and tax.
- Refactor it to use the new model/calculator instead.

4. Remove obsolete code

- The legacy.py indirection is no longer needed after refactoring.
- Remove it and redirect any callers to the new API.

5. Update the main program

Refactor app/main.py to use the new design while producing exactly the same output as before.

6. Update and extend tests

- Update existing tests to use the new API where appropriate.
- Add tests for the receipt formatting to ensure the output still matches.
- Ensure the test runner executes all tests.
- All tests must pass after the refactor.

7. Preserve behavior

Even after the major architectural changes:

- The final total for the sample order must remain correct.
- The formatted receipt must contain the same numerical values as before.
- python -m tests.run_tests must succeed.
- python -m app.main must produce the same numbers and layout.

8. Final cleanup

- No unused code.
- No leftover legacy functions.
- No duplicate logic.
- The final architecture should be clean, readable, and maintainable.
