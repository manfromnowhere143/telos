from django.db.models.enums import IntegerChoices


class Number(IntegerChoices):
    ONE = 1


print(f"RESULT={repr((Number.values, str(Number.ONE)))}")
