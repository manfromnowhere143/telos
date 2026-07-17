import copy

from django.conf import settings

if not settings.configured:
    settings.configure(
        SECRET_KEY="x",
        INSTALLED_APPS=[],
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
        USE_I18N=False,
    )

import django
django.setup()

from django import forms
from django.forms.widgets import Widget


class BackrefWidget(Widget):
    def __deepcopy__(self, memo):
        result = copy.copy(self)
        memo[id(self)] = result
        result.owner = copy.deepcopy(self.owner, memo)
        return result


field = forms.Field()
field.widget = BackrefWidget()
field.widget.owner = field

cloned = copy.deepcopy(field)
print("RESULT=" + repr(cloned.widget.owner is cloned))
