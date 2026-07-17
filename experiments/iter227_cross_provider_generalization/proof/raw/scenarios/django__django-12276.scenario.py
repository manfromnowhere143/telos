from django.conf import settings

if not settings.configured:
    settings.configure(
        SECRET_KEY="test",
        INSTALLED_APPS=[],
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
    )

import django
django.setup()

from django import forms


class UploadForm(forms.Form):
    upload = forms.FileField(initial="saved.txt")


form = UploadForm(data={}, files={})
valid = form.is_valid()
html = form["upload"].as_widget()

print("RESULT=" + repr((valid, " required" in html)))
