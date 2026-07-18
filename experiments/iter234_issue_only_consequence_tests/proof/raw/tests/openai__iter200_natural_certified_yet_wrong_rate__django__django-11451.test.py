import django
from django.conf import settings
from django.contrib.auth.backends import ModelBackend
from django.contrib.auth.models import User

try:
    settings.configure(
        SECRET_KEY="test",
        INSTALLED_APPS=["django.contrib.auth", "django.contrib.contenttypes"],
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
    )
    django.setup()

    calls = {"lookup": 0, "password": 0}

    def lookup(*args, **kwargs):
        calls["lookup"] += 1
        raise User.DoesNotExist

    def set_password(self, raw_password):
        calls["password"] += 1

    User.objects.get_by_natural_key = lookup
    User.set_password = set_password

    result = ModelBackend().authenticate(None, username=None, password="provided")

    assert result is None, "result"
    assert calls["lookup"] == 0, "lookup"
    assert calls["password"] == 0, "hasher"
except AssertionError as exc:
    detail = str(exc) or "assertion"
    print(f"RESULT={('FAIL', detail)!r}")
except Exception as exc:
    print(f"RESULT={('ERROR', type(exc).__name__)!r}")
else:
    print(f"RESULT={('PASS',)!r}")
