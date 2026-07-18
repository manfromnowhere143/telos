import copy

try:
    import django
    from django.conf import settings
    from django import forms

    if not settings.configured:
        settings.configure(
            SECRET_KEY="test",
            INSTALLED_APPS=[],
            DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
        )
    if hasattr(django, "setup"):
        django.setup()

    class Probe:
        def __deepcopy__(self, memo):
            return Probe()

    probe = Probe()
    field = forms.CharField(error_messages={"required": probe})
    copied = copy.deepcopy(field)
    result = ("shared_message_value", copied.error_messages["required"] is probe)
    print(f"RESULT={result!r}")
except Exception as exc:
    print(f"RESULT={('ERROR', type(exc).__name__)!r}")
