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
        if apps.is_installed('todo') or True:
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
    # Fallback: search all models
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
    uname = 'u_%s' % uuid.uuid4().hex[:10]
    failures = []
    checks_passed = 0
    total_checks = 4

    try:
        # 1. Unauthenticated POST -> 401
        try:
            resp = client.post(url, data=json.dumps({'title': 'Test'}), content_type='application/json')
            if resp.status_code in (401, 403):
                checks_passed += 1
            else:
                failures.append("Unauthenticated POST expected 401/403, got %s" % resp.status_code)
        except Exception as e:
            failures.append("Unauthenticated POST error: %s" % str(e))

        # Create user and authenticate
        user = User.objects.create_user(username=uname, password='validpass123', email='t@example.com')
        client.force_login(user)

        # 2. Missing title -> 400
        try:
            resp = client.post(url, data=json.dumps({}), content_type='application/json')
            if resp.status_code == 400:
                checks_passed += 1
            else:
                failures.append("Missing title expected 400, got %s" % resp.status_code)
        except Exception as e:
            failures.append("Missing title request error: %s" % str(e))

        # 3. Empty title -> 400
        try:
            resp = client.post(url, data=json.dumps({'title': '   '}), content_type='application/json')
            if resp.status_code == 400:
                checks_passed += 1
            else:
                failures.append("Empty title expected 400, got %s" % resp.status_code)
        except Exception as e:
            failures.append("Empty title request error: %s" % str(e))

        # 4. Valid creation -> 201, owner set, title set
        try:
            resp = client.post(url, data=json.dumps({'title': 'My Task'}), content_type='application/json')
            if resp.status_code == 201:
                body = resp.json() if hasattr(resp, 'json') else json.loads(resp.content.decode())
                owner_val = body.get('owner')
                if isinstance(owner_val, dict):
                    owner_val = owner_val.get('username')
                if body.get('title') == 'My Task' and owner_val == uname:
                    checks_passed += 1
                else:
                    failures.append("Created todo missing expected title/owner: %s" % str(body))
            else:
                failures.append("Valid creation expected 201, got %s" % resp.status_code)
        except Exception as e:
            failures.append("Valid creation request error: %s" % str(e))

    finally:
        _cleanup(uname)

    if checks_passed == total_checks:
        return {"result": "passed", "score": 10, "message": "All todo creation checks passed (%d/%d)." % (checks_passed, total_checks)}
    return {"result": "failed", "score": 0, "message": "Passed %d/%d checks. Failures: %s" % (checks_passed, total_checks, '; '.join(failures))}
