from django.conf import settings

settings.configure(
    SECRET_KEY="test",
    INSTALLED_APPS=[],
)

import django

django.setup()

from django.forms.widgets import FileInput

result = FileInput().value_from_datadict({}, {"upload": "payload"}, "upload")
print("RESULT=" + repr(result))
