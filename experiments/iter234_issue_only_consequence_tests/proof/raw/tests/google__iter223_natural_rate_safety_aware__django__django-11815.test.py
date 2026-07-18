import django
from django.conf import settings
from enum import Enum

try:
    if not settings.configured:
        settings.configure(INSTALLED_APPS=[])
        django.setup()

    from django.utils.translation import gettext_lazy as _
    from django.db.migrations.writer import MigrationWriter

    class Status(Enum):
        GOOD = _('Good')
        BAD = _('Bad')

    # Serialize the Enum member with a lazy translation value
    serialized_string, imports = MigrationWriter.serialize(Status.GOOD)

    # The issue expects the Enum to be serialized using its name (e.g. Status['GOOD'])
    # instead of its value (e.g. Status('Good')), to avoid translation-related ValueErrors
    # when the migration is applied in a different language context.
    if "['GOOD']" in serialized_string or ".GOOD" in serialized_string:
        print(f"RESULT={('PASS',)!r}")
    else:
        print(f"RESULT={('FAIL', f'Serialized string uses value instead of name: {serialized_string}')!r}")

except Exception as e:
    print(f"RESULT={('ERROR', type(e).__name__)!r}")
