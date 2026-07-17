from django.conf.global_settings import gettext_noop

print("RESULT=" + repr(gettext_noop("same-origin")))
