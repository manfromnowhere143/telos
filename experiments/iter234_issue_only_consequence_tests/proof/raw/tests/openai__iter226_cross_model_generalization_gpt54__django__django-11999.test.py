try:
    import django
    from django.conf import settings
    from django.db import models

    if not settings.configured:
        settings.configure(
            INSTALLED_APPS=[],
            DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
        )
    django.setup()

    class DisplayMixin:
        def get_foo_bar_display(self):
            return "something inherited"

    class FooBar(DisplayMixin, models.Model):
        foo_bar = models.CharField(
            max_length=1,
            choices=[("1", "foo"), ("2", "bar")],
        )

        class Meta:
            app_label = "display_override_fixture"

    assert FooBar(foo_bar="1").get_foo_bar_display() == "something inherited"
    assert FooBar(foo_bar="2").get_foo_bar_display() == "something inherited"
except AssertionError:
    print(f"RESULT={('FAIL', 'inherited display override')!r}")
except Exception as exc:
    print(f"RESULT={('ERROR', type(exc).__name__)!r}")
else:
    print(f"RESULT={('PASS',)!r}")
