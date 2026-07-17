from django.conf import settings

if not settings.configured:
    settings.configure(
        SECRET_KEY="test",
        INSTALLED_APPS=[],
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
    )

import django
django.setup()

from django.template.base import Parser
from django.template.exceptions import TemplateSyntaxError
from django.template.library import parse_bits

try:
    args, kwargs = parse_bits(
        Parser([]),
        ["unexpected=1"],
        [],
        None,
        None,
        [],
        [],
        [],
        False,
        "probe",
    )
    result = ("returned", len(args), tuple(sorted(kwargs)))
except TemplateSyntaxError as exc:
    result = ("error", str(exc))

print("RESULT=" + repr(result))
