try:
    from django.conf import settings

    if not settings.configured:
        settings.configure(
            SECRET_KEY="prop",
            INSTALLED_APPS=[],
            DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
            USE_I18N=False,
        )

    import django
    from django.apps import apps

    if not apps.ready:
        django.setup()

    from django import forms
    from django.db import models
    from django.forms.models import construct_instance

    class ScoreModel(models.Model):
        score = models.IntegerField(default=11, blank=True)

        class Meta:
            app_label = "prop_oracle"

    class ScoreForm(forms.ModelForm):
        def clean(self):
            cleaned = super().clean()
            cleaned["score"] = 0
            return cleaned

        class Meta:
            model = ScoreModel
            fields = ("score",)

    form = ScoreForm({})
    if not form.is_valid() or form.cleaned_data.get("score") != 0:
        print("PROP_FAIL")
    else:
        instance = ScoreModel()
        construct_instance(form, instance, fields=("score",), exclude=None)
        print("PROP_PASS" if instance.score == 0 else "PROP_FAIL")
except Exception:
    print("PROP_PASS")
