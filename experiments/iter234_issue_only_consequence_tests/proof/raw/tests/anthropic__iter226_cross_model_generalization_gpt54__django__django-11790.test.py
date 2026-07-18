try:
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure(
            INSTALLED_APPS=[
                "django.contrib.auth",
                "django.contrib.contenttypes",
            ],
            DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
            AUTH_USER_MODEL="auth.User",
        )
    django.setup()

    from django.contrib.auth.forms import AuthenticationForm

    form = AuthenticationForm()
    widget_attrs = form.fields["username"].widget.attrs
    maxlength = widget_attrs.get("maxlength")
    assert maxlength == 254, f"widget maxlength={maxlength!r}"

    rendered = str(form["username"])
    assert 'maxlength="254"' in rendered, f"rendered missing maxlength: {rendered!r}"

    print(f"RESULT={('PASS',)!r}")
except AssertionError as exc:
    print(f"RESULT={('FAIL', str(exc))!r}")
except Exception as exc:
    print(f"RESULT={('ERROR', type(exc).__name__)!r}")
