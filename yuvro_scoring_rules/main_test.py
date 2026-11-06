import os
import sys
import json
import traceback


def _setup_django():
    try:
        import django
    except ImportError:
        return False, "Django is not installed in the environment."
    try:
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'todo_project.settings')
        try:
            django.setup()
        except Exception as e:
            # Try common alternative settings modules
            for alt in ('settings', 'todo.settings', 'todoapp.settings', 'config.settings', 'mysite.settings'):
                try:
                    os.environ['DJANGO_SETTINGS_MODULE'] = alt
                    django.setup()
                    return True, None
                except Exception:
                    continue
            return False, "Django setup failed: %s" % str(e)
        return True, None
    except Exception as e:
        return False, "Django setup error: %s" % str(e)


def _run_task(module_name, task_key, max_score):
    try:
        mod = __import__(module_name, fromlist=['evaluate'])
        evaluate = getattr(mod, 'evaluate', None)
        if evaluate is None:
            return {"result": "failed", "score": 0, "message": "No evaluate() function found in %s" % module_name}
        result = evaluate()
        if not isinstance(result, dict):
            return {"result": "failed", "score": 0, "message": "evaluate() did not return a dict"}
        res = result.get('result', 'failed')
        score = result.get('score', 0)
        message = result.get('message', '')
        if res not in ('passed', 'failed'):
            res = 'failed'
        try:
            score = int(score)
        except Exception:
            score = 0
        if score < 0:
            score = 0
        if score > max_score:
            score = max_score
        if res == 'failed':
            score = 0
        return {"result": res, "score": score, "message": str(message)}
    except Exception as e:
        tb = traceback.format_exc()
        return {"result": "failed", "score": 0, "message": "Exception in %s: %s" % (module_name, str(e))}


def main():
    # Ensure the scoring rules directory is importable
    here = os.path.dirname(os.path.abspath(__file__))
    if here not in sys.path:
        sys.path.insert(0, here)

    ok, err = _setup_django()

    tasks = {}
    task_specs = [
        ('task1', 'test1', 10),
        ('task2', 'test2', 10),
        ('task3', 'test3', 10),
    ]

    if not ok:
        for key, _mod, max_score in task_specs:
            tasks[key] = {"result": "failed", "score": 0, "message": err or "Django setup failed"}
    else:
        for key, mod, max_score in task_specs:
            tasks[key] = _run_task(mod, key, max_score)

    total = sum(t.get('score', 0) for t in tasks.values())
    max_possible = sum(s for _k, _m, s in task_specs)

    output = {
        "tasks": tasks,
        "total_score": total,
        "max_possible_score": max_possible,
    }
    sys.stdout.write(json.dumps(output))
    sys.stdout.flush()


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        fallback = {
            "tasks": {
                "task1": {"result": "failed", "score": 0, "message": "Runner error: %s" % str(e)},
                "task2": {"result": "failed", "score": 0, "message": "Runner error: %s" % str(e)},
                "task3": {"result": "failed", "score": 0, "message": "Runner error: %s" % str(e)},
            },
            "total_score": 0,
            "max_possible_score": 30,
        }
        sys.stdout.write(json.dumps(fallback))
        sys.stdout.flush()
