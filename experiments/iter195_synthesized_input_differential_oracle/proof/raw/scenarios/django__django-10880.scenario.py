from django.conf import settings

settings.configure(
    DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
    INSTALLED_APPS=[],
)
import django
django.setup()

from django.db import connection
from django.db.models import Case, Count, Value, When
from django.db.models.sql.query import Query

compiler = Query(None).get_compiler(connection=connection)
expression = Count(
    Case(When(Value(True), then=Value(1)), default=Value(0)),
    distinct=1,
)
print("RESULT=" + repr(expression.as_sql(compiler, connection)))
