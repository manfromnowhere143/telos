try:
    import django
    from django.conf import settings
    from django import forms
    from django.core.files.base import ContentFile

    if not settings.configured:
        settings.configure(
            SECRET_KEY="test",
            INSTALLED_APPS=[],
            USE_I18N=False,
        )
    django.setup()

    class EditForm(forms.Form):
        title = forms.CharField()
        attachment = forms.FileField(required=True, widget=forms.FileInput)

    existing = ContentFile(b"existing file", name="existing.txt")
    editing = EditForm(
        data={"title": "updated"},
        initial={"attachment": existing},
    )
    html = str(editing["attachment"])

    assert editing.is_valid()
    assert 'type="file"' in html
    assert "required" not in html

    new_form = EditForm()
    assert "required" in str(new_form["attachment"])

    print(f"RESULT={('PASS',)!r}")
except AssertionError:
    print(f"RESULT={('FAIL', 'assertion')!r}")
except Exception as exc:
    print(f"RESULT={('ERROR', type(exc).__name__)!r}")
