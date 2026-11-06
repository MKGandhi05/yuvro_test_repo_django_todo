import json
import uuid


def _get_client():
    from django.test import Client
    return Client()


def _cleanup(username):
    try:
        from django.contrib.auth.models import User
        from django.apps import apps
        User.objects.filter(username=username).delete()
        try:
            Todo = apps.get_model('todo', 'Todo')
            Todo.objects.filter(owner__username=username).delete()
        except Exception:
            pass
    except Exception:
        pass


def _get_todo_model():
    from django.apps import apps
    for app_label in ('todo', 'todos', 'todoapp', 'api', 'core'):
        try:
            return apps.get_model(app_label, 'Todo')
        except Exception:
            continue
    for model in apps.get_models():
        if model.__name__.lower() == 'todo':
            return model
    raise Exception("Todo model not found")


def evaluate():
    try:
        from django.contrib.auth.models import User
    except Exception as e:
        return {"result": "failed", "score": 0, "message": "Cannot import User model: %s" % str(e)}

    try:
        Todo = _get_todo_model()
    except Exception as e:
        return {"result": "failed", "score": 0, "message": "Cannot locate Todo model: %s" % str(e)}

    client = _get_client()
    url = '/api/todos/'
    uname_a = 'u_%s' % uuid.uuid4().hex[:10]
    uname_b = 'u_%s' % uuid.uuid4().hex[:10]
    failures = []
    checks_passed = 0
    total_checks = 5

    try:
        # 1. Unauthenticated GET -> 401
        try:
            resp = client.get(url)
            if resp.status_code in (401, 403):
                checks_passed += 1
            else:
                failures.append("Unauthenticated GET expected 401/403, got %s" % resp.status_code)
        except Exception as e:
            failures.append("Unauthenticated GET error: %s" % str(e))

        user_a = User.objects.create_user(username=uname_a, password='validpass123', email='a@example.com')
        user_b = User.objects.create_user(username=uname_b, password='validpass123', email='b@example.com')

        # Seed data
        Todo.objects.create(title='A1', completed=False, owner=user_a)
        Todo.objects.create(title='A2', completed=True, owner=user_a)
        Todo.objects.create(title='B1', completed=False, owner=user_b)

        client.force_login(user_a)

        # 2. GET returns only user's todos
        try:
            resp = client.get(url)
            if resp.status_code == 200:
                body = resp.json() if hasattr(resp, 'json') else json.loads(resp.content.decode())
                if isinstance(body, dict) and 'results' in body:
                    body = body['results']
                titles = set()
                for item in body:
                    titles.add(item.get('title'))
                if titles == {'A1', 'A2'}:
                    checks_passed += 1
                else:
                    failures.append("Expected only A1,A2 got %s" % titles)
            else:
                failures.append("Authenticated GET expected 200, got %s" % resp.status_code)
        except Exception as e:
            failures.append("Authenticated GET error: %s" % str(e))

        # 3. Filter completed=true
        try:
            resp = client.get(url + '?completed=true')
            if resp.status_code == 200:
                body = resp.json() if hasattr(resp, 'json') else json.loads(resp.content.decode())
                if isinstance(body, dict) and 'results' in body:
                    body = body['results']
                titles = set(item.get('title') for item in body)
                if titles == {'A2'}:
                    checks_passed += 1
                else:
                    failures.append("completed=true expected A2 got %s" % titles)
            else:
                failures.append("completed=true expected 200, got %s" % resp.status_code)
        except Exception as e:
            failures.append("completed=true error: %s" % str(e))

        # 4. Filter completed=false
        try:
            resp = client.get(url + '?completed=false')
            if resp.status_code == 200:
                body = resp.json() if hasattr(resp, 'json') else json.loads(resp.content.decode())
                if isinstance(body, dict) and 'results' in body:
                    body = body['results']
                titles = set(item.get('title') for item in body)
                if titles == {'A1'}:
                    checks_passed += 1
                else:
                    failures.append("completed=false expected A1 got %s" % titles)
            else:
                failures.append("completed=false expected 200, got %s" % resp.status_code)
        except Exception as e:
            failures.append("completed=false error: %s" % str(e))

        # 5. Invalid completed value -> 400 (or at least not leaking other users' data)
        try:
            resp = client.get(url + '?completed=maybe')
            if resp.status_code == 400:
                checks_passed += 1
            else:
                # Accept 200 only if it doesn't leak other users' todos
                if resp.status_code == 200:
                    body = resp.json() if hasattr(resp, 'json') else json.loads(resp.content.decode())
                    if isinstance(body, dict) and 'results' in body:
                        body = body['results']
                    titles = set(item.get('title') for item in body)
                    if 'B1' not in titles:
                        checks_passed += 1
                    else:
                        failures.append("Invalid completed value leaked other users' todos")
                else:
                    failures.append("Invalid completed expected 400, got %s" % resp.status_code)
        except Exception as e:
            failures.append("Invalid completed error: %s" % str(e))

    finally:
        _cleanup(uname_a)
        _cleanup(uname_b)

    if checks_passed == total_checks:
        return {"result": "passed", "score": 10, "message": "All todo listing/filtering checks passed (%d/%d)." % (checks_passed, total_checks)}
    return {"result": "failed", "score": 0, "message": "Passed %d/%d checks. Failures: %s" % (checks_passed, total_checks, '; '.join(failures))}
