import re

try:
    import django
    from django.conf import settings

    if not settings.configured:
        settings.configure(
            SECRET_KEY="test-key",
            INSTALLED_APPS=[
                "django.contrib.auth",
                "django.contrib.contenttypes",
            ],
            USE_I18N=False,
        )
    django.setup()

    from django.contrib.auth.forms import AuthenticationForm

    form = AuthenticationForm()
    field = form.fields["username"]
    rendered = form["username"].as_widget()
    match = re.search(r'\bmaxlength="(\d+)"', rendered)

    assert match is not None, "missing maxlength"
    assert int(match.group(1)) == field.max_length, "wrong maxlength"

    print(f"RESULT={('PASS',)!r}")
except AssertionError as exc:
    detail = str(exc) or "assertion failed"
    print(f"RESULT={('FAIL', detail)!r}")
except Exception as exc:
    print(f"RESULT={('ERROR', type(exc).__name__)!r}")
