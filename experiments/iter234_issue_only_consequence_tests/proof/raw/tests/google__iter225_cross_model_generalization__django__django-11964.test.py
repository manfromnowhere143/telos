import django
from django.conf import settings
from django.db import models

def main():
    try:
        settings.configure()
        django.setup()

        class MyChoice(models.TextChoices):
            FIRST_CHOICE = "first", "The first choice, it is"
            SECOND_CHOICE = "second", "The second choice, it is"

        class MyIntChoice(models.IntegerChoices):
            FIRST_CHOICE = 1, "The first choice, it is"
            SECOND_CHOICE = 2, "The second choice, it is"

        class MyObject(models.Model):
            my_str_value = models.CharField(max_length=10, choices=MyChoice.choices)
            my_int_value = models.IntegerField(choices=MyIntChoice.choices)

            class Meta:
                app_label = 'test_app'
                managed = False

        # Simulate a freshly created instance with enum choices directly assigned
        my_object = MyObject(
            my_str_value=MyChoice.FIRST_CHOICE,
            my_int_value=MyIntChoice.FIRST_CHOICE
        )
        
        # The issue describes that str() on the enum value returns the enum name (e.g., 'MyChoice.FIRST_CHOICE')
        # instead of the underlying value (e.g., 'first'), which causes problems during serialization or external API calls.
        str_val = str(my_object.my_str_value)
        if str_val != "first":
            print(f"RESULT={('FAIL', f'str() returned {str_val}')!r}")
            return

        int_str_val = str(my_object.my_int_value)
        if int_str_val != "1":
            print(f"RESULT={('FAIL', f'str() for IntegerChoices returned {int_str_val}')!r}")
            return

        print(f"RESULT={('PASS',)!r}")

    except Exception as e:
        print(f"RESULT={('ERROR', type(e).__name__)!r}")

if __name__ == '__main__':
    main()
