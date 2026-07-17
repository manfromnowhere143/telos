from django.conf import settings

if not settings.configured:
    settings.configure(
        SECRET_KEY="test",
        INSTALLED_APPS=[
            "django.contrib.auth",
            "django.contrib.contenttypes",
        ],
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
    )

import django

django.setup()

from django.contrib.auth import forms


class Field:
    def __init__(self, max_length, verbose_name):
        self.max_length = max_length
        self.verbose_name = verbose_name


class Meta:
    def __init__(self):
        self.calls = 0

    def get_field(self, name):
        self.calls += 1
        return Field(11 if self.calls == 1 else 22, "account name")


class UserModel:
    USERNAME_FIELD = "username"
    _meta = Meta()


forms.get_user_model = lambda: UserModel

form = forms.AuthenticationForm()
print(
    "RESULT=%r"
    % (
        UserModel._meta.calls,
        form.username_field.max_length,
        form.fields["username"].max_length,
        form.fields["username"].widget.attrs.get("maxlength"),
    )
)
