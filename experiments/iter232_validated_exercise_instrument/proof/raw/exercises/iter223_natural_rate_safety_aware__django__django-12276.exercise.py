from django.core.files.uploadedfile import SimpleUploadedFile
from django.forms.widgets import ClearableFileInput, FileInput

try:
    initial_file = SimpleUploadedFile("existing.txt", b"data")
    result = (
        ("FileInput", FileInput().use_required_attribute(None),
         FileInput().use_required_attribute(initial_file)),
        ("ClearableFileInput", ClearableFileInput().use_required_attribute(None),
         ClearableFileInput().use_required_attribute(initial_file)),
    )
    print("RESULT=" + repr(result))
except Exception as exc:
    print("RESULT=" + repr(("ERROR", type(exc).__name__)))
