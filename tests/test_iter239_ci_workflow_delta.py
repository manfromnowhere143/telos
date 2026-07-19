"""Known-good and known-bad tests for iter239's exact CI workflow delta."""

from __future__ import annotations

from pathlib import Path

from scripts import validate_iter239_ci_workflow_delta as guard


ROOT = Path(__file__).resolve().parents[1]


def predecessor() -> bytes:
    return guard.load_predecessor_workflow(ROOT)


def expected() -> bytes:
    return guard.expected_workflow(predecessor())


def mutated(old: bytes, new: bytes) -> bytes:
    candidate = expected()
    assert candidate.count(old) == 1, old
    return candidate.replace(old, new, 1)


def assert_rejected(candidate: bytes, reason: str) -> None:
    errors = guard.validation_errors(predecessor(), candidate)
    assert errors
    assert any(reason in error for error in errors), errors


def test_committed_workflow_is_the_exact_preregistered_delta() -> None:
    assert (ROOT / guard.WORKFLOW_PATH).read_bytes() == expected()
    assert guard.validate_current(ROOT) == []


def test_exact_event_specific_name_is_accepted() -> None:
    assert guard.validation_errors(predecessor(), expected()) == []


def test_old_or_alternate_job_name_is_rejected() -> None:
    assert_rejected(predecessor(), "job-name drift")
    assert_rejected(
        mutated(
            guard.NEW_JOB_NAME_LINE,
            b"    name: verify pull_request py${{ matrix.python-version }}\n",
        ),
        "job-name drift",
    )


def test_push_or_pull_request_path_filter_is_rejected() -> None:
    assert_rejected(
        mutated(
            b"  pull_request:\n",
            b'  pull_request:\n    paths:\n      - "scripts/**"\n',
        ),
        "path filter",
    )
    assert_rejected(
        mutated(
            b"  push:\n",
            b'  push:\n    paths-ignore:\n      - "docs/**"\n',
        ),
        "path filter",
    )


def test_trigger_and_permission_drift_are_rejected() -> None:
    assert_rejected(
        mutated(b"  push:\n", b"  workflow_dispatch:\n"),
        "trigger drift",
    )
    assert_rejected(
        mutated(b"  contents: read\n", b"  contents: write\n"),
        "permission drift",
    )


def test_runner_and_matrix_drift_are_rejected() -> None:
    assert_rejected(
        mutated(b"    runs-on: ubuntu-24.04\n", b"    runs-on: ubuntu-latest\n"),
        "runner drift",
    )
    assert_rejected(
        mutated(
            b'        python-version: ["3.11", "3.12"]\n',
            b'        python-version: ["3.11"]\n',
        ),
        "matrix or strategy drift",
    )


def test_action_dependency_and_command_drift_are_rejected() -> None:
    assert_rejected(
        mutated(
            b"actions/checkout@9c091bb21b7c1c1d1991bb908d89e4e9dddfe3e0",
            b"actions/checkout@1111111111111111111111111111111111111111",
        ),
        "action or dependency drift",
    )
    assert_rejected(
        mutated(b"        run: pytest -q\n", b"        run: pytest -q -x\n"),
        "command or dependency drift",
    )
    assert_rejected(
        mutated(
            b"            -r requirements-ci.txt\n",
            b"            -r requirements.txt\n",
        ),
        "command or dependency drift",
    )


def test_job_level_condition_and_continue_on_error_are_rejected() -> None:
    assert_rejected(
        mutated(
            b"  verify:\n",
            b"  verify:\n    if: github.actor != 'dependabot[bot]'\n",
        ),
        "job-level condition drift",
    )
    assert_rejected(
        mutated(
            b"  verify:\n",
            b"  verify:\n    continue-on-error: true\n",
        ),
        "job-level continue-on-error drift",
    )


def test_step_level_condition_and_continue_on_error_are_rejected() -> None:
    assert_rejected(
        mutated(
            b"      - name: Tests\n        run: pytest -q\n",
            b"      - name: Tests\n        if: github.event_name == 'push'\n"
            b"        run: pytest -q\n",
        ),
        "step-level condition drift",
    )
    assert_rejected(
        mutated(
            b"      - name: Tests\n        run: pytest -q\n",
            b"      - name: Tests\n        continue-on-error: true\n"
            b"        run: pytest -q\n",
        ),
        "step-level continue-on-error drift",
    )


def test_extra_job_or_step_is_rejected() -> None:
    assert_rejected(
        expected()
        + b"\n  decoy:\n    runs-on: ubuntu-24.04\n    steps:\n"
        + b"      - run: true\n",
        "job-set drift",
    )
    assert_rejected(
        mutated(
            b"    steps:\n",
            b"    steps:\n      - name: Decoy\n        run: true\n",
        ),
        "step-set drift",
    )


def test_semantically_inert_byte_drift_is_rejected() -> None:
    assert_rejected(expected() + b"# unreviewed comment\n", "workflow byte delta")


def test_duplicate_yaml_key_is_rejected() -> None:
    assert_rejected(
        mutated(
            b"permissions:\n  contents: read\n",
            b"permissions:\n  contents: read\n  contents: read\n",
        ),
        "duplicate key",
    )


def test_predecessor_digest_is_pinned() -> None:
    errors = guard.validation_errors(predecessor() + b"\n", expected())
    assert errors
    assert "pinned predecessor workflow digest mismatch" in errors[0]
