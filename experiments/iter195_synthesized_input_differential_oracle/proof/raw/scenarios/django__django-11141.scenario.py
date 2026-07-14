import os
import sys
import tempfile

from django.conf import settings

root = tempfile.mkdtemp()
app_name = "probe_empty_migrations_app"
app_dir = os.path.join(root, app_name)
os.makedirs(os.path.join(app_dir, "migrations"))

with open(os.path.join(app_dir, "__init__.py"), "w", encoding="utf-8") as f:
    f.write("")

sys.path.insert(0, root)

settings.configure(
    SECRET_KEY="x",
    INSTALLED_APPS=[app_name],
    DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
)

import django
from django.db.migrations.loader import MigrationLoader

django.setup()

loader = MigrationLoader(None, load=False, ignore_no_migrations=True)
loader.load_disk()

print("RESULT=%r" % ((app_name in loader.migrated_apps, app_name in loader.unmigrated_apps),))
