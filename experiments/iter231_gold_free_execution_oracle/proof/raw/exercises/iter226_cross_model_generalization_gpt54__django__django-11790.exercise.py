import django
from django.conf import settings

try:
    if not settings.configured:
        settings.configure(
            SECRET_KEY="test",
            INSTALLED_APPS=[
                "django.contrib.auth",
                "django.contrib.contenttypes",
            ],
            DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3"}},
        )
    django.setup()

    from django.contrib.auth import forms as auth_forms

    original_user_model = auth_forms.UserModel
    results = []
    for max_length in (None, 12):
        field = type("Field", (), {"max_length": max_length, "verbose_name": "username"})()
        fake_user_model = type(
            "User",
            (),
            {
                "USERNAME_FIELD": "username",
                "_meta": type(
                    "Meta",
                    (),
                    {"get_field": staticmethod(lambda name, field=field: field)},
                )(),
            },
        )
        auth_forms.UserModel = fake_user_model
        form = auth_forms.AuthenticationForm()
        results.append(
            (
                max_length,
                form.fields["username"].max_length,
                form.fields["username"].widget.attrs.get("maxlength"),
                "maxlength" in form["username"].as_widget(),
            )
        )
    auth_forms.UserModel = original_user_model
    print("RESULT=" + repr(results))
except Exception as exc:
    print("RESULT=" + repr(("ERROR", type(exc).__name__)))
