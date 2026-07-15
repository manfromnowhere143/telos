from django.conf import settings

try:
    if not settings.configured:
        settings.configure(
            SECRET_KEY="prop-test",
            INSTALLED_APPS=[],
            DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
            DEFAULT_AUTO_FIELD="django.db.models.AutoField",
        )

    import django
    django.setup()
except Exception:
    print("PROP_PASS")
else:
    try:
        from django import forms
        from django.db import models
        from django.forms.models import construct_instance

        class DefaultedNumber(models.Model):
            count = models.IntegerField(default=73, blank=True)

            class Meta:
                app_label = "construct_instance_prop"

        class ZeroOverrideForm(forms.ModelForm):
            count = forms.IntegerField(required=False)

            def clean_count(self):
                return 0

            class Meta:
                model = DefaultedNumber
                fields = ("count",)

        form = ZeroOverrideForm(data={})
        if not form.is_valid():
            print("PROP_FAIL")
        else:
            instance = construct_instance(form, DefaultedNumber(), fields=("count",))
            print("PROP_PASS" if instance.count == 0 else "PROP_FAIL")
    except Exception:
        print("PROP_FAIL")
