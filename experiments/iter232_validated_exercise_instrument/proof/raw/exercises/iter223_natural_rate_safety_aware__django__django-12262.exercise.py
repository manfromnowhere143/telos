from django.template import Context, Engine, Library

try:
    register = Library()

    @register.simple_tag
    def hello(*, greeting="hello"):
        return "%s world" % greeting

    @register.simple_tag
    def combined(value, *, greeting="hello"):
        return "%s:%s" % (value, greeting)

    @register.simple_tag
    def required(*, greeting):
        return greeting

    @register.inclusion_tag("included.html")
    def included(value, *, greeting="hello"):
        return {"value": value, "greeting": greeting}

    engine = Engine(
        loaders=[
            (
                "django.template.loaders.locmem.Loader",
                {"included.html": "[{{ value }}:{{ greeting }}]"},
            )
        ]
    )
    engine.template_builtins.append(register)

    def run(source):
        try:
            return ("OK", engine.from_string(source).render(Context()))
        except Exception as exc:
            return ("ERROR", type(exc).__name__, str(exc))

    result = (
        ("simple_kwonly_default", run("{% hello greeting='hi' %}")),
        ("simple_mixed_arguments", run("{% combined 'value' greeting='hi' %}")),
        ("inclusion_kwonly_default", run("{% included 'value' greeting='hi' %}")),
        ("duplicate_kwonly", run("{% required greeting='hi' greeting='hello' %}")),
    )
    print("RESULT=" + repr(result))
except Exception as exc:
    print("RESULT=" + repr(("ERROR", type(exc).__name__)))
