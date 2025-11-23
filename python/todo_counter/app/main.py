from .todo_utils import count_todos

TODOS = [
    {"text": "Buy milk", "done": False},
    {"text": "Clean room", "done": True},
    {"text": "Study AI", "done": False},
]


def main():
    print("Pending todos:", count_todos(TODOS))


if __name__ == "__main__":
    main()

