import re

try:
    import django
    from django.conf import settings

    if not settings.configured:
        settings.configure(
            SECRET_KEY="test",
            INSTALLED_APPS=[
                "django.contrib.auth",
                "django.contrib.contenttypes",
            ],
            USE_I18N=False,
        )
    django.setup()

    from django.contrib.auth.forms import AuthenticationForm

    form = AuthenticationForm(None)
    expected = form.fields["username"].max_length
    rendered = form.as_p()
    input_match = re.search(r'<input\b[^>]*\bname="username"[^>]*>', rendered)
    assert input_match is not None, "username input missing"

    maxlength_match = re.search(
        r'\bmaxlength="(\d+)"', input_match.group(0)
    )
    assert maxlength_match is not None, "maxlength missing"
    assert int(maxlength_match.group(1)) == expected, "wrong maxlength"
except AssertionError as exc:
    print(f"RESULT={('FAIL', str(exc) or 'assertion')!r}")
except Exception as exc:
    print(f"RESULT={('ERROR', type(exc).__name__)!r}")
else:
    print(f"RESULT={('PASS',)!r}")
