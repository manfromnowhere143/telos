import django
from django.conf import settings

try:
    if not settings.configured:
        settings.configure(
            SECRET_KEY="test-secret",
            INSTALLED_APPS=[
                "django.contrib.auth",
                "django.contrib.contenttypes",
            ],
            DATABASES={
                "default": {
                    "ENGINE": "django.db.backends.sqlite3",
                    "NAME": ":memory:",
                }
            },
            USE_I18N=False,
        )
    django.setup()

    from django.contrib.auth.forms import AuthenticationForm

    form = AuthenticationForm()
    expected = str(form.fields["username"].max_length)
    html = form["username"].as_widget()
    assert 'maxlength="' + expected + '"' in html
    print(f"RESULT={('PASS',)!r}")
except AssertionError:
    detail = "username maxlength not rendered"
    print(f"RESULT={('FAIL', detail)!r}")
except Exception as exc:
    print(f"RESULT={('ERROR', type(exc).__name__)!r}")
