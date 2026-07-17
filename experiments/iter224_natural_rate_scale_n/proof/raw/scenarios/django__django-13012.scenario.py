from django.conf import settings

if not settings.configured:
    settings.configure(
        INSTALLED_APPS=[],
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
    )

import django

django.setup()

from django.db.models.expressions import Expression, OrderBy


class Probe(Expression):
    def get_group_by_cols(self, alias=None):
        return [("alias", alias)]


probe = Probe()
ordering = OrderBy(Probe())
ordering.set_source_expressions([probe])
result = ordering.get_group_by_cols(alias="probe_alias")
print("RESULT=" + repr(result))
