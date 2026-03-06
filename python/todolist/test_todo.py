import json
import os
import pytest

from todo import TodoList


def test_add_and_list_all_in_memory():
    todos = TodoList()

    first = todos.add("Buy milk")
    second = todos.add("Walk dog")

    assert first == {"id": 1, "title": "Buy milk", "done": False}
    assert second == {"id": 2, "title": "Walk dog", "done": False}

    assert todos.list_all() == [
        {"id": 1, "title": "Buy milk", "done": False},
        {"id": 2, "title": "Walk dog", "done": False},
    ]


def test_add_strips_whitespace():
    todos = TodoList()

    item = todos.add("   Clean room   ")

    assert item == {"id": 1, "title": "Clean room", "done": False}


def test_add_rejects_empty_title():
    todos = TodoList()

    with pytest.raises(ValueError):
        todos.add("")

    with pytest.raises(ValueError):
        todos.add("   ")


def test_complete_existing_item():
    todos = TodoList()
    todos.add("Task 1")
    updated = todos.complete(1)

    assert updated == {"id": 1, "title": "Task 1", "done": True}
    assert todos.list_all() == [{"id": 1, "title": "Task 1", "done": True}]


def test_complete_missing_item_raises_keyerror():
    todos = TodoList()

    with pytest.raises(KeyError):
        todos.complete(123)


def test_remove_existing_item():
    todos = TodoList()
    todos.add("A")
    todos.add("B")

    removed = todos.remove(1)

    assert removed == {"id": 1, "title": "A", "done": False}
    assert todos.list_all() == [{"id": 2, "title": "B", "done": False}]


def test_remove_missing_item_raises_keyerror():
    todos = TodoList()

    with pytest.raises(KeyError):
        todos.remove(999)


def test_ids_are_not_reused_after_remove():
    todos = TodoList()
    todos.add("A")
    todos.add("B")
    todos.remove(1)

    item = todos.add("C")

    assert item["id"] == 3
    assert todos.list_all() == [
        {"id": 2, "title": "B", "done": False},
        {"id": 3, "title": "C", "done": False},
    ]


def test_persists_to_json_file(tmp_path):
    path = tmp_path / "todos.json"

    todos = TodoList(str(path))
    todos.add("Buy milk")
    todos.add("Walk dog")
    todos.complete(2)

    raw = json.loads(path.read_text())

    assert raw == [
        {"id": 1, "title": "Buy milk", "done": False},
        {"id": 2, "title": "Walk dog", "done": True},
    ]


def test_reload_from_existing_file_preserves_items_and_next_id(tmp_path):
    path = tmp_path / "todos.json"

    first = TodoList(str(path))
    first.add("A")
    first.add("B")

    second = TodoList(str(path))
    assert second.list_all() == [
        {"id": 1, "title": "A", "done": False},
        {"id": 2, "title": "B", "done": False},
    ]

    new_item = second.add("C")
    assert new_item == {"id": 3, "title": "C", "done": False}


def test_missing_file_starts_empty(tmp_path):
    path = tmp_path / "missing.json"

    todos = TodoList(str(path))

    assert todos.list_all() == []


def test_invalid_json_raises_value_error(tmp_path):
    path = tmp_path / "todos.json"
    path.write_text("{not valid json")

    with pytest.raises(ValueError):
        TodoList(str(path))


def test_changes_saved_immediately(tmp_path):
    path = tmp_path / "todos.json"

    todos = TodoList(str(path))
    todos.add("A")

    reloaded = TodoList(str(path))
    assert reloaded.list_all() == [{"id": 1, "title": "A", "done": False}]

    todos.complete(1)

    reloaded = TodoList(str(path))
    assert reloaded.list_all() == [{"id": 1, "title": "A", "done": True}]

    todos.remove(1)

    reloaded = TodoList(str(path))
    assert reloaded.list_all() == []
