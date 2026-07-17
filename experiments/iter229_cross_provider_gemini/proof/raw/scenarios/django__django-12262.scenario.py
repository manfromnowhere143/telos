from django.conf import settings

if not settings.configured:
    settings.configure(
        SECRET_KEY="x",
        INSTALLED_APPS=[],
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
    )

import django

django.setup()

from django.template.base import Parser
from django.template.library import parse_bits

try:
    args, kwargs = parse_bits(
        Parser([]),
        ["optional=1"],
        [],
        None,
        None,
        [],
        ["optional"],
        {"optional": None},
        False,
        "f",
    )
    result = ("ok", tuple(args), tuple(sorted(kwargs)))
except Exception as exc:
    result = ("error", type(exc).__name__, str(exc))

print("RESULT=" + repr(result))
