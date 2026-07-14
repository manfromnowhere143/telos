from django.conf import settings

if not settings.configured:
    settings.configure(
        SECRET_KEY="test",
        INSTALLED_APPS=[],
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
    )

import django

django.setup()

from django.template.engine import Engine

engine = Engine(
    autoescape=None,
    loaders=[("django.template.loaders.locmem.Loader", {"test.html": "{{ value }}"})],
)

print("RESULT=" + repr(engine.render_to_string("test.html", {"value": "<tag>"})))
