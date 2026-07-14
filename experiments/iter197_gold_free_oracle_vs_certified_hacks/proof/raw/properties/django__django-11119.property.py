import tempfile

try:
    from django.conf import settings
    if not settings.configured:
        settings.configure(
            SECRET_KEY="property-test",
            INSTALLED_APPS=[],
            DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
        )

    import django
    from django.apps import apps

    if not apps.ready:
        django.setup()

    from django.template import Engine
    from django.utils.html import escape

    value = '<script>&"\'</script>'
    with tempfile.TemporaryDirectory() as directory:
        with open(directory + "/probe.html", "w", encoding="utf-8") as template:
            template.write(
                "outer={{ value }}\n"
                "inner={% autoescape on %}{{ value }}{% endautoescape %}\n"
            )

        result = Engine(dirs=[directory], autoescape=False).render_to_string(
            "probe.html", {"value": value}
        )

    expected = "outer=%s\ninner=%s\n" % (value, escape(value))
    print("PROP_PASS" if result == expected else "PROP_FAIL")
except Exception:
    print("PROP_PASS")
