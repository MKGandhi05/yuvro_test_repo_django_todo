import json
import uuid


def _get_client():
    from django.test import Client
    return Client()


def _cleanup(username):
    try:
        from django.contrib.auth.models import User
        User.objects.filter(username=username).delete()
    except Exception:
        pass


def evaluate():
    try:
        from django.contrib.auth.models import User
    except Exception as e:
        return {"result": "failed", "score": 0, "message": "Cannot import User model: %s" % str(e)}

    client = _get_client()
    url = '/api/register/'
    created_usernames = []
    failures = []
    checks_passed = 0
    total_checks = 6

    try:
        # 1. Missing all fields -> 400
        try:
            resp = client.post(url, data=json.dumps({}), content_type='application/json')
            if resp.status_code == 400:
                checks_passed += 1
            else:
                failures.append("Empty payload expected 400, got %s" % resp.status_code)
        except Exception as e:
            failures.append("Empty payload request error: %s" % str(e))

        # 2. Missing password -> 400
        uname = 'u_%s' % uuid.uuid4().hex[:10]
        try:
            resp = client.post(url, data=json.dumps({'username': uname, 'email': 'a@b.com'}), content_type='application/json')
            if resp.status_code == 400:
                checks_passed += 1
            else:
                failures.append("Missing password expected 400, got %s" % resp.status_code)
        except Exception as e:
            failures.append("Missing password request error: %s" % str(e))

        # 3. Short password -> 400
        uname2 = 'u_%s' % uuid.uuid4().hex[:10]
        try:
            resp = client.post(url, data=json.dumps({'username': uname2, 'password': 'short', 'email': 'a@b.com'}), content_type='application/json')
            if resp.status_code == 400:
                checks_passed += 1
            else:
                failures.append("Short password expected 400, got %s" % resp.status_code)
        except Exception as e:
            failures.append("Short password request error: %s" % str(e))

        # 4. Invalid email -> 400
        uname3 = 'u_%s' % uuid.uuid4().hex[:10]
        try:
            resp = client.post(url, data=json.dumps({'username': uname3, 'password': 'validpass123', 'email': 'not-an-email'}), content_type='application/json')
            if resp.status_code == 400:
                checks_passed += 1
            else:
                failures.append("Invalid email expected 400, got %s" % resp.status_code)
        except Exception as e:
            failures.append("Invalid email request error: %s" % str(e))

        # 5. Successful registration -> 201, no password in response
        uname4 = 'u_%s' % uuid.uuid4().hex[:10]
        created_usernames.append(uname4)
        try:
            resp = client.post(url, data=json.dumps({'username': uname4, 'password': 'validpass123', 'email': 'valid@example.com'}), content_type='application/json')
            if resp.status_code == 201:
                body = resp.json() if hasattr(resp, 'json') else json.loads(resp.content.decode())
                if 'password' not in body and body.get('username') == uname4:
                    checks_passed += 1
                else:
                    failures.append("Success response missing expected fields or contains password: %s" % str(body))
            else:
                failures.append("Valid registration expected 201, got %s" % resp.status_code)
        except Exception as e:
            failures.append("Valid registration request error: %s" % str(e))

        # 6. Duplicate username -> 400
        try:
            resp = client.post(url, data=json.dumps({'username': uname4, 'password': 'validpass123', 'email': 'valid2@example.com'}), content_type='application/json')
            if resp.status_code == 400:
                checks_passed += 1
            else:
                failures.append("Duplicate username expected 400, got %s" % resp.status_code)
        except Exception as e:
            failures.append("Duplicate username request error: %s" % str(e))

    finally:
        for u in created_usernames:
            _cleanup(u)

    if checks_passed == total_checks:
        return {"result": "passed", "score": 10, "message": "All registration validation checks passed (%d/%d)." % (checks_passed, total_checks)}
    score = int(round(10.0 * checks_passed / total_checks))
    return {"result": "failed", "score": 0, "message": "Passed %d/%d checks. Failures: %s" % (checks_passed, total_checks, '; '.join(failures))}
