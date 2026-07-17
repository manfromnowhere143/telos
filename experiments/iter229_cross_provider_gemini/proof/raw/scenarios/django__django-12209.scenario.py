from django.conf import settings

settings.configure(
    DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
    INSTALLED_APPS=[],
    SECRET_KEY="test",
)

import django

django.setup()

from django.db import models

events = []


class Probe(models.Model):
    id = models.IntegerField(primary_key=True, default=1)

    class Meta:
        app_label = "probe"

    def _do_update(self, base_qs, using, pk_val, values, update_fields, forced_update):
        events.append("update")
        return True

    def _do_insert(self, manager, using, fields, returning_fields, raw):
        events.append("insert")
        return []


Probe()._save_table(
    raw=True,
    cls=Probe,
    force_insert=False,
    force_update=False,
    using="default",
    update_fields=None,
)

print("RESULT=" + repr(events))
