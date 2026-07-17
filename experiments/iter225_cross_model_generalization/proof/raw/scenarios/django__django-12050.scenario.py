from django.conf import settings

if not settings.configured:
    settings.configure(
        SECRET_KEY="test",
        INSTALLED_APPS=[],
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
    )

import django

django.setup()

from django.db.models.sql.query import Query


class Probe:
    def resolve_expression(self, query, reuse=None, allow_joins=True, simple_col=False):
        return "resolved"

    def __repr__(self):
        return "Probe()"


result = Query(None).resolve_lookup_value([[Probe()]], None, True, False)
print("RESULT=" + repr(result))
