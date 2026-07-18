try:
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure(
            DEBUG=True,
            DATABASES={},
            INSTALLED_APPS=[
                "django.contrib.contenttypes",
                "django.contrib.auth",
            ],
            AUTH_USER_MODEL="auth.User",
            USE_TZ=True,
        )
    django.setup()

    from django.contrib.auth.forms import AuthenticationForm

    form = AuthenticationForm()
    username_field = form.fields["username"]
    widget_attrs = username_field.widget.attrs
    rendered = str(form["username"])

    detail = None
    # The widget should carry maxlength in its attrs
    if "maxlength" not in widget_attrs:
        detail = "maxlength missing from widget attrs"
    elif str(widget_attrs["maxlength"]) != "254":
        detail = f"widget maxlength={widget_attrs['maxlength']!r}"
    elif 'maxlength="254"' not in rendered:
        detail = f"maxlength not in rendered HTML: {rendered!r}"

    if detail is None:
        print(f"RESULT={('PASS',)!r}")
    else:
        print(f"RESULT={('FAIL', detail)!r}")
except Exception as exc:
    print(f"RESULT={('ERROR', type(exc).__name__)!r}")
