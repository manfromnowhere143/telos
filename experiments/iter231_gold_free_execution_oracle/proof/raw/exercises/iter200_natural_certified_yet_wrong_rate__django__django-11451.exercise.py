import django
from django.conf import settings

try:
    if not settings.configured:
        settings.configure(
            SECRET_KEY="fixture",
            DEBUG=True,
            DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
            INSTALLED_APPS=["django.contrib.auth", "django.contrib.contenttypes"],
            MIDDLEWARE=[],
        )
    django.setup()

    from django.contrib.auth.backends import ModelBackend
    from django.core.management import call_command
    from django.db import connection
    from django.test.utils import CaptureQueriesContext

    call_command("migrate", verbosity=0, interactive=False)
    backend = ModelBackend()
    cases = [
        ("no_credentials", None, None),
        ("password_only", None, "secret"),
        ("username_only", "missing-user", None),
    ]
    observed = []
    for label, username, password in cases:
        with CaptureQueriesContext(connection) as queries:
            result = backend.authenticate(None, username=username, password=password)
        observed.append((label, result, len(queries)))
    print("RESULT=%r" % (observed,))
except Exception as exc:
    print("RESULT=%r" % (("ERROR", type(exc).__name__),))
