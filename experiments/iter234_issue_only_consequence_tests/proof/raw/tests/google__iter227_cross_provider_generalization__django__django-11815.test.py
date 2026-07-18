import django
from django.conf import settings
from enum import Enum
from django.utils.translation import gettext_lazy as _

if not settings.configured:
    settings.configure(INSTALLED_APPS=[])
django.setup()

from django.db.migrations.writer import MigrationWriter

class Status(Enum):
    GOOD = _('Good')
    BAD = _('Bad')

    def __str__(self):
        return self.name

def main():
    try:
        # Serializing the enum member should use its name (stable) 
        # instead of its value (which could change due to translation).
        serialized, _ = MigrationWriter.serialize(Status.GOOD)
        
        # Valid outputs should reference the enum member by name
        # e.g. __main__.Status['GOOD'] or __main__.Status.GOOD
        if "['GOOD']" in serialized or ".GOOD" in serialized:
            print(f"RESULT={('PASS',)!r}")
        else:
            print(f"RESULT={('FAIL', f'Serialized improperly: {serialized}')!r}")
            
    except Exception as e:
        print(f"RESULT={('ERROR', type(e).__name__)!r}")

if __name__ == "__main__":
    main()
