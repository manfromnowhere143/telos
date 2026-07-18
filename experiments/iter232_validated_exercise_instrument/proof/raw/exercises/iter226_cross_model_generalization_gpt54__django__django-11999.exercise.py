try:
    import django
    from django.conf import settings
    from django.db import models

    if not settings.configured:
        settings.configure(
            SECRET_KEY="fixture",
            INSTALLED_APPS=[],
            DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3"}},
        )
    django.setup()

    class Direct(models.Model):
        value = models.CharField(max_length=1, choices=[("a", "label")])

        def get_value_display(self):
            return "direct"

        class Meta:
            app_label = "fixture"

    class Abstract(models.Model):
        value = models.CharField(max_length=1, choices=[("a", "label")])

        def get_value_display(self):
            return "abstract"

        class Meta:
            abstract = True

    class Child(Abstract):
        class Meta:
            app_label = "fixture"

    class Mixin:
        def get_value_display(self):
            return "mixin"

    class Mixed(Mixin, models.Model):
        value = models.CharField(max_length=1, choices=[("a", "label")])

        class Meta:
            app_label = "fixture"

    observed = (
        Direct(value="a").get_value_display(),
        Child(value="a").get_value_display(),
        Mixed(value="a").get_value_display(),
    )
    print(f"RESULT={observed!r}")
except Exception as exc:
    print(f"RESULT={('ERROR', type(exc).__name__)!r}")
