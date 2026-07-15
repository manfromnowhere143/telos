from django.conf import settings

if not settings.configured:
    settings.configure(
        SECRET_KEY="x",
        INSTALLED_APPS=[],
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
    )

import django

django.setup()

from django.urls.resolvers import RegexPattern


class ProbeMatch:
    def __init__(self):
        self.calls = 0

    def groupdict(self):
        return {}

    def groups(self):
        self.calls += 1
        return (f"groups-call-{self.calls}",)

    def end(self):
        return 0


class ProbeRegex:
    def __init__(self):
        self.match = ProbeMatch()

    def search(self, path):
        return self.match


pattern = RegexPattern("", is_endpoint=False)
pattern.regex = ProbeRegex()
print(f"RESULT={pattern.match('x')!r}")
