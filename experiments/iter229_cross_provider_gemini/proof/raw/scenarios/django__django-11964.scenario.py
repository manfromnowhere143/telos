from django.db.models.enums import TextChoices


class Probe(TextChoices):
    ITEM = "item", "Item"


print(f"RESULT={repr((Probe.values, str(Probe.ITEM)))}")
