try:
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure(INSTALLED_APPS=[], DATABASES={})
    django.setup()
    from django.db import models

    class MyChoice(models.TextChoices):
        FIRST_CHOICE = "first", "The first choice, it is"
        SECOND_CHOICE = "second", "The second choice, it is"

    class MyIntChoice(models.IntegerChoices):
        ONE = 1, "One"
        TWO = 2, "Two"

    detail = None

    # str() of a TextChoices member should be its value
    if str(MyChoice.FIRST_CHOICE) != "first":
        detail = f"text str={str(MyChoice.FIRST_CHOICE)!r}"
    elif str(MyChoice.SECOND_CHOICE) != "second":
        detail = f"text str2={str(MyChoice.SECOND_CHOICE)!r}"
    elif str(MyIntChoice.ONE) != "1":
        detail = f"int str={str(MyIntChoice.ONE)!r}"
    elif str(MyIntChoice.TWO) != "2":
        detail = f"int str2={str(MyIntChoice.TWO)!r}"
    # still an instance of str/int
    elif not isinstance(MyChoice.FIRST_CHOICE, str):
        detail = "text not str instance"
    elif not isinstance(MyIntChoice.ONE, int):
        detail = "int not int instance"
    # value comparison
    elif MyChoice.FIRST_CHOICE.value != "first":
        detail = "text value wrong"
    elif int(MyIntChoice.TWO) != 2:
        detail = "int value wrong"

    if detail is None:
        print(f"RESULT={('PASS',)!r}")
    else:
        print(f"RESULT={('FAIL', detail)!r}")
except Exception as exc:
    print(f"RESULT={('ERROR', type(exc).__name__)!r}")
