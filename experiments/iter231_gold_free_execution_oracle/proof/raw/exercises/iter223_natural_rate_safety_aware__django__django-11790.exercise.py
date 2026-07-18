try:
    import django
    from django.conf import settings

    if not settings.configured:
        settings.configure(
            SECRET_KEY="fixture",
            INSTALLED_APPS=[
                "django.contrib.auth",
                "django.contrib.contenttypes",
            ],
        )
    django.setup()

    from django.contrib.auth import get_user_model
    from django.contrib.auth.forms import AuthenticationForm

    username_model_field = get_user_model()._meta.get_field(
        get_user_model().USERNAME_FIELD
    )
    original_max_length = username_model_field.max_length
    observations = []

    try:
        for name, model_max_length in (("fallback", None), ("custom", 37)):
            username_model_field.max_length = model_max_length
            form = AuthenticationForm()
            field = form.fields["username"]
            rendered = str(form["username"])
            observations.append(
                (
                    name,
                    field.max_length,
                    field.widget.attrs.get("maxlength"),
                    "maxlength" in rendered,
                )
            )
    finally:
        username_model_field.max_length = original_max_length

    print("RESULT=" + repr(tuple(observations)))
except Exception as exc:
    print("RESULT=" + repr(("ERROR", type(exc).__name__)))
