# Yuvro Scoring Rules — Django Todo Signup Bugs

This directory contains the automated scoring harness for the "Django todo Signup bugs" engineering lab.

## Structure

- `main_test.py` — Entry point. Sets up Django, runs each task test, aggregates results, and prints a single JSON object to stdout.
- `test1.py` — Task 1: User registration endpoint validation (`/api/register/`).
- `test2.py` — Task 2: Todo creation & ownership (`POST /api/todos/`).
- `test3.py` — Task 3: Todo listing & filtering (`GET /api/todos/`).

Each `testN.py` exposes an `evaluate()` function returning:

```json
{ "result": "passed" | "failed", "score": <int>, "message": "..." }
```

## How it works

1. `main_test.py` sets `DJANGO_SETTINGS_MODULE` (defaults to `todo_project.settings`, with fallbacks) and calls `django.setup()`.
2. Each task test uses `django.test.Client` to exercise the API endpoints.
3. Test data (users, todos) is created with unique usernames and cleaned up in a `finally` block.
4. All exceptions are caught and converted into a `failed` result so the JSON output is never broken.

## Scoring

- Task 1: 10 marks (6 checks)
- Task 2: 10 marks (4 checks)
- Task 3: 10 marks (5 checks)
- Total: 30 marks

A task is marked `passed` only if all of its checks pass. Otherwise it is `failed` with score 0 and a message listing the failing checks.

## Running locally

From the project root (where `manage.py` lives):

```bash
python yuvro_scoring_rules/main_test.py
```

You should see a single JSON object on stdout:

```json
{
  "tasks": {
    "task1": { "result": "passed", "score": 10, "message": "..." },
    "task2": { "result": "passed", "score": 10, "message": "..." },
    "task3": { "result": "passed", "score": 10, "message": "..." }
  },
  "total_score": 30,
  "max_possible_score": 30
}
```

## Notes

- The harness assumes the Django project is importable from the current working directory.
- If your settings module has a different name, set `DJANGO_SETTINGS_MODULE` before running, or add a fallback in `main_test.py`.
- The Todo model is auto-discovered across common app labels (`todo`, `todos`, `todoapp`, `api`, `core`) and by model name.
