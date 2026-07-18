import copy

try:
    import django
    from django import forms
    from django.conf import settings

    if not settings.configured:
        settings.configure(
            SECRET_KEY="test",
            INSTALLED_APPS=[],
            DATABASES={
                "default": {
                    "ENGINE": "django.db.backends.sqlite3",
                    "NAME": ":memory:",
                }
            },
        )
    if hasattr(django, "setup"):
        django.setup()

    class ProbeField(forms.CharField):
        copies = 0

        def __copy__(self):
            type(self).copies += 1
            return self

    field = ProbeField()
    clone = copy.deepcopy(field)
    result = (ProbeField.copies, clone is field)
    print(f"RESULT={repr(result)}")
except Exception as exc:
    print(f"RESULT={repr(('ERROR', type(exc).__name__))}")
