import django
from django.conf import settings
from django import forms

def run_test():
    settings.configure()
    django.setup()
    
    # Check 1: Direct API on FileInput
    widget = forms.FileInput()
    if widget.use_required_attribute(initial='dummy.txt'):
        return False, "FileInput.use_required_attribute returned True when initial data exists"
        
    if not widget.use_required_attribute(initial=None):
        return False, "FileInput.use_required_attribute returned False when no initial data exists"

    # Check 2: Rendered HTML via a Form
    class TestForm(forms.Form):
        file_field = forms.FileField(widget=forms.FileInput(), required=True)
        
    form_with_initial = TestForm(initial={'file_field': 'document.pdf'})
    html_with_initial = str(form_with_initial['file_field'])
    if 'required' in html_with_initial:
        return False, "Rendered FileInput has 'required' attribute despite initial data"
        
    form_empty = TestForm()
    html_empty = str(form_empty['file_field'])
    if 'required' not in html_empty:
        return False, "Rendered FileInput is missing 'required' attribute without initial data"

    return True, ""

try:
    passed, msg = run_test()
    if passed:
        print(f"RESULT={('PASS',)!r}")
    else:
        print(f"RESULT={('FAIL', msg)!r}")
except Exception as e:
    print(f"RESULT={('ERROR', type(e).__name__)!r}")
