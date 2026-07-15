import importlib
import os
import sys
import tempfile

result = "PROP_PASS"
tmpdir = None

try:
    import django
    from django.conf import settings

    tmpdir = tempfile.TemporaryDirectory()
    root = tmpdir.name
    app_name = "prop_namespace_migrations_app"
    app_dir = os.path.join(root, app_name)
    migrations_dir = os.path.join(app_dir, "migrations")

    os.makedirs(migrations_dir)

    with open(os.path.join(app_dir, "__init__.py"), "w") as f:
        f.write("")

    with open(os.path.join(migrations_dir, "0001_initial.py"), "w") as f:
        f.write(
            "from django.db import migrations\n"
            "\n"
            "class Migration(migrations.Migration):\n"
            "    initial = True\n"
            "    dependencies = []\n"
            "    operations = []\n"
        )

    with open(os.path.join(migrations_dir, "0002_followup.py"), "w") as f:
        f.write(
            "from django.db import migrations\n"
            "\n"
            "class Migration(migrations.Migration):\n"
            "    dependencies = [('prop_namespace_migrations_app', '0001_initial')]\n"
            "    operations = []\n"
        )

    sys.path.insert(0, root)

    if not settings.configured:
        settings.configure(
            SECRET_KEY="property-test",
            INSTALLED_APPS=[app_name],
            DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
            USE_TZ=True,
        )
        django.setup()
    else:
        # A preconfigured process cannot reliably be made to discover this
        # temporary application, so don't treat setup limitations as failure.
        raise RuntimeError("settings already configured")

    migration_module_name = app_name + ".migrations"
    migration_module = importlib.import_module(migration_module_name)

    # Ensure the namespace package presents the condition described by the task:
    # discovery must rely on __path__, not on a __file__ attribute.
    if not hasattr(migration_module, "__path__"):
        raise AssertionError("migrations module is not a package")
    if hasattr(migration_module, "__file__"):
        delattr(migration_module, "__file__")

    from django.db import connection
    from django.db.migrations.loader import MigrationLoader

    loader = MigrationLoader(connection)
    first = (app_name, "0001_initial")
    second = (app_name, "0002_followup")
    plan = loader.graph.forwards_plan(second)

    if (
        first not in loader.disk_migrations
        or second not in loader.disk_migrations
        or app_name in loader.unmigrated_apps
        or first not in plan
        or second not in plan
        or plan.index(first) >= plan.index(second)
    ):
        result = "PROP_FAIL"

except RuntimeError as exc:
    if str(exc) != "settings already configured":
        result = "PROP_FAIL"
except Exception:
    result = "PROP_FAIL"
finally:
    if tmpdir is not None:
        tmpdir.cleanup()
    print(result)
