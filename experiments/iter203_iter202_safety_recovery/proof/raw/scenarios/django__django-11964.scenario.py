from django.db import models

class SampleChoice(models.TextChoices):
    FIRST = "first", "First"

observable = (SampleChoice.values, str(SampleChoice.FIRST), SampleChoice.__str__.__doc__ is not None)
print(f"RESULT={observable!r}")
