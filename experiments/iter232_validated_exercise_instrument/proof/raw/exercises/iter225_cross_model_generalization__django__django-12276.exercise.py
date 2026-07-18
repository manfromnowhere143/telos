try:
    from django import forms

    initials = (None, "", "saved.txt", False, 0)
    observed = {
        "FileInput": tuple(
            (initial, forms.FileInput().use_required_attribute(initial))
            for initial in initials
        ),
        "ClearableFileInput": tuple(
            (initial, forms.ClearableFileInput().use_required_attribute(initial))
            for initial in initials
        ),
    }
    print(f"RESULT={observed!r}")
except Exception as exc:
    print(f"RESULT={('ERROR', type(exc).__name__)!r}")
