from django.conf import settings

if not settings.configured:
    settings.configure(
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
        INSTALLED_APPS=[],
        SECRET_KEY="detector",
    )

import django

django.setup()

from django.db import connection, models
from django.db.models.sql.constants import ROW_COUNT
from django.db.models.sql.subqueries import DeleteQuery


class Probe(models.Model):
    class Meta:
        app_label = "detector"
        db_table = "detector_probe"


with connection.schema_editor() as editor:
    editor.create_model(Probe)

query = DeleteQuery(Probe)
result = query.get_compiler("default").execute_sql(ROW_COUNT)
aliases = tuple(sorted((alias, query.alias_refcount[alias]) for alias in query.alias_map))
print("RESULT=" + repr((result, aliases)))
