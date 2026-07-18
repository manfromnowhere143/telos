import django
from django import forms
from django.conf import settings
from django.db import models

try:
    if not settings.configured:
        settings.configure(
            SECRET_KEY="test",
            INSTALLED_APPS=[],
            USE_I18N=False,
        )
    django.setup()

    class Document(models.Model):
        attachment = models.FileField()

        class Meta:
            app_label = "consequence_test"

    class DocumentForm(forms.ModelForm):
        class Meta:
            model = Document
            fields = ["attachment"]
            widgets = {"attachment": forms.FileInput}

    document = Document(attachment="already-saved.txt")
    form = DocumentForm(instance=document)
    html = form["attachment"].as_widget()

    assert form.fields["attachment"].required, "field not required"
    assert document.attachment.name == "already-saved.txt", "missing initial"
    assert 'type="file"' in html, "not file input"
    assert "required" not in html, "required rendered"
    print(f"RESULT={('PASS',)!r}")
except AssertionError as exc:
    print(f"RESULT={('FAIL', str(exc))!r}")
except Exception as exc:
    print(f"RESULT={('ERROR', type(exc).__name__)!r}")
