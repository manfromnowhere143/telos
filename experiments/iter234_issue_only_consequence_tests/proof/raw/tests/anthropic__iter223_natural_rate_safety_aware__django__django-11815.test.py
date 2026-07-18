try:
    import enum
    from django.db.migrations.serializer import serializer_factory
    from django.utils.translation import gettext_lazy as _

    class Status(enum.Enum):
        GOOD = _('Good')
        BAD = _('Bad')

        def __str__(self):
            return self.name

    serialized, imports = serializer_factory(Status.GOOD).serialize()

    # Should use name-based access, not value-based
    assert "Status['GOOD']" in serialized, f"got {serialized!r}"
    assert "Status('Good')" not in serialized, f"got {serialized!r}"

    # Plain enum with non-translatable value
    class Color(enum.Enum):
        RED = 'red'
        GREEN = 'green'

    s2, _i2 = serializer_factory(Color.RED).serialize()
    assert "Color['RED']" in s2, f"got {s2!r}"

    print(f"RESULT={('PASS',)!r}")
except AssertionError as exc:
    print(f"RESULT={('FAIL', str(exc))!r}")
except Exception as exc:
    print(f"RESULT={('ERROR', type(exc).__name__)!r}")
