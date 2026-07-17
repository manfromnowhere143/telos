from django.conf import settings

if not settings.configured:
    settings.configure(
        INSTALLED_APPS=[],
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
    )

import django

django.setup()

from django.db import models
from django.db.migrations.autodetector import MigrationAutodetector
from django.db.migrations.questioner import MigrationQuestioner
from django.db.migrations.state import ModelState, ProjectState

old_base = ModelState(
    "baseapp",
    "Base",
    [("clash", models.IntegerField())],
)
new_base = ModelState(
    "baseapp",
    "Base",
    [("clash", models.IntegerField())],
)
new_child = ModelState(
    "childapp",
    "Child",
    [("clash", models.IntegerField())],
    bases=("baseapp.base",),
)

from_state = ProjectState(models={("baseapp", "base"): old_base})
to_state = ProjectState(
    models={
        ("baseapp", "base"): new_base,
        ("childapp", "child"): new_child,
    }
)

detector = MigrationAutodetector(from_state, to_state, MigrationQuestioner())
detector.generate_created_models()

operation = detector.generated_operations["childapp"][0]
dependencies = getattr(operation, "_auto_deps", ())
result = tuple(sorted(dependencies, key=lambda item: (item[0], item[1], repr(item[2]), item[3])))

print("RESULT=" + repr(result))
