Build a Python module named `todo.py` that implements a small todo list manager.

Requirements:
- Create a class `TodoList(storage_path: str | None = None)`.
- If `storage_path` is provided, todos should be persisted to that JSON file.
- If the file does not exist, start with an empty list.
- If the file exists but contains invalid JSON, raise `ValueError` when constructing the class.
- Each todo item should have:
  - `id: int`
  - `title: str`
  - `done: bool`
- IDs should start at 1 and increase by 1 for each new item.
- Implement these methods:

  1. `add(title: str) -> dict`
     - Strips surrounding whitespace from title.
     - Raises `ValueError` if title is empty after stripping.
     - Returns the created todo item.

  2. `list_all() -> list[dict]`
     - Returns all todos in insertion order.

  3. `complete(todo_id: int) -> dict`
     - Marks the matching todo as done.
     - Raises `KeyError` if the id does not exist.
     - Returns the updated todo.

  4. `remove(todo_id: int) -> dict`
     - Removes the matching todo.
     - Raises `KeyError` if the id does not exist.
     - Returns the removed todo.

- Changes must be saved immediately when `storage_path` is provided.
- Do not use external dependencies.
- Include clear docstrings and type hints.
- Keep the implementation simple.

Behavior notes:
- Removing an item does not reuse IDs.
- Re-loading from disk should preserve items and the next generated ID.

In the end run the tests:
pytest test_todo.py -v
