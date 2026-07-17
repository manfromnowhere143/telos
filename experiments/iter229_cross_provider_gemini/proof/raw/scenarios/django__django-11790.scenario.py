from django.conf import settings

settings.configure(
    SECRET_KEY="test",
    INSTALLED_APPS=[
        "django.contrib.auth",
        "django.contrib.contenttypes",
    ],
    DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
    USE_I18N=False,
)

import django

django.setup()

import django.contrib.auth.forms as auth_forms


class MetadataField:
    def __init__(self, max_length):
        self.max_length = max_length
        self.verbose_name = "login name"


class Metadata:
    def __init__(self):
        self.calls = 0

    def get_field(self, name):
        self.calls += 1
        return MetadataField(17 if self.calls == 1 else 29)


metadata = Metadata()


class UserModel:
    USERNAME_FIELD = "login"
    _meta = metadata


auth_forms.UserModel = UserModel
form = auth_forms.AuthenticationForm()

print("RESULT=" + repr((metadata.calls, form.username_field.max_length, form.fields["username"].widget.attrs["maxlength"])))
