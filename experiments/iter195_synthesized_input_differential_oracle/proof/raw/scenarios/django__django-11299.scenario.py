from django.conf import settings

settings.configure(
    DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
    INSTALLED_APPS=[],
    SECRET_KEY="test",
)

import django

django.setup()

from django.db import connection, models
from django.db.models import Q
from django.db.models.sql.query import Query


class Probe(models.Model):
    field_1 = models.IntegerField()

    class Meta:
        app_label = "probe"
        db_table = "probe_table"


condition = Q(~Q(Q(field_1=1)))
query = Query(Probe, alias_cols=False)
where = query.build_where(condition)
compiler = query.get_compiler(connection=connection)
sql, params = where.as_sql(compiler, connection)

print("RESULT=" + repr(sql))
