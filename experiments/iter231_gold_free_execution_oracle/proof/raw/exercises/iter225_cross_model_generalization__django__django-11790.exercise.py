try:
    from django.conf import settings
    from django.apps import apps

    if not settings.configured:
        settings.configure(
            SECRET_KEY="test",
            INSTALLED_APPS=[
                "django.contrib.auth",
                "django.contrib.contenttypes",
            ],
        )
    if not apps.ready:
        import django
        django.setup()

    from django.contrib.auth.forms import AuthenticationForm

    form = AuthenticationForm()
    field = form.fields["username"]
    rendered = field.widget.render("username", "")
    print("RESULT=%r" % (
        field.max_length,
        field.widget.attrs.get("maxlength"),
        "maxlength" in rendered,
    ))
except Exception as exc:
    print("RESULT=%r" % ("ERROR", type(exc).__name__))
