import copy

from django.conf import settings

if not settings.configured:
    settings.configure(
        SECRET_KEY="test",
        INSTALLED_APPS=[],
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
        USE_I18N=False,
    )

import django

django.setup()

from django.forms.fields import Field
from django.forms.widgets import Widget


class ProbeWidget(Widget):
    def __deepcopy__(self, memo):
        duplicate = type(self)()
        duplicate.seen_field = memo[id(self.owner)]
        return duplicate


widget = ProbeWidget()
field = Field(widget=widget)
widget.owner = field

cloned = copy.deepcopy(field)
print("RESULT=" + repr(cloned.widget.seen_field is cloned))
