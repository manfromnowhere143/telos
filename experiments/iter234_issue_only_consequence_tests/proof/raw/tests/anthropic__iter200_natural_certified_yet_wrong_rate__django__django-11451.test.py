try:
    import django
    from django.conf import settings
    settings.configure(
        DEBUG=True,
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
        INSTALLED_APPS=["django.contrib.auth", "django.contrib.contenttypes"],
        AUTH_PASSWORD_VALIDATORS=[],
        PASSWORD_HASHERS=["django.contrib.auth.hashers.MD5PasswordHasher"],
    )
    django.setup()
    from django.db import connection
    from django.test.utils import CaptureQueriesContext
    from django.contrib.auth.backends import ModelBackend

    with connection.schema_editor() as editor:
        from django.contrib.auth.models import User
        editor.create_model(User)

    backend = ModelBackend()

    # Case 1: username is None -> no query
    with CaptureQueriesContext(connection) as ctx:
        result = backend.authenticate(None, username=None, password="secret")
    n_none_user = len(ctx.captured_queries)
    assert result is None, "expected None result"
    assert n_none_user == 0, f"username=None made {n_none_user} queries"

    # Case 2: password is None -> no query
    with CaptureQueriesContext(connection) as ctx:
        result = backend.authenticate(None, username="alice", password=None)
    n_none_pw = len(ctx.captured_queries)
    assert result is None, "expected None result for password None"
    assert n_none_pw == 0, f"password=None made {n_none_pw} queries"

    # Case 3: sanity - both provided but user doesn't exist -> should query
    with CaptureQueriesContext(connection) as ctx:
        result = backend.authenticate(None, username="bob", password="secret")
    n_real = len(ctx.captured_queries)
    assert result is None, "nonexistent user should authenticate to None"
    assert n_real >= 1, f"valid credentials should query, got {n_real}"

    print(f"RESULT={('PASS',)!r}")
except AssertionError as exc:
    print(f"RESULT={('FAIL', str(exc))!r}")
except Exception as exc:
    print(f"RESULT={('ERROR', type(exc).__name__)!r}")
