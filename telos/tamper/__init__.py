"""Verifier-tamper detection over raw candidate patches.

This package operates only on the raw unified diff a candidate submits plus the publicly
declared ``FAIL_TO_PASS`` test node ids. It never reads a ground-truth label, an attack-type
field, or an authored semantic boolean. It exists to move Telos completion verification from
self-authored fixtures onto external ground truth (real SWE-bench Verified patches).
"""

from telos.tamper.detector import (
    Candidate,
    TamperSignal,
    TamperVerdict,
    detect_tamper,
    execution_tests_only_accepts,
)

__all__ = [
    "Candidate",
    "TamperSignal",
    "TamperVerdict",
    "detect_tamper",
    "execution_tests_only_accepts",
]
