import django
from django.conf import settings
from django.db import models
from django.contrib import admin
import re

def main():
    try:
        settings.configure(
            INSTALLED_APPS=[
                'django.contrib.admin',
                'django.contrib.contenttypes',
                'django.contrib.auth',
            ],
            DATABASES={'default': {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': ':memory:'
            }}
        )
        django.setup()

        class DummyModel(models.Model):
            name = models.CharField(max_length=10)
            class Meta:
                app_label = 'admin'

        class DummyAdmin(admin.ModelAdmin):
            list_editable = ['name']
            def get_queryset(self, request):
                class FakeQS:
                    def filter(self, **kwargs):
                        return kwargs
                return FakeQS()

        ma = DummyAdmin(DummyModel, admin.site)
        
        class MockRequest:
            # We use 'prefix(' to force a regex failure if left unescaped
            POST = {'prefix(-0-id': '1'}
        
        # This will raise re.error if prefix is used raw in regex formatting
        res = ma._get_list_editable_queryset(MockRequest(), 'prefix(')
        
        # If successfully escaped, it should extract the primary key
        if res.get('pk__in') != ['1']:
            print(f"RESULT={('FAIL', 'Failed to extract primary key')!r}")
            return
            
    except re.error as e:
        print(f"RESULT={('FAIL', 're.error raised: ' + str(e))!r}")
    except Exception as e:
        print(f"RESULT={('ERROR', type(e).__name__)!r}")
    else:
        print(f"RESULT={('PASS',)!r}")

if __name__ == '__main__':
    main()
