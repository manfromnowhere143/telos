"""Known-good and adversarial checks for iter239's additive remote receipt."""

from __future__ import annotations

from copy import deepcopy
import importlib.util
import os
from pathlib import Path
import py_compile
from typing import Any, Callable

import pytest

from scripts import capture_iter239_remote_acceptance as capture_guard
from scripts import validate_iter239_remote_acceptance as guard


ROOT = Path(__file__).resolve().parents[1]
RECEIPT = (
    ROOT
    / "experiments"
    / "iter240_ground_truth_admission_design"
    / "proof"
    / "iter239_remote_acceptance.json"
)
RAW_ROOT = RECEIPT.parent / "raw" / "iter239_remote_acceptance"
CATALOGUE = (
    ROOT
    / "experiments"
    / "iter240_ground_truth_admission_design"
    / "fixtures"
    / "iter239_remote_acceptance_known_bad.json"
)

EXPECTED_ERRORS = {
    "raw_digest_mismatch": "raw response byte binding differs",
    "attempt_marker_digest_mismatch": "capture-attempt marker byte binding differs",
    "attempt_marker_state_changed": "capture-attempt fixed plan differs",
    "capture_instrument_digest_mismatch": (
        "capture instrument byte binding differs"
    ),
    "unexpected_raw_file": "remote acceptance raw file set differs",
    "oversized_raw_response": "raw response byte binding differs",
    "duplicate_json_key": "duplicate JSON key",
    "write_count_nonzero": "remote acceptance request counts differ",
    "pagination_link_present": "response inventory fixed metadata differs",
    "numeric_http_status_float": "response inventory fixed metadata differs",
    "pull_request_not_merged": "pull-request merge projection differs",
    "sealed_run_second_attempt": "workflow run acceptance differs",
    "workflow_run_id_float": "workflow run identity differs",
    "required_check_wrong_app": (
        "required check is absent, duplicated, or from the wrong app"
    ),
    "required_check_duplicated": (
        "required check is absent, duplicated, or from the wrong app"
    ),
    "required_check_suite_mismatch": "required check acceptance differs",
    "sealed_run_completed_after_merge": "sealed run does not predate merge",
    "merged_run_stale_head": "workflow run acceptance differs",
    "master_unprotected": "post-merge master branch projection differs",
    "ruleset_bypass_enabled": "post-merge ruleset identity/enforcement differs",
    "effective_rule_missing": "post-merge effective rules differ",
    "independent_review_overclaim": "receipt conclusion differs or overclaims",
    "limitation_weakened": "remote acceptance limitations differ",
    "response_predates_merged_ci": "final response predates merged-master CI",
    "duplicate_request_id": (
        "GitHub response request IDs are absent or duplicated"
    ),
    "response_dates_out_of_order": (
        "GitHub response dates are absent or out of request order"
    ),
}


class FakeResponse:
    def __init__(self, *, index: int, status: int = 200) -> None:
        self.status = status
        self._body = b"{}"
        self._headers = [
            ("Content-Type", "application/json; charset=utf-8"),
            ("Date", "Sun, 19 Jul 2026 21:00:00 GMT"),
            ("X-GitHub-Api-Version-Selected", capture_guard.API_VERSION),
            ("X-GitHub-Request-Id", f"fixture-{index}"),
        ]

    def read(self, amount: int) -> bytes:
        assert amount == capture_guard.MAX_RESPONSE_BYTES + 1
        return self._body

    def getheaders(self) -> list[tuple[str, str]]:
        return self._headers


class FakeConnection:
    def __init__(self, responses: list[FakeResponse]) -> None:
        self.responses = responses
        self.requests: list[tuple[str, str, dict[str, str]]] = []
        self.closed = False

    def request(
        self,
        method: str,
        path: str,
        *,
        headers: dict[str, str],
    ) -> None:
        self.requests.append((method, path, headers))

    def getresponse(self) -> FakeResponse:
        return self.responses.pop(0)

    def close(self) -> None:
        self.closed = True


def configure_fake_capture(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    responses: list[FakeResponse],
) -> FakeConnection:
    class FakeValidator:
        @staticmethod
        def validate(**_kwargs: Any) -> list[str]:
            return []

    validator_raw = (
        ROOT / "scripts/validate_iter239_remote_acceptance.py"
    ).read_bytes()
    FakeValidator.__exact_source_sha256__ = guard.sha256(validator_raw)
    FakeValidator.__exact_source_byte_count__ = len(validator_raw)
    connection = FakeConnection(responses)
    monkeypatch.setattr(capture_guard, "RECEIPT", tmp_path / "receipt.json")
    monkeypatch.setattr(capture_guard, "RAW_ROOT", tmp_path / "raw")
    monkeypatch.setattr(
        capture_guard,
        "token_from_environment_or_gh",
        lambda: "fixture-token",
    )
    monkeypatch.setattr(capture_guard, "preflight_capture", FakeValidator)
    monkeypatch.setattr(
        capture_guard,
        "validate_staged_receipt",
        lambda *args, **kwargs: None,
    )
    monkeypatch.setattr(capture_guard.ssl, "create_default_context", lambda: object())
    monkeypatch.setattr(
        capture_guard.http.client,
        "HTTPSConnection",
        lambda *args, **kwargs: connection,
    )
    monkeypatch.setattr(
        capture_guard,
        "build_receipt",
        lambda documents, inventory, *, started_at, completed_at, marker_bytes: {
            "completed_at": completed_at,
            "documents": sorted(documents),
            "inventory": inventory,
            "marker_sha256": guard.sha256(marker_bytes),
            "started_at": started_at,
        },
    )
    return connection


def load_json(path: Path) -> Any:
    return guard.strict_json(path.read_bytes(), label=str(path))


def inventory_entry(receipt: dict[str, Any], name: str) -> dict[str, Any]:
    matches = [
        row
        for row in receipt["capture"]["response_inventory"]
        if row["name"] == name
    ]
    assert len(matches) == 1
    return matches[0]


def synthetic_documents() -> dict[str, Any]:
    policy = load_json(
        ROOT / "experiments/iter239_repository_governance/policy.json"
    )
    after_state = load_json(
        ROOT
        / "experiments"
        / "iter239_repository_governance"
        / "proof"
        / "after_state.json"
    )
    ruleset = deepcopy(policy["request_body"])
    ruleset.update(
        {
            "id": guard.RULESET_ID,
            "source": guard.REPOSITORY,
            "source_type": "Repository",
            "current_user_can_bypass": "never",
        }
    )
    suite_ids = {
        29701167247: 7001,
        29701168051: 7002,
        29701305166: 7003,
    }
    run_times = {
        29701167247: ("2026-07-19T19:00:00Z", "2026-07-19T19:10:00Z"),
        29701168051: ("2026-07-19T19:15:00Z", "2026-07-19T19:25:00Z"),
        29701305166: ("2026-07-19T19:49:00Z", "2026-07-19T20:00:00Z"),
    }

    def run(
        run_id: int,
        *,
        event: str,
        head_sha: str,
        head_branch: str,
    ) -> dict[str, Any]:
        created_at, updated_at = run_times[run_id]
        return {
            "id": run_id,
            "workflow_id": guard.WORKFLOW_ID,
            "run_attempt": 1,
            "event": event,
            "status": "completed",
            "conclusion": "success",
            "head_sha": head_sha,
            "head_branch": head_branch,
            "path": guard.WORKFLOW_PATH,
            "check_suite_id": suite_ids[run_id],
            "created_at": created_at,
            "updated_at": updated_at,
        }

    check_rows: dict[str, list[dict[str, Any]]] = {
        guard.SEALED_TIP: [],
        guard.MERGE_COMMIT: [],
    }
    for name, _event, run_id, check_id, head_sha in guard.EXPECTED_CHECKS:
        _created_at, updated_at = run_times[run_id]
        check_rows[head_sha].append(
            {
                "id": check_id,
                "name": name,
                "head_sha": head_sha,
                "status": "completed",
                "conclusion": "success",
                "details_url": (
                    f"https://github.com/{guard.REPOSITORY}/actions/runs/"
                    f"{run_id}/job/{check_id}"
                ),
                "app": {
                    "id": guard.INTEGRATION_ID,
                    "slug": "github-actions",
                },
                "check_suite": {"id": suite_ids[run_id]},
                "started_at": (
                    "2026-07-19T19:01:00Z"
                    if run_id == 29701167247
                    else (
                        "2026-07-19T19:16:00Z"
                        if run_id == 29701168051
                        else "2026-07-19T19:50:00Z"
                    )
                ),
                "completed_at": updated_at,
            }
        )

    return {
        "pull_request_87": {
            "number": 87,
            "state": "closed",
            "merged": True,
            "merged_at": "2026-07-19T19:48:19Z",
            "merge_commit_sha": None,
            "draft": False,
            "head": {
                "sha": guard.SEALED_TIP,
                "ref": "agent/iter239-repository-governance",
                "repo": {"full_name": guard.REPOSITORY},
            },
            "base": {
                "sha": guard.PREDECESSOR_MASTER,
                "ref": "master",
                "repo": {"full_name": guard.REPOSITORY},
            },
        },
        "sealed_push_run": run(
            29701167247,
            event="push",
            head_sha=guard.SEALED_TIP,
            head_branch="agent/iter239-repository-governance",
        ),
        "sealed_pr_run": run(
            29701168051,
            event="pull_request",
            head_sha=guard.SEALED_TIP,
            head_branch="agent/iter239-repository-governance",
        ),
        "sealed_tip_check_runs": {
            "total_count": len(check_rows[guard.SEALED_TIP]),
            "check_runs": check_rows[guard.SEALED_TIP],
        },
        "merged_master_run": run(
            29701305166,
            event="push",
            head_sha=guard.MERGE_COMMIT,
            head_branch="master",
        ),
        "merged_master_check_runs": {
            "total_count": len(check_rows[guard.MERGE_COMMIT]),
            "check_runs": check_rows[guard.MERGE_COMMIT],
        },
        "master_branch": {
            "name": "master",
            "protected": True,
            "commit": {"sha": guard.MERGE_COMMIT},
        },
        "ruleset": ruleset,
        "effective_rules": after_state["projections"]["effective_rules"],
    }


def write_synthetic_receipt(tmp_path: Path) -> tuple[dict[str, Any], Path, Path]:
    receipt_path = tmp_path / "iter239_remote_acceptance.json"
    raw_root = tmp_path / "raw"
    raw_root.mkdir(mode=0o755)
    started_at = "2026-07-19T20:01:00Z"
    completed_at = started_at
    marker = capture_guard.build_attempt_marker(started_at=started_at)
    for instrument in marker["instruments"]:
        relative = instrument["path"]
        if relative not in guard.POST_CAPTURE_EVOLVABLE_PATHS:
            continue
        retained = guard.retained_capture_instrument_bytes(ROOT, relative)
        instrument["byte_count"] = len(retained)
        instrument["sha256"] = guard.sha256(retained)
    marker_raw = capture_guard.canonical_json(marker)
    marker_path = raw_root / capture_guard.ATTEMPT_FILENAME
    marker_path.write_bytes(marker_raw)
    marker_path.chmod(0o644)

    documents = synthetic_documents()
    inventory: list[dict[str, Any]] = []
    for index, (name, request_path, filename) in enumerate(guard.ENDPOINTS):
        raw = guard.canonical_json(documents[name])
        path = raw_root / filename
        path.write_bytes(raw)
        path.chmod(0o644)
        inventory.append(
            {
                "name": name,
                "method": "GET",
                "request_path": request_path,
                "http_status": 200,
                "response_date": started_at,
                "api_version_selected": guard.API_VERSION,
                "github_request_id": f"synthetic-{index:02d}",
                "etag": f'"synthetic-{index:02d}"',
                "link": None,
                "raw_body_path": (
                    "experiments/iter240_ground_truth_admission_design/"
                    f"proof/raw/iter239_remote_acceptance/{filename}"
                ),
                "raw_body_byte_count": len(raw),
                "raw_body_sha256": guard.sha256(raw),
            }
        )
    receipt = capture_guard.build_receipt(
        documents,
        inventory,
        started_at=started_at,
        completed_at=completed_at,
        marker_bytes=marker_raw,
    )
    write_receipt(receipt, receipt_path)
    receipt_path.chmod(0o644)
    return receipt, receipt_path, raw_root


def stage_receipt(tmp_path: Path) -> tuple[dict[str, Any], Path, Path]:
    return write_synthetic_receipt(tmp_path)


def write_receipt(receipt: dict[str, Any], receipt_path: Path) -> None:
    receipt_path.write_bytes(guard.canonical_json(receipt))


def mutate_raw(
    receipt: dict[str, Any],
    raw_root: Path,
    name: str,
    mutation: Callable[[Any], None],
) -> None:
    _, _, filename = next(row for row in guard.ENDPOINTS if row[0] == name)
    raw_path = raw_root / filename
    document = load_json(raw_path)
    mutation(document)
    raw = guard.canonical_json(document)
    raw_path.write_bytes(raw)
    entry = inventory_entry(receipt, name)
    entry["raw_body_byte_count"] = len(raw)
    entry["raw_body_sha256"] = guard.sha256(raw)


def duplicate_key_raw(
    receipt: dict[str, Any],
    raw_root: Path,
    name: str,
) -> None:
    _, _, filename = next(row for row in guard.ENDPOINTS if row[0] == name)
    raw_path = raw_root / filename
    original = raw_path.read_bytes().lstrip()
    assert original.startswith(b"{")
    raw = b'{"id":29701167247,' + original[1:]
    raw_path.write_bytes(raw)
    entry = inventory_entry(receipt, name)
    entry["raw_body_byte_count"] = len(raw)
    entry["raw_body_sha256"] = guard.sha256(raw)


def mutate_attempt_marker(
    receipt: dict[str, Any],
    raw_root: Path,
    mutation: Callable[[dict[str, Any]], None],
) -> None:
    marker_path = raw_root / capture_guard.ATTEMPT_FILENAME
    marker = load_json(marker_path)
    assert isinstance(marker, dict)
    mutation(marker)
    raw = guard.canonical_json(marker)
    marker_path.write_bytes(raw)
    binding = receipt["capture"]["attempt_marker"]
    binding["raw_body_byte_count"] = len(raw)
    binding["raw_body_sha256"] = guard.sha256(raw)


def mutate_named_check(
    document: Any,
    *,
    name: str,
    mutation: Callable[[dict[str, Any]], None],
) -> None:
    assert isinstance(document, dict)
    rows = document["check_runs"]
    matches = [
        row
        for row in rows
        if row["name"] == name
        and row["head_sha"] == guard.SEALED_TIP
        and row["app"]["id"] == guard.INTEGRATION_ID
    ]
    assert len(matches) == 1
    mutation(matches[0])


def apply_known_bad(
    case_id: str,
    receipt: dict[str, Any],
    raw_root: Path,
) -> None:
    if case_id == "raw_digest_mismatch":
        inventory_entry(receipt, "pull_request_87")["raw_body_sha256"] = "0" * 64
    elif case_id == "attempt_marker_digest_mismatch":
        receipt["capture"]["attempt_marker"]["raw_body_sha256"] = "0" * 64
    elif case_id == "attempt_marker_state_changed":
        mutate_attempt_marker(
            receipt,
            raw_root,
            lambda marker: marker.__setitem__("state", "completed"),
        )
    elif case_id == "capture_instrument_digest_mismatch":
        mutate_attempt_marker(
            receipt,
            raw_root,
            lambda marker: marker["instruments"][0].__setitem__(
                "sha256",
                "0" * 64,
            ),
        )
    elif case_id == "unexpected_raw_file":
        (raw_root / "unregistered.json").write_text("{}\n", encoding="utf-8")
    elif case_id == "oversized_raw_response":
        _, _, filename = next(
            row for row in guard.ENDPOINTS if row[0] == "pull_request_87"
        )
        raw_path = raw_root / filename
        raw = raw_path.read_bytes()
        raw += b" " * (guard.MAX_RESPONSE_BYTES + 1 - len(raw))
        raw_path.write_bytes(raw)
        entry = inventory_entry(receipt, "pull_request_87")
        entry["raw_body_byte_count"] = len(raw)
        entry["raw_body_sha256"] = guard.sha256(raw)
    elif case_id == "duplicate_json_key":
        duplicate_key_raw(receipt, raw_root, "sealed_push_run")
    elif case_id == "write_count_nonzero":
        receipt["request_counts"]["POST"] = 1
    elif case_id == "pagination_link_present":
        inventory_entry(receipt, "effective_rules")["link"] = (
            '<https://api.github.com/next>; rel="next"'
        )
    elif case_id == "numeric_http_status_float":
        inventory_entry(receipt, "pull_request_87")["http_status"] = 200.0
    elif case_id == "pull_request_not_merged":
        mutate_raw(
            receipt,
            raw_root,
            "pull_request_87",
            lambda document: document.__setitem__("merged", False),
        )
    elif case_id == "sealed_run_second_attempt":
        mutate_raw(
            receipt,
            raw_root,
            "sealed_push_run",
            lambda document: document.__setitem__("run_attempt", 2),
        )
    elif case_id == "workflow_run_id_float":
        mutate_raw(
            receipt,
            raw_root,
            "sealed_push_run",
            lambda document: document.__setitem__(
                "id",
                float(document["id"]),
            ),
        )
    elif case_id == "required_check_wrong_app":
        mutate_raw(
            receipt,
            raw_root,
            "sealed_tip_check_runs",
            lambda document: mutate_named_check(
                document,
                name="verify push py3.11",
                mutation=lambda row: row["app"].__setitem__("id", 1),
            ),
        )
    elif case_id == "required_check_duplicated":
        def duplicate(document: Any) -> None:
            assert isinstance(document, dict)
            rows = document["check_runs"]
            matches = [
                row
                for row in rows
                if row["name"] == "verify push py3.11"
                and row["head_sha"] == guard.SEALED_TIP
                and row["app"]["id"] == guard.INTEGRATION_ID
            ]
            assert len(matches) == 1
            rows.append(deepcopy(matches[0]))
            document["total_count"] = len(rows)

        mutate_raw(receipt, raw_root, "sealed_tip_check_runs", duplicate)
    elif case_id == "required_check_suite_mismatch":
        mutate_raw(
            receipt,
            raw_root,
            "sealed_tip_check_runs",
            lambda document: mutate_named_check(
                document,
                name="verify push py3.11",
                mutation=lambda row: row["check_suite"].__setitem__("id", 9999),
            ),
        )
    elif case_id == "sealed_run_completed_after_merge":
        mutate_raw(
            receipt,
            raw_root,
            "sealed_push_run",
            lambda document: document.__setitem__(
                "updated_at",
                "2026-07-19T19:50:00Z",
            ),
        )
    elif case_id == "merged_run_stale_head":
        mutate_raw(
            receipt,
            raw_root,
            "merged_master_run",
            lambda document: document.__setitem__("head_sha", guard.SEALED_TIP),
        )
    elif case_id == "master_unprotected":
        mutate_raw(
            receipt,
            raw_root,
            "master_branch",
            lambda document: document.__setitem__("protected", False),
        )
    elif case_id == "ruleset_bypass_enabled":
        mutate_raw(
            receipt,
            raw_root,
            "ruleset",
            lambda document: document.__setitem__(
                "current_user_can_bypass",
                "always",
            ),
        )
    elif case_id == "effective_rule_missing":
        def remove_rule(document: Any) -> None:
            assert isinstance(document, list)
            assert document
            document.pop()

        mutate_raw(receipt, raw_root, "effective_rules", remove_rule)
    elif case_id == "independent_review_overclaim":
        receipt["conclusion"]["independent_review"] = "supported"
    elif case_id == "limitation_weakened":
        receipt["limitations"][-1] = "Engineering closure is sufficient."
    elif case_id == "response_predates_merged_ci":
        inventory_entry(receipt, "pull_request_87")["response_date"] = (
            "2026-07-19T19:00:00Z"
        )
    elif case_id == "duplicate_request_id":
        first = inventory_entry(receipt, "pull_request_87")["github_request_id"]
        inventory_entry(receipt, "sealed_push_run")["github_request_id"] = first
    elif case_id == "response_dates_out_of_order":
        inventory_entry(receipt, "sealed_push_run")["response_date"] = (
            "2026-07-19T20:00:00Z"
        )
    else:  # pragma: no cover - catalogue equality makes this unreachable
        raise AssertionError(f"unimplemented known-bad case: {case_id}")


def test_retained_remote_acceptance_passes_offline() -> None:
    assert guard.validate() == []


def test_evolved_governance_validator_keeps_exact_capture_provenance(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    relative = "scripts/validate_iter239_repository_governance.py"
    assert guard.POST_CAPTURE_EVOLVABLE_PATHS == {
        "scripts/validate_iter239_remote_acceptance.py",
        relative,
    }
    historical = guard._git(
        ROOT,
        "show",
        f"{guard.CAPTURE_EVIDENCE_COMMIT}:{relative}",
    )
    assert (ROOT / relative).read_bytes() != historical
    assert guard.retained_capture_instrument_bytes(ROOT, relative) == historical

    original = guard._git

    def corrupted(root: Path, *arguments: str) -> bytes:
        payload = original(root, *arguments)
        if arguments == (
            "show",
            f"{guard.CAPTURE_EVIDENCE_COMMIT}:{relative}",
        ):
            return payload + b"retained drift\n"
        return payload

    monkeypatch.setattr(guard, "_git", corrupted)
    receipt = load_json(RECEIPT)
    failures = guard.attempt_failures(receipt, root=ROOT, raw_root=RAW_ROOT)
    assert f"capture instrument byte binding differs: {relative}" in failures


def test_synthetic_known_good_receipt_passes_before_live_capture(
    tmp_path: Path,
) -> None:
    _receipt, receipt_path, raw_root = write_synthetic_receipt(tmp_path)
    assert guard.validate(
        receipt_path=receipt_path,
        raw_root=raw_root,
        check_repository=False,
    ) == []


def test_capture_performs_each_fixed_get_exactly_once(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    connection = configure_fake_capture(
        monkeypatch,
        tmp_path,
        [
            FakeResponse(index=index)
            for index, _endpoint in enumerate(capture_guard.ENDPOINTS)
        ],
    )
    capture_guard.capture()
    observed = [(method, path) for method, path, _headers in connection.requests]
    expected = [
        ("GET", request_path)
        for _name, request_path, _filename in capture_guard.ENDPOINTS
    ]
    assert observed == expected
    assert connection.responses == []
    assert connection.closed is True
    assert capture_guard.RECEIPT.is_file()
    assert sorted(path.name for path in capture_guard.RAW_ROOT.iterdir()) == sorted(
        [
            capture_guard.ATTEMPT_FILENAME,
            *[
                filename
                for _name, _request_path, filename in capture_guard.ENDPOINTS
            ],
        ]
    )


def test_capture_does_not_retry_failed_get(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    connection = configure_fake_capture(
        monkeypatch,
        tmp_path,
        [FakeResponse(index=0), FakeResponse(index=1, status=503)],
    )
    with pytest.raises(capture_guard.CaptureError, match="without retry"):
        capture_guard.capture()
    assert len(connection.requests) == 2
    assert connection.closed is True
    assert not capture_guard.RECEIPT.exists()
    assert sorted(path.name for path in capture_guard.RAW_ROOT.iterdir()) == [
        capture_guard.ATTEMPT_FILENAME
    ]
    with pytest.raises(capture_guard.CaptureError, match="refusing any rerun"):
        capture_guard.require_unattempted()


def test_semantic_veto_publishes_no_acceptance_receipt(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    connection = configure_fake_capture(
        monkeypatch,
        tmp_path,
        [
            FakeResponse(index=index)
            for index, _endpoint in enumerate(capture_guard.ENDPOINTS)
        ],
    )

    def reject(*_args: Any, **_kwargs: Any) -> None:
        raise capture_guard.CaptureError("synthetic semantic veto")

    monkeypatch.setattr(capture_guard, "validate_staged_receipt", reject)
    with pytest.raises(capture_guard.CaptureError, match="semantic veto"):
        capture_guard.capture()
    assert len(connection.requests) == len(capture_guard.ENDPOINTS)
    assert not capture_guard.RECEIPT.exists()
    assert sorted(path.name for path in capture_guard.RAW_ROOT.iterdir()) == [
        capture_guard.ATTEMPT_FILENAME
    ]


def test_dangling_output_symlink_blocks_capture(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    raw_root = tmp_path / "raw"
    raw_root.symlink_to(tmp_path / "absent-target", target_is_directory=True)
    monkeypatch.setattr(capture_guard, "RAW_ROOT", raw_root)
    monkeypatch.setattr(capture_guard, "RECEIPT", tmp_path / "receipt.json")
    with pytest.raises(capture_guard.CaptureError, match="refusing any rerun"):
        capture_guard.require_unattempted()


def test_exact_source_loaders_ignore_timestamp_valid_stale_bytecode(
    tmp_path: Path,
) -> None:
    source_path = tmp_path / "stale_fixture.py"
    source_path.write_text("VALUE = 'cached'\n", encoding="utf-8")
    source_path.chmod(0o644)
    metadata = source_path.stat()
    py_compile.compile(str(source_path), doraise=True)
    source_path.write_text("VALUE = 'source'\n", encoding="utf-8")
    os.utime(
        source_path,
        ns=(metadata.st_atime_ns, metadata.st_mtime_ns),
    )

    spec = importlib.util.spec_from_file_location(
        "iter239_conventional_stale_fixture",
        source_path,
    )
    assert spec is not None
    assert spec.loader is not None
    conventional = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(conventional)
    assert conventional.VALUE == "cached"

    validator_loaded = guard.load_module(
        source_path,
        "iter239_validator_exact_source_fixture",
    )
    capture_loaded = capture_guard.load_exact_source_module(
        source_path,
        "iter239_capture_exact_source_fixture",
    )
    assert validator_loaded.VALUE == "source"
    assert capture_loaded.VALUE == "source"
    expected = guard.sha256(source_path.read_bytes())
    assert validator_loaded.__exact_source_sha256__ == expected
    assert capture_loaded.__exact_source_sha256__ == expected


def test_rest_omitted_or_null_merge_sha_is_not_used_as_merge_authority() -> None:
    pull = load_json(RAW_ROOT / "pull_request_87.json")
    assert pull.get("merge_commit_sha") is None
    assert guard.validate() == []


@pytest.mark.parametrize("case_id", sorted(EXPECTED_ERRORS))
def test_every_known_bad_receipt_is_rejected(
    case_id: str,
    tmp_path: Path,
) -> None:
    receipt, receipt_path, raw_root = stage_receipt(tmp_path)
    apply_known_bad(case_id, receipt, raw_root)
    write_receipt(receipt, receipt_path)
    failures = guard.validate(
        receipt_path=receipt_path,
        raw_root=raw_root,
        check_repository=False,
    )
    assert any(EXPECTED_ERRORS[case_id] in failure for failure in failures), failures


def test_known_bad_catalogue_is_canonical_and_fully_exercised() -> None:
    raw = CATALOGUE.read_bytes()
    catalogue = guard.strict_json(raw, label="known-bad catalogue")
    assert raw == guard.canonical_json(catalogue)
    assert catalogue["schema_version"] == (
        "telos.iter239.remote_acceptance.known_bad.v1"
    )
    rows = catalogue["cases"]
    observed = {row["id"]: row["expected_error"] for row in rows}
    assert len(observed) == len(rows)
    assert observed == EXPECTED_ERRORS
