try:
    import django
    from django.apps import apps
    from django.conf import settings

    if not settings.configured:
        settings.configure(
            SECRET_KEY="test",
            INSTALLED_APPS=[
                "django.contrib.auth",
                "django.contrib.contenttypes",
            ],
            DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
            USE_I18N=False,
        )
    if not apps.ready:
        django.setup()

    from django.contrib.auth.forms import AuthenticationForm
    from django.contrib.auth.models import User

    class UsernameFieldSwitcher:
        def __init__(self):
            self.calls = 0

        def __get__(self, instance, owner):
            self.calls += 1
            return "username" if self.calls == 1 else "email"

    User.USERNAME_FIELD = UsernameFieldSwitcher()
    form = AuthenticationForm()
    result = (
        form.fields["username"].max_length,
        form.fields["username"].widget.attrs["maxlength"],
    )
except Exception as exc:
    result = ("ERROR", type(exc).__name__)

print(f"RESULT={result!r}")
