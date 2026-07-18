try:
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure(
            DEBUG=True,
            TEMPLATES=[{
                'BACKEND': 'django.template.backends.django.DjangoTemplates',
                'DIRS': [],
                'APP_DIRS': False,
                'OPTIONS': {'libraries': {'reg': __name__}},
            }],
            INSTALLED_APPS=[],
        )
    django.setup()

    from django import template
    register = template.Library()

    @register.simple_tag
    def hello(*, greeting='hello'):
        return f'{greeting} world'

    @register.simple_tag
    def hi(*, greeting):
        return f'{greeting} world'

    detail = None

    # Case 1: kw-only arg with default supplied works
    out = template.Template("{% load reg %}{% hello greeting='hi' %}").render(template.Context({}))
    if out != 'hi world':
        detail = f"case1 got {out!r}"

    # Case 1b: default used
    out2 = template.Template("{% load reg %}{% hello %}").render(template.Context({}))
    if detail is None and out2 != 'hello world':
        detail = f"case1b got {out2!r}"

    # Case 2: duplicate keyword -> multiple values message
    if detail is None:
        try:
            template.Template("{% load reg %}{% hi greeting='hi' greeting='hello' %}").render(template.Context({}))
            detail = "no error on duplicate kwarg"
        except template.TemplateSyntaxError as e:
            if 'multiple values for keyword argument' not in str(e):
                detail = f"wrong msg: {e}"

    if detail is None:
        print(f"RESULT={('PASS',)!r}")
    else:
        print(f"RESULT={('FAIL', detail)!r}")
except Exception as exc:
    print(f"RESULT={('ERROR', type(exc).__name__)!r}")
