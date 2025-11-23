You are being benchmarked.
Perform ALL steps below by editing the project files in this Python codebase.

Current structure:
- app/__init__.py
- app/main.py
- app/todo_utils.py
- tests/__init__.py
- tests/run_tests.py
- tests/test_todo_utils.py

1. Fix the bug in app/todo_utils.py:
   - count_todos(todos) must return the number of todos where done == False.

2. Add a NEW function filter_done_todos(todos) in app/todo_utils.py:
   - returns a new list containing only items where done == True.

3. Update app/main.py to:
   - import filter_done_todos
   - print "Completed todos: X" where X is the number of done items
   - print the completed todo texts, one per line, after that

4. Create a NEW file app/summary.py that exports:
   - summarize(todos): returns a string like:
       "2 pending, 1 completed"
     based on the done flag in the given todos list.

5. Modify app/main.py to import summarize and print its result at the end.

6. Update tests:
   - Create tests/test_summary.py with a function test_summarize()
   - It must test that:
       summarize([
         {"done": False},
         {"done": True},
         {"done": False},
       ])
       returns exactly:
         "2 pending, 1 completed"

7. Update tests/run_tests.py:
   - import and run the new test_summarize function from tests/test_summary.py
   - include its result in the results list and in the failure reporting logic.

8. DELETE the file app/old_stuff.py if it exists.
   - For the purposes of this benchmark, create app/old_stuff.py and then delete it.

9. Finally:
   - Run the tests: python -m tests.run_tests
   - Run the project: python -m app.main
   - Confirm the output matches the expectations.

Make all required file system changes and code edits.
Do not skip any step.

