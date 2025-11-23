from app.todo_utils import count_todos


def test_count_todos():
    todos = [
        {"done": False},
        {"done": True},
        {"done": False},
    ]
    result = count_todos(todos)
    return {
        "name": "count_todos counts only not-done items",
        "pass": result == 2,
        "result": result,
    }

