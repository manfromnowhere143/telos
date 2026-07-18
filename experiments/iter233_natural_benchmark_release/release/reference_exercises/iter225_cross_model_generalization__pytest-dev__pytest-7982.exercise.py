import pytest

try:
    class Entry:
        def __init__(self, name, target_is_dir, is_symlink):
            self.name = name
            self.target_is_dir = target_is_dir
            self.is_symlink = is_symlink

        def is_dir(self, follow_symlinks=True):
            return self.target_is_dir and (follow_symlinks or not self.is_symlink)

    entries = (
        Entry("regular_dir", True, False),
        Entry("linked_dir", True, True),
        Entry("linked_file", False, True),
    )
    observed = tuple(
        (entry.name, entry.is_dir(False), entry.is_dir())
        for entry in entries
    )
    print(f"RESULT={observed!r}")
except Exception as exc:
    print(f"RESULT={('ERROR', type(exc).__name__)!r}")
