try:
    import django
    from django.conf import settings
    
    if not settings.configured:
        settings.configure(INSTALLED_APPS=[])
        django.setup()
        
    from django.db import models
    
    class FooBar(models.Model):
        foo_bar = models.CharField("foo", max_length=10, choices=[(1, 'foo'), (2, 'bar')])
        
        class Meta:
            app_label = 'myapp'
            
        def get_foo_bar_display(self):
            return "something"
            
    obj = FooBar(foo_bar=1)
    res = obj.get_foo_bar_display()
    
    if res == "something":
        print(f"RESULT={('PASS',)!r}")
    else:
        print(f"RESULT={('FAIL', f'Overridden method ignored, got: {res}')!r}")
except Exception as e:
    print(f"RESULT={('ERROR', type(e).__name__)!r}")
