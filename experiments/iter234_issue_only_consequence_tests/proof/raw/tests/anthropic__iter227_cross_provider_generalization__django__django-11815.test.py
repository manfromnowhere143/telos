try:
    import enum
    from django.db.migrations.serializer import serializer_factory
    from django.utils.translation import gettext_lazy as _

    class Status(enum.Enum):
        GOOD = _('Good')
        BAD = _('Bad')

        def __str__(self):
            return self.name

    string, imports = serializer_factory(Status.GOOD).serialize()

    # The migration should reference the enum by NAME, not by value.
    if "Status['GOOD']" not in string:
        raise AssertionError(f"expected name-based access, got {string!r}")
    if "Status('Good')" in string:
        raise AssertionError(f"used value instead of name: {string!r}")

    # Plain (non-lazy) enum should also work by name.
    class Color(enum.Enum):
        RED = 'r'
        GREEN = 'g'

    string2, _imports2 = serializer_factory(Color.RED).serialize()
    if "Color['RED']" not in string2:
        raise AssertionError(f"expected Color['RED'], got {string2!r}")

    print(f"RESULT={('PASS',)!r}")
except AssertionError as exc:
    print(f"RESULT={('FAIL', str(exc))!r}")
except Exception as exc:
    print(f"RESULT={('ERROR', type(exc).__name__)!r}")
