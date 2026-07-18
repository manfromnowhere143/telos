import django
from django.conf import settings

try:
    if not settings.configured:
        settings.configure(
            DEBUG=True,
            DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
            INSTALLED_APPS=[
                "django.contrib.auth",
                "django.contrib.contenttypes",
            ],
            USE_TZ=True,
        )
    django.setup()

    from django.contrib.auth.forms import AuthenticationForm

    form = AuthenticationForm()
    username_field = form.fields["username"]

    # maxlength should be set on the widget attrs
    widget_attrs = username_field.widget.attrs
    maxlength = widget_attrs.get("maxlength")

    assert maxlength is not None, "maxlength missing from widget attrs"
    assert int(maxlength) == 254, f"maxlength={maxlength}"

    # And it should actually render into the HTML
    rendered = str(form["username"])
    assert 'maxlength="254"' in rendered, f"maxlength not in rendered HTML: {rendered}"

    print(f"RESULT={('PASS',)!r}")
except AssertionError as exc:
    print(f"RESULT={('FAIL', str(exc))!r}")
except Exception as exc:
    print(f"RESULT={('ERROR', type(exc).__name__)!r}")
