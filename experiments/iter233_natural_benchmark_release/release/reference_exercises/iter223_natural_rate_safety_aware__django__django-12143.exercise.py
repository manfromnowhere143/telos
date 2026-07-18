import types

try:
    from django.contrib.admin.options import ModelAdmin

    prefix = "items[0].+?"
    request = types.SimpleNamespace(
        POST={
            "items[0].+?-0-id": "literal-prefix",
            "items0x-0-id": "regex-interpretation",
            "items[0].+?-1-id-extra": "wrong-suffix",
        }
    )
    admin = types.SimpleNamespace(
        model=types.SimpleNamespace(
            _meta=types.SimpleNamespace(pk=types.SimpleNamespace(name="id"))
        )
    )
    result = ModelAdmin._get_edited_object_pks(admin, request, prefix)
    print("RESULT={!r}".format(result))
except Exception as exc:
    print("RESULT={!r}".format(("ERROR", type(exc).__name__)))
