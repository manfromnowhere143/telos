import os
import tempfile

import django
from django.conf import settings
from django.conf.global_settings import gettext_noop
from django.core.files.base import ContentFile
from django.core.files.storage import FileSystemStorage

settings.configure(
    INSTALLED_APPS=[],
    DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
)
django.setup()

gettext_noop("file upload permission")

with tempfile.TemporaryDirectory() as directory:
    storage = FileSystemStorage(location=directory)
    name = storage.save("uploaded.txt", ContentFile(b"x"))
    mode = os.stat(os.path.join(directory, name)).st_mode & 0o777

print(f"RESULT={oct(mode)!r}")
