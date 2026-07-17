from django.conf import settings

settings.configure(
    INSTALLED_APPS=[],
    DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
)

import django

django.setup()

from django.db.models.sql.query import Query


class Marker:
    def resolve_expression(self, query, reuse=None, allow_joins=True):
        return "resolved"


result = Query(None).resolve_lookup_value(
    [(Marker(),)],
    can_reuse=None,
    allow_joins=True,
    simple_col=False,
)

print("RESULT=" + repr(result))
