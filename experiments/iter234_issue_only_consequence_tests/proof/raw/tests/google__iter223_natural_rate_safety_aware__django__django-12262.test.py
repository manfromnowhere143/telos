import django
from django.conf import settings
from django.template import Engine, Context, TemplateSyntaxError
from django.template.defaulttags import register

def test():
    if not settings.configured:
        settings.configure(INSTALLED_APPS=[])
        django.setup()

    @register.simple_tag(name='tag_kwarg_default')
    def tag_kwarg_default(*, greeting='hello'):
        return f'{greeting} world'

    @register.simple_tag(name='tag_kwarg')
    def tag_kwarg(*, greeting):
        return f'{greeting} world'

    engine = Engine()

    # Part 1: Tag with a keyword-only argument and a default value
    try:
        t1 = engine.from_string("{% tag_kwarg_default greeting='hi' %}")
        res1 = t1.render(Context({}))
        if res1 != 'hi world':
            print(f"RESULT={('FAIL', f'Unexpected output: {res1}')!r}")
            return
    except Exception as e:
        print(f"RESULT={('FAIL', f'Failed on keyword-only with default: {e}')!r}")
        return

    # Part 2: Supplying a keyword argument multiple times should raise a descriptive error
    try:
        engine.from_string("{% tag_kwarg greeting='hi' greeting='hello' %}")
        print(f"RESULT={('FAIL', 'Expected TemplateSyntaxError for duplicate kwargs')!r}")
        return
    except TemplateSyntaxError as e:
        msg = str(e)
        if "multiple values for keyword argument 'greeting'" not in msg:
            print(f"RESULT={('FAIL', f'Wrong error message: {msg}')!r}")
            return
    except Exception as e:
        print(f"RESULT={('FAIL', f'Wrong exception raised: {type(e).__name__}')!r}")
        return

    print(f"RESULT={('PASS',)!r}")

try:
    test()
except Exception as exc:
    print(f"RESULT={('ERROR', type(exc).__name__)!r}")
