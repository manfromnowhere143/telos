from django.conf import settings

if not settings.configured:
    settings.configure(
        INSTALLED_APPS=[],
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
    )

import django
django.setup()

from django.core.files.uploadedfile import SimpleUploadedFile
from django.forms.widgets import FileInput

widget = FileInput()
upload = SimpleUploadedFile("upload.txt", b"x")
value = widget.value_from_datadict({}, {"attachment": upload}, "attachment")

print("RESULT=" + repr((value.name, widget.use_required_attribute("existing-file"))))
