try:
    from django.db import models
    from django.utils.translation import gettext_lazy as _

    class MyChoice(models.TextChoices):
        FIRST_CHOICE = "first", _("The first choice, it is")
        SECOND_CHOICE = "second", _("The second choice, it is")

    class MyIntChoice(models.IntegerChoices):
        ONE = 1, _("One")
        TWO = 2, _("Two")

    detail = None

    # str() of a TextChoices member must equal its value
    if str(MyChoice.FIRST_CHOICE) != "first":
        detail = f"str text got {str(MyChoice.FIRST_CHOICE)!r}"

    # str() of an IntegerChoices member must equal str of its value
    if detail is None and str(MyIntChoice.ONE) != "1":
        detail = f"str int got {str(MyIntChoice.ONE)!r}"

    # f-string uses __format__ / __str__ too
    if detail is None and f"{MyChoice.SECOND_CHOICE}" != "second":
        detail = f"fstring got {f'{MyChoice.SECOND_CHOICE}'!r}"

    # value should be usable directly as a plain str/int comparison
    if detail is None and MyChoice.FIRST_CHOICE.value != "first":
        detail = "value mismatch"

    if detail is None and MyIntChoice.TWO.value != 2:
        detail = "int value mismatch"

    # concatenation like sending to external API
    if detail is None and ("x" + str(MyChoice.FIRST_CHOICE)) != "xfirst":
        detail = "concat mismatch"

    if detail is None:
        print(f"RESULT={('PASS',)!r}")
    else:
        print(f"RESULT={('FAIL', detail)!r}")
except Exception as exc:
    print(f"RESULT={('ERROR', type(exc).__name__)!r}")
