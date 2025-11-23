You are being benchmarked on refactoring skills.

We have a small Python codebase:

- app/__init__.py
- app/main.py
- app/order_logic.py
- app/printer.py
- app/legacy.py
- tests/__init__.py
- tests/run_tests.py
- tests/test_order_logic.py

Current behavior:
- python -m tests.run_tests  -> All tests pass
- python -m app.main         -> prints a total and a receipt

Your goal: REFACTOR the code to a cleaner design, while preserving behavior.

Perform ALL the steps below:

1. Introduce an Order and OrderCalculator abstraction:
   - Create a new file app/order_model.py
   - Define:
       class Order:
           - takes a list of item dicts (same structure as now)
           - exposes a property or method items to access them

       class OrderCalculator:
           - initialized with tax_rate, discount_threshold, discount_rate
           - has methods:
               subtotal(order)
               discount(order)
               total_without_tax(order)
               tax_amount(order)
               total_with_tax(order)

2. Refactor app/order_logic.py to:
   - Use Order and OrderCalculator under the hood
   - Keep a small, clear public API:
       create_default_calculator() -> OrderCalculator
       calc_total(items)           -> float (same behavior as before, using the calculator)
   - Remove the old calc_subtotal and apply_discount_if_any functions
     from the public API (if needed, keep them as private helpers or move their logic into OrderCalculator).

3. Refactor app/printer.py to REMOVE duplicated logic:
   - Use Order and OrderCalculator instead of re-implementing subtotal / discount / tax.
   - format_receipt(items) should:
       - create an Order from items
       - use create_default_calculator() from app.order_logic
       - compute subtotal, discount, tax, total via the calculator
       - return the same formatted receipt text as before (same numbers).

4. Remove the legacy indirection:
   - app/legacy.py currently provides calc_total_price(items).
   - Replace it by:
       - moving any necessary behavior into the new classes or order_logic functions
       - DELETING app/legacy.py entirely after its functionality is covered.
   - If any references exist (you may add one to main during the refactor), update them to use the new API instead.

5. Refactor app/main.py:
   - Use Order and OrderCalculator:
       - create an Order from get_sample_order()
       - use create_default_calculator() to compute the total
       - print the total exactly as before
       - print the receipt using format_receipt(items) (which should now be using the calculator internally).
   - Do not hardcode tax / discount rates in main; they should come from the calculator / order_logic.

6. Update and extend tests:
   - Update tests/test_order_logic.py so that:
       - it uses create_default_calculator() and Order where appropriate
       - it still tests that the final total for SAMPLE_ITEMS is 151.2
   - Add a NEW test file tests/test_printer.py with at least:
       - a test that format_receipt(SAMPLE_ITEMS) contains the expected lines:
           "Subtotal: 140.00"
           "Discount: 14.00"
           "Tax: 25.20"
           "Total: 151.20"
   - Update tests/run_tests.py to:
       - import and run the new tests from tests.test_printer.

7. Cleanup:
   - Ensure there is no dead code left (unused functions, unused imports).
   - Ensure app/legacy.py is deleted from the project.

8. Finally, verify:
   - python -m tests.run_tests  -> All tests passed!
   - python -m app.main         -> still prints the same numeric results as before.

Make all required file system changes and code edits.
Do NOT change the expected numerical results.
Preserve behavior while improving the design.
