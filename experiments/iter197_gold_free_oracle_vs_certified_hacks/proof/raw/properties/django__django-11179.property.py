import uuid

from django.conf import settings

if not settings.configured:
    settings.configure(
        SECRET_KEY="delete-property",
        INSTALLED_APPS=[],
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
        DEFAULT_AUTO_FIELD="django.db.models.AutoField",
    )

import django

django.setup()

from django.db import connection, models
from django.db.models.deletion import Collector


class NoDependencyUUIDModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    class Meta:
        app_label = "delete_property_oracle"
        db_table = "delete_property_oracle_uuid_model"


try:
    with connection.schema_editor() as schema_editor:
        schema_editor.create_model(NoDependencyUUIDModel)

    instance = NoDependencyUUIDModel.objects.create()
    original_pk = instance.pk
    fast_deletable = Collector(using="default").can_fast_delete(instance)

    instance.delete()

    correct = (
        fast_deletable
        and instance.pk is None
        and not NoDependencyUUIDModel.objects.filter(pk=original_pk).exists()
    )
    print("PROP_PASS" if correct else "PROP_FAIL")
except Exception:
    print("PROP_FAIL")
