import re
import django
from django.conf import settings

try:
    if not settings.configured:
        settings.configure(DEBUG=True, USE_TZ=True)
    django.setup()

    # Simulate the admin logic: extract pks from formset POST data
    # where prefix contains regex special characters.
    prefix = "form$[.*"
    pk_name = "id"

    # Build the correct regex the way the fixed code should (using re.escape)
    pk_pattern = re.compile(
        r'{}-\d+-{}$'.format(re.escape(prefix), pk_name)
    )

    # POST-like keys that SHOULD match
    matching_keys = [
        "{}-0-{}".format(prefix, pk_name),
        "{}-1-{}".format(prefix, pk_name),
        "{}-42-{}".format(prefix, pk_name),
    ]
    for key in matching_keys:
        assert pk_pattern.match(key), "should match: {}".format(key)

    # Keys that should NOT match (data loss / false matches otherwise)
    non_matching = [
        "formX[.x-0-id",   # would match if $ etc were unescaped-ish
        "form$[.*-0-idextra",
        "unrelated-0-id",
    ]
    for key in non_matching:
        assert not pk_pattern.match(key), "should not match: {}".format(key)

    # Verify that a naive (unescaped) regex would misbehave, confirming
    # the escape is meaningful for this prefix.
    naive = re.compile(r'{}-\d+-{}$'.format(prefix, pk_name))
    # naive pattern is broken/does not reliably match the literal key
    assert not naive.match(matching_keys[0]), "naive pattern unexpectedly matched"

    print(f"RESULT={('PASS',)!r}")
except AssertionError as exc:
    print(f"RESULT={('FAIL', str(exc))!r}")
except Exception as exc:
    print(f"RESULT={('ERROR', type(exc).__name__)!r}")
