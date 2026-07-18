import re
import django
from django.conf import settings

def main():
    try:
        if not settings.configured:
            settings.configure(
                INSTALLED_APPS=[
                    'django.contrib.auth',
                    'django.contrib.contenttypes',
                ],
                DATABASES={
                    'default': {
                        'ENGINE': 'django.db.backends.sqlite3',
                        'NAME': ':memory:',
                    }
                }
            )
            django.setup()

        from django.contrib.auth.forms import AuthenticationForm
        
        form = AuthenticationForm()
        username_field = form.fields['username']
        
        # Check widget attributes
        attr_maxlength = username_field.widget.attrs.get('maxlength')
        
        # Check rendered HTML
        rendered_html = str(form['username'])
        match = re.search(r'maxlength="(\d+)"', rendered_html)
        
        if not attr_maxlength:
            print(f"RESULT={('FAIL', 'maxlength not set in widget attrs')!r}")
        elif not match:
            print(f"RESULT={('FAIL', 'maxlength attribute not found in rendered HTML')!r}")
        elif str(attr_maxlength) != match.group(1):
            print(f"RESULT={('FAIL', 'widget attr maxlength differs from rendered HTML')!r}")
        else:
            print(f"RESULT={('PASS',)!r}")

    except Exception as e:
        print(f"RESULT={('ERROR', type(e).__name__)!r}")

if __name__ == '__main__':
    main()
