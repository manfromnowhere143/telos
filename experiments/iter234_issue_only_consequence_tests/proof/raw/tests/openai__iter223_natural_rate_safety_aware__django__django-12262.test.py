try:
    from django.template import Context, Engine, Library, TemplateSyntaxError

    register = Library()
    engine = Engine(libraries={"fixture_tags": register})

    @register.simple_tag
    def simple(value, *, left="<", right=">"):
        return f"{left}{value}{right}"

    inclusion_template = engine.from_string("{{ pre }}{{ value }}{{ post }}")

    @register.inclusion_tag(inclusion_template)
    def card(value, *, pre="(", post=")"):
        return {"value": value, "pre": pre, "post": post}

    template = engine.from_string(
        '{% load fixture_tags %}'
        '{% simple "x" %}|{% simple "x" right="!" %}|'
        '{% simple "x" left="[" right="]" %}|'
        '{% card "y" %}|{% card "y" pre="[" post="]" %}'
    )
    rendered = template.render(Context())
    if rendered != "<x>|<x!|[x]|(y)|[y]":
        raise AssertionError("keyword-only-output")

    try:
        engine.from_string(
            '{% load fixture_tags %}{% card "y" pre="[" pre="{" %}'
        )
    except TemplateSyntaxError as exc:
        if str(exc) != "'card' received multiple values for keyword argument 'pre'":
            raise AssertionError("duplicate-message")
    else:
        raise AssertionError("duplicate-accepted")

except AssertionError as exc:
    detail = str(exc) or "assertion"
    print(f"RESULT={('FAIL', detail)!r}")
except Exception as exc:
    print(f"RESULT={('ERROR', type(exc).__name__)!r}")
else:
    print(f"RESULT={('PASS',)!r}")
