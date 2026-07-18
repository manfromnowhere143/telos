try:
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure(USE_I18N=False)
    django.setup()
    from django.forms.widgets import FileInput

    w = FileInput()
    # When initial data exists, required attribute should NOT be rendered
    if w.use_required_attribute(initial="something.txt") is not False:
        print(f"RESULT={('FAIL', 'required rendered with initial')!r}")
    elif w.use_required_attribute(initial=None) is not True:
        print(f"RESULT={('FAIL', 'required not rendered without initial')!r}")
    else:
        print(f"RESULT={('PASS',)!r}")
except Exception as exc:
    print(f"RESULT={('ERROR', type(exc).__name__)!r}")
