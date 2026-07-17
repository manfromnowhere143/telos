from django.conf import settings

if not settings.configured:
    settings.configure(
        SECRET_KEY="test",
        INSTALLED_APPS=[
            "django.contrib.auth",
            "django.contrib.contenttypes",
        ],
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
        USE_TZ=True,
    )

import django
django.setup()

from django import forms
from django.contrib.auth.forms import AuthenticationForm


class ObservableMaxLengthField(forms.Field):
    widget = forms.TextInput

    def __init__(self, *args, **kwargs):
        self._stored_max_length = None
        super().__init__(*args, **kwargs)

    @property
    def max_length(self):
        if self._stored_max_length is None:
            return None
        return self._stored_max_length + 1

    @max_length.setter
    def max_length(self, value):
        self._stored_max_length = value


class TestAuthenticationForm(AuthenticationForm):
    username = ObservableMaxLengthField()


form = TestAuthenticationForm()
print("RESULT=" + repr(form.fields["username"].widget.attrs["maxlength"]))
