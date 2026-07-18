try:
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure(USE_I18N=False)
    django.setup()
    from django.forms.widgets import FileInput

    w = FileInput()
    # When initial data exists, required attribute should NOT be output
    result_with_initial = w.use_required_attribute(initial="somefile.txt")
    # When no initial data, required attribute may be output
    result_without_initial = w.use_required_attribute(initial=None)

    fails = []
    if result_with_initial is not False:
        fails.append(f"with_initial={result_with_initial!r}")
    if result_without_initial is not True:
        fails.append(f"without_initial={result_without_initial!r}")

    if fails:
        print(f"RESULT={('FAIL', ', '.join(fails))!r}")
    else:
        print(f"RESULT={('PASS',)!r}")
except Exception as exc:
    print(f"RESULT={('ERROR', type(exc).__name__)!r}")
