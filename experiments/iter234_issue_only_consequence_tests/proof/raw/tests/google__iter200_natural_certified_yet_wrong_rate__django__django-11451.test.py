import django
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend

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
        
        UserModel = get_user_model()
        
        # Track calls to avoid actual DB access and hasher work, which are expensive.
        called_get = []
        def mock_get_by_natural_key(username):
            called_get.append(username)
            # Simulating the missing user since None isn't a valid username
            raise UserModel.DoesNotExist("Mocked DoesNotExist")
            
        UserModel._default_manager.get_by_natural_key = mock_get_by_natural_key

        called_set = []
        def mock_set_password(self, raw_password):
            called_set.append(raw_password)
            
        UserModel.set_password = mock_set_password
        
        backend = ModelBackend()
        
        # When username=None, it should short-circuit and not execute queries or hasher
        backend.authenticate(request=None, username=None, password="dummy_password")
        
        if called_get:
            print(f"RESULT={('FAIL', 'get_by_natural_key was executed when username is None')!r}")
            return
            
        if called_set:
            print(f"RESULT={('FAIL', 'set_password was called needlessly')!r}")
            return
            
        print(f"RESULT={('PASS',)!r}")
            
    except Exception as e:
        print(f"RESULT={('ERROR', type(e).__name__)!r}")

if __name__ == '__main__':
    main()
