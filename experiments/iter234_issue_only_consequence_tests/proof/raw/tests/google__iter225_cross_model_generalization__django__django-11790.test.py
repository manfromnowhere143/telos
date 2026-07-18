import django
from django.conf import settings

def main():
    try:
        settings.configure(
            INSTALLED_APPS=[
                'django.contrib.auth',
                'django.contrib.contenttypes',
            ],
            DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}}
        )
        django.setup()

        from django.contrib.auth.forms import AuthenticationForm

        form = AuthenticationForm()
        username_field = form.fields['username']
        max_len = username_field.max_length
        
        if not max_len:
            print(f"RESULT={('FAIL', 'username field lacks max_length property')!r}")
            return
            
        # The issue describes that the field does not render with the maxlength attribute anymore.
        # We check the actual rendered HTML output to ensure it's present.
        rendered = str(form['username'])
        
        if f'maxlength="{max_len}"' not in rendered:
            print(f"RESULT={('FAIL', 'maxlength attribute missing from rendered widget')!r}")
        else:
            print(f"RESULT={('PASS',)!r}")
            
    except Exception as e:
        print(f"RESULT={('ERROR', type(e).__name__)!r}")

if __name__ == "__main__":
    main()
