import re
import django
from django.conf import settings

def main():
    try:
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
        
        # Instantiate the form and render the username field to HTML
        form = AuthenticationForm()
        html = str(form['username'])
        expected_max = form.fields['username'].max_length
        
        if expected_max is None:
            raise AssertionError("Field 'username' has no max_length set")
            
        # Extract the maxlength attribute from the rendered HTML
        match = re.search(r'maxlength="(\d+)"', html)
        if not match:
            raise AssertionError(f"maxlength attribute missing in rendered HTML: {html}")
            
        rendered_max = int(match.group(1))
        
        # Verify it matches the field's max_length
        if rendered_max != expected_max:
            raise AssertionError(f"Rendered maxlength {rendered_max} != {expected_max}")
            
        print(f"RESULT={('PASS',)!r}")
        
    except AssertionError as e:
        print(f"RESULT={('FAIL', str(e))!r}")
    except Exception as e:
        print(f"RESULT={('ERROR', type(e).__name__)!r}")

if __name__ == "__main__":
    main()
