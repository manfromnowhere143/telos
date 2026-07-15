import os
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
    django.setup()

    from django.template import Engine

    value = '<&>"\''
    with tempfile.TemporaryDirectory() as template_dir:
        template_name = "autoescape_probe.html"
        with open(os.path.join(template_dir, template_name), "w", encoding="utf-8") as template:
            template.write("value:" + "{{ value }}")

        engine = Engine(dirs=[template_dir], autoescape=False)
        rendered = engine.render_to_string(template_name, {"value": value})

    print("PROP_PASS" if rendered == "value:" + value else "PROP_FAIL")
except Exception:
    print("PROP_FAIL")
