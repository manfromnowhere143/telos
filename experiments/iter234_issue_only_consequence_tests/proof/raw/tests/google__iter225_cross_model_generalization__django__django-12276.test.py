import django
from django.conf import settings
from django.forms import Form, FileField
from django.forms.widgets import FileInput

def run():
    try:
        if not settings.configured:
            settings.configure()
            django.setup()

        # 1. Direct widget method test
        widget = FileInput()
        
        # When initial data is provided, use_required_attribute should be False
        if widget.use_required_attribute(initial='dummy_file.txt'):
            print(f"RESULT={('FAIL', 'FileInput.use_required_attribute returned True with initial data')!r}")
            return
        
        # When no initial data is provided, use_required_attribute should be True
        if not widget.use_required_attribute(initial=None):
            print(f"RESULT={('FAIL', 'FileInput.use_required_attribute returned False without initial data')!r}")
            return

        # 2. Form rendering test
        class TestForm(Form):
            file = FileField(widget=FileInput, required=True)

        # Without initial data, the required attribute should be present
        form_no_initial = TestForm()
        html_no_initial = str(form_no_initial['file'])
        if 'required' not in html_no_initial:
            print(f"RESULT={('FAIL', 'required attribute missing when no initial data')!r}")
            return

        # With initial data, the required attribute should NOT be present
        form_initial = TestForm(initial={'file': 'dummy_file.txt'})
        html_initial = str(form_initial['file'])
        if 'required' in html_initial:
            print(f"RESULT={('FAIL', 'required attribute present when initial data exists')!r}")
            return

        print(f"RESULT={('PASS',)!r}")

    except Exception as e:
        print(f"RESULT={('ERROR', type(e).__name__)!r}")

if __name__ == "__main__":
    run()
