import django
from django.conf import settings

if not settings.configured:
    settings.configure()
    django.setup()

from django.db import models

class MyChoice(models.TextChoices):
    FIRST = "first", "The first choice"

class MyIntChoice(models.IntegerChoices):
    ONE = 1, "The first choice"

try:
    val_text = str(MyChoice.FIRST)
    if val_text != "first":
        raise AssertionError(f"TextChoices __str__ gave {val_text!r}, expected 'first'")
        
    val_int = str(MyIntChoice.ONE)
    if val_int != "1":
        raise AssertionError(f"IntegerChoices __str__ gave {val_int!r}, expected '1'")
        
    print(f"RESULT={('PASS',)!r}")
except AssertionError as e:
    print(f"RESULT={('FAIL', str(e))!r}")
except Exception as e:
    print(f"RESULT={('ERROR', type(e).__name__)!r}")
