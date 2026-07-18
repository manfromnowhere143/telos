import django.db.models as models

try:
    class TextChoice(models.TextChoices):
        FIRST = "first", "First choice"
        EMPTY = "", "Empty choice"

    class IntegerChoice(models.IntegerChoices):
        ZERO = 0, "Zero"
        ONE = 1, "One"

    result = (
        ("text", [(str(member), repr(member.value), type(member).__name__) for member in TextChoice]),
        ("integer", [(str(member), repr(member.value), type(member).__name__) for member in IntegerChoice]),
    )
    print("RESULT=" + repr(result))
except Exception as exc:
    print("RESULT=" + repr(("ERROR", type(exc).__name__)))
