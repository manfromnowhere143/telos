#!/usr/bin/env python3
"""Fail-closed guard for iter235 witness recovery.

The integrity condition here is NOT the one iter234 enforces. A gold-differential witness is the
ground-truth labelling instrument, so it sees gold by design and always has; forbidding that would forbid
the experiment. The gold-free detectors of iter230-iter234 never see a witness or its output, and nothing
in iter235 changes that boundary.

What must hold instead:

* **Selection is by instrument failure only.** The generator reads the derived target cohort and must not
  read a label, a divergence, or a judge verdict. For these rows no outcome exists, which is the point --
  regenerating them is instrument repair, not outcome fishing.
* **Both arms run.** A witness that produces an observable on one arm cannot establish divergence, and one
  that fails on gold is provably broken because gold is the correct fix. The executor must run candidate
  and gold and record an exit for each.
* **Every committed witness** is hash-bound and passes the iter232 stage A validity gate, which also
  rejects code that only parses on an interpreter newer than the container's.
* **The executor** carries the isolation flags, bounded timeouts, the shard contract, the wall-clock row
  ceiling, and an allowlist over mounts that permits gold but nothing else.
"""

from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.validate_iter232_exercise_validity import exercise_errors  # noqa: E402

EXP = ROOT / "experiments/iter235_witness_recovery"
WITNESSES = EXP / "proof/raw/witnesses"
SUMMARY = WITNESSES / "witnesses_summary.json"
TARGETS = EXP / "proof/raw/targets.json"
GENERATOR = ROOT / "scripts/run_iter235_witnesses.py"
RUNNER = ROOT / "scripts/ci_iter235_execute.sh"
WORKFLOW = ROOT / ".github/workflows/iter235-execute.yml"

SCHEMA = "telos.iter235.witnesses_summary.v1"
SHA_RE = re.compile(r"[0-9a-f]{64}")
MAX_WITNESS_BYTES = 64 * 1024

ALLOWED_MOUNT_SUFFIXES = (
    "/telos/candidate.patch:ro",
    "/telos/gold.patch:ro",
    ".witness.py:/telos/witness.py:ro",
)
MOUNT_RE = re.compile(r"""-v\s+["']?(?P<spec>[^"'\s]+:/[^"'\s]+:ro)["']?""")
REQUIRED_DOCKER_FLAGS = (
    "--network none", "--cap-drop ALL", "--security-opt no-new-privileges=true",
    "--pids-limit 1024", "--memory 10g", "--cpus 4",
    "--log-driver local", "--log-opt max-size=3m", "--log-opt max-file=1",
    "--log-opt compress=false",
)
REQUIRED_LIMITS = {
    "ITER235_APPLY_TIMEOUT_SECONDS": "120",
    "ITER235_WITNESS_TIMEOUT_SECONDS": "180",
    "ITER235_KILL_GRACE_SECONDS": "10",
    "ITER235_OUTPUT_LIMIT_BYTES": "262144",
    "ITER235_ROW_CEILING_SECONDS": "2400",
}
# Outcome fields the SELECTOR must never consult. Gold is absent from this list deliberately: the witness
# generator needs the gold hunk to build a differential, and that is its job.
SELECTION_FORBIDDEN = ("diverges", "outcome_complete", "judge", "verdict", "confirmed", "label")


def _code_strings(text: str) -> list[str]:
    tree = ast.parse(text)
    docstrings = {
        id(n.body[0].value) for n in ast.walk(tree)
        if isinstance(n, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
        and n.body and isinstance(n.body[0], ast.Expr)
        and isinstance(n.body[0].value, ast.Constant) and isinstance(n.body[0].value.value, str)
    }
    return [
        n.value for n in ast.walk(tree)
        if isinstance(n, ast.Constant) and isinstance(n.value, str) and id(n) not in docstrings
    ]


def selection_integrity_errors(text: str) -> list[str]:
    """The generator must take its cohort from the derived targets and read no outcome."""

    errors: list[str] = []
    try:
        literals = _code_strings(text)
    except SyntaxError as exc:
        return [f"generator does not parse: {exc}"]
    joined = "\n".join(literals)
    if "targets.json" not in joined:
        errors.append("generator does not read the derived target cohort")
    for field in SELECTION_FORBIDDEN:
        if field in joined:
            errors.append(f"generator reads an outcome field: {field}")
    return errors


def runner_safety_errors(text: str) -> list[str]:
    errors: list[str] = []
    for flag in REQUIRED_DOCKER_FLAGS:
        if flag not in text:
            errors.append(f"executor missing isolation flag: {flag}")
    for name, value in REQUIRED_LIMITS.items():
        if f"{name}={value}" not in text:
            errors.append(f"executor does not pin {name}={value}")
    code = "\n".join(ln for ln in text.splitlines() if not ln.lstrip().startswith("#"))
    mounts = [m.group("spec").strip("\"'") for m in MOUNT_RE.finditer(code)]
    if not mounts:
        errors.append("executor declares no mounts to check")
    for spec in mounts:
        if not spec.endswith(ALLOWED_MOUNT_SUFFIXES):
            errors.append(f"executor mounts outside the allowlist: {spec}")
    if "IMAGE_PROVENANCE_INSPECTION_FAIL" not in text:
        errors.append("executor does not fail closed on missing image provenance")
    if "ITER235_ROW_CEILING_SECONDS}s" not in text:
        errors.append("executor lacks the bounded wall-clock row ceiling")
    for fragment in (
        'SHARD_INDEX_RAW="${TELOS_ITER235_SHARD_INDEX-0}"',
        "(( o % SHARD_COUNT == SHARD_INDEX ))",
    ):
        if text.count(fragment) != 1:
            errors.append("executor shard contract missing or duplicated")
    # Both arms, or divergence cannot be established at all.
    for fragment in ("run_arm candidate /telos/candidate.patch", "run_arm gold /telos/gold.patch"):
        if fragment not in text:
            errors.append(f"executor does not run: {fragment}")
    return errors


def witness_state_errors() -> tuple[str, list[str]]:
    if not SUMMARY.exists():
        return ("no-witnesses-yet",
                [] if not list(WITNESSES.glob("*.py")) else
                ["witness scripts exist without witnesses_summary.json"])
    summary = json.loads(SUMMARY.read_text())
    errors: list[str] = []
    if summary.get("schema_version") != SCHEMA:
        errors.append("witnesses summary schema mismatch")

    if TARGETS.is_file():
        target_keys = {
            (t["run"], t["instance_id"])
            for t in json.loads(TARGETS.read_text())["targets"]
        }
        for row in summary.get("manifest") or []:
            if (row.get("run"), row.get("instance_id")) not in target_keys:
                errors.append(
                    f"witness for {row.get('instance_id')} is not in the derived cohort"
                )

    expected: dict[Path, str] = {}
    for index, row in enumerate(summary.get("manifest") or []):
        label = f"witness manifest row {index}"
        stem = f"{row.get('run')}__{str(row.get('instance_id')).replace('/', '__')}"
        status = row.get("status")
        if status == "witness":
            digest = row.get("witness_sha256")
            if not isinstance(digest, str) or not SHA_RE.fullmatch(digest):
                errors.append(f"{label} witness_sha256 is invalid")
                continue
            expected[WITNESSES / f"{stem}.witness.py"] = digest
        elif status == "no_valid_witness":
            if (WITNESSES / f"{stem}.witness.py").exists():
                errors.append(f"{label} uncovered row has a witness committed on disk")
            if not row.get("rejected_attempts"):
                errors.append(f"{label} must record why every attempt was rejected")
        else:
            errors.append(f"{label} has an unknown status")

    actual = set(WITNESSES.glob("*.witness.py"))
    if actual != set(expected):
        missing = sorted(p.name for p in set(expected) - actual)
        extra = sorted(p.name for p in actual - set(expected))
        errors.append(f"witness file set mismatch; missing={missing[:3]}, extra={extra[:3]}")
    for path, digest in expected.items():
        if not path.is_file():
            continue
        raw = path.read_bytes()
        if not raw or len(raw) > MAX_WITNESS_BYTES:
            errors.append(f"{path.name}: size outside the safe bound")
            continue
        payload = raw[:-1] if raw.endswith(b"\n") else raw
        if hashlib.sha256(payload).hexdigest() != digest:
            errors.append(f"{path.name}: summary hash mismatch")
        errors.extend(
            f"{path.name}: {e}" for e in exercise_errors(payload.decode("utf-8", "replace"))
        )
    return ("valid" if not errors else "invalid"), errors


def main() -> int:
    status, errors = witness_state_errors()
    for path, checker, name in (
        (GENERATOR, selection_integrity_errors, "generator"),
        (RUNNER, runner_safety_errors, "executor"),
    ):
        try:
            errors.extend(checker(path.read_text()))
        except OSError as exc:
            errors.append(f"cannot inspect iter235 {name}: {exc}")
    if WORKFLOW.is_file():
        text = WORKFLOW.read_text()
        if "if: always()" in text or "continue-on-error:" in text:
            errors.append("iter235 workflow must not weaken failure semantics")
    if errors:
        for error in errors:
            print(f"iter235 safety error: {error}", file=sys.stderr)
        return 1
    print(
        f"iter235 safety: cohort selected by instrument failure, both arms run, witnesses {status}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
