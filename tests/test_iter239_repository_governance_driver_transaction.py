"""Deterministic contract tests for iter239's transaction/observation layer.

The transport-core tests cover request bounds.  This file fixes the missing
orchestration contract before live use:

* pure ``pagination_record``, ``project_ruleset``, ``project_check_rows``,
  ``assert_before_preconditions``, ``build_dispatch_attempt``,
  ``classify_abort``, and ``merge_operational_phases`` helpers;
* ``run_governance_transaction`` with injected captures, writer, projector,
  and clock, returning the documents it retained;
* a nonblocking ``repository_transaction_lock`` held across the transaction;
* explicit ``recover=True`` for every restart path.

The injection points are deliberate.  They let these tests prove ordering and
recovery without credentials, remote state, timing, or monkeypatched sockets.
"""

from __future__ import annotations

from contextlib import nullcontext
from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any, Callable

import pytest


ROOT = Path(__file__).resolve().parents[1]
SOURCE = "a" * 40
OPERATIONAL_HEAD = "b" * 40
DISPATCH_STAGE = ".post_dispatch_stage.json"


def load_driver():
    path = ROOT / "scripts/configure_repository_governance.py"
    spec = importlib.util.spec_from_file_location(
        "configure_repository_governance_transaction_contract",
        path,
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def load_fixtures():
    path = ROOT / "tests/test_iter239_repository_governance.py"
    spec = importlib.util.spec_from_file_location(
        "iter239_repository_governance_fixture_builders",
        path,
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class SequenceClock:
    def __init__(self) -> None:
        self._values = iter(
            [
                "2026-07-19T12:00:00Z",
                "2026-07-19T12:00:01Z",
                "2026-07-19T12:00:02Z",
                "2026-07-19T12:00:03Z",
                "2026-07-19T12:00:04Z",
                "2026-07-19T12:00:05Z",
                "2026-07-19T12:00:06Z",
                "2026-07-19T12:00:07Z",
            ]
        )

    def __call__(self) -> str:
        return next(self._values)


class RecordingClient:
    def __init__(
        self,
        *,
        post_projection: dict[str, Any] | None = None,
        post_error: BaseException | None = None,
        on_post: Callable[[], None] | None = None,
    ) -> None:
        self.post_projection = post_projection
        self.post_error = post_error
        self.on_post = on_post
        self.post_calls = 0
        self.counts = {
            method: 0
            for method in ("DELETE", "GET", "PATCH", "POST", "PUT")
        }
        self.semantic_counts = {
            operation: 0
            for operation in (
                "branch_delete",
                "branch_update",
                "collaborator_invite",
                "collaborator_role_change",
                "force_push",
                "publication",
                "release",
                "run_delete",
                "visibility_change",
                "workflow_delete",
                "workflow_disable",
                "workflow_dispatch",
                "workflow_enable",
                "workflow_rerun",
            )
        }

    def record_gets(self, count: int) -> None:
        self.counts["GET"] += count

    def post_ruleset(
        self,
        _document: dict[str, Any],
    ) -> tuple[int, dict[str, Any], bytes]:
        self.post_calls += 1
        self.counts["POST"] += 1
        if self.on_post is not None:
            self.on_post()
        if self.post_error is not None:
            raise self.post_error
        assert self.post_projection is not None
        return (
            201,
            deepcopy(self.post_projection),
            json.dumps(self.post_projection).encode("utf-8"),
        )

    def receipt_counts(self) -> dict[str, int]:
        return {
            **self.counts,
            **self.semantic_counts,
        }


class CaptureScript:
    def __init__(
        self,
        *,
        before: dict[str, Any],
        after: dict[str, Any],
    ) -> None:
        self.before = before
        self.after = after
        self.before_calls = 0
        self.after_calls = 0

    def capture_before(
        self,
        client: RecordingClient,
        **_context: Any,
    ) -> dict[str, Any]:
        self.before_calls += 1
        client.record_gets(self.before["request_counts"]["GET"])
        return deepcopy(self.before)

    def capture_after(
        self,
        client: RecordingClient,
        **_context: Any,
    ) -> dict[str, Any]:
        self.after_calls += 1
        client.record_gets(self.after["request_counts"]["GET"])
        return deepcopy(self.after)


class RecordingWriter:
    def __init__(self, driver) -> None:
        self.driver = driver
        self.names: list[str] = []
        self.before_write: Callable[[Path], None] | None = None

    def __call__(self, path: Path, document: dict[str, Any]) -> bytes:
        if self.before_write is not None:
            self.before_write(path)
        self.names.append(path.name)
        return self.driver.materialize_once(path, document)


def transaction_inputs(driver):
    fixtures = load_fixtures()
    policy, policy_raw, evidence = fixtures.good_bundle(driver.guard)
    before, _before_raw = evidence["before_state"]
    after, _after_raw = evidence["after_state"]
    named = after["projections"]["named_ruleset"]
    return fixtures, policy, policy_raw, before, after, named


def invoke_transaction(
    driver,
    *,
    client: RecordingClient,
    proof_root: Path,
    policy: dict[str, Any],
    policy_raw: bytes,
    captures: CaptureScript,
    writer: RecordingWriter,
    recover: bool,
) -> dict[str, Any]:
    return driver.run_governance_transaction(
        client,
        proof_root=proof_root,
        policy=policy,
        policy_raw=policy_raw,
        source_commit=SOURCE,
        recover=recover,
        capture_before=captures.capture_before,
        capture_after=captures.capture_after,
        write_document=writer,
        project_ruleset=lambda value: deepcopy(value),
        clock=SequenceClock(),
    )


def load_retained(driver, path: Path) -> tuple[dict[str, Any], bytes]:
    return driver.guard.load_canonical_json(path)


def test_pagination_record_is_exact_and_rejects_partial_capture() -> None:
    driver = load_driver()
    projection = [{"id": 1}, {"id": 2}, {"id": 3}]
    record = driver.pagination_record(
        projection,
        complete=True,
        http_statuses=[200, 200],
        page_count=2,
        request_count=2,
    )
    assert record == {
        "complete": True,
        "http_statuses": [200, 200],
        "item_count": 3,
        "page_count": 2,
        "projection_sha256": driver.guard.canonical_sha256(projection),
        "request_count": 2,
    }
    with pytest.raises(driver.GovernanceMutationError, match="complete"):
        driver.pagination_record(
            projection,
            complete=False,
            http_statuses=[200],
            page_count=1,
            request_count=1,
        )
    with pytest.raises(driver.GovernanceMutationError, match="status"):
        driver.pagination_record(
            projection,
            complete=True,
            http_statuses=[200],
            page_count=2,
            request_count=2,
        )


def test_ruleset_projection_preserves_server_metadata_and_normalization() -> None:
    driver = load_driver()
    fixtures, policy, _policy_raw, _before, _after, expected = transaction_inputs(
        driver
    )
    del fixtures
    raw = {
        "id": expected["id"],
        "name": policy["request_body"]["name"],
        "target": policy["request_body"]["target"],
        "source": expected["source"],
        "source_type": expected["source_type"],
        "enforcement": policy["request_body"]["enforcement"],
        "conditions": deepcopy(policy["request_body"]["conditions"]),
        "rules": deepcopy(expected["server_policy"]["rules"]),
        "created_at": expected["server_metadata"]["created_at"],
        "updated_at": expected["server_metadata"]["updated_at"],
        "node_id": expected["server_metadata"]["node_id"],
        "_links": deepcopy(expected["server_metadata"]["links"]),
        "current_user_can_bypass": "never",
    }
    assert driver.project_ruleset(raw) == expected
    raw["current_user_can_bypass"] = "always"
    with pytest.raises(driver.GovernanceMutationError, match="bypass"):
        driver.project_ruleset(raw)


def test_check_projection_binds_suite_run_event_attempt_and_app() -> None:
    driver = load_driver()
    head = "b" * 40
    raw = [
        {
            "app": {"id": driver.guard.INTEGRATION_ID},
            "check_suite": {"id": 5000},
            "conclusion": "success",
            "head_sha": head,
            "id": 3001,
            "name": "verify pull_request py3.11",
            "status": "completed",
        },
        {
            "app": {"id": driver.guard.INTEGRATION_ID},
            "check_suite": {"id": 5000},
            "conclusion": "success",
            "head_sha": head,
            "id": 3002,
            "name": "verify pull_request py3.12",
            "status": "completed",
        },
    ]
    run_metadata = {
        5000: {
            "attempt": 1,
            "event": "pull_request",
            "workflow_id": driver.guard.WORKFLOW_ID,
            "workflow_path": driver.guard.WORKFLOW_RELATIVE.as_posix(),
            "workflow_run_id": 1000,
        }
    }
    projected = driver.project_check_rows(
        raw,
        workflow_runs_by_suite_id=run_metadata,
    )
    assert [row["name"] for row in projected] == [
        "verify pull_request py3.11",
        "verify pull_request py3.12",
    ]
    assert all(row["attempt"] == 1 for row in projected)
    assert all(row["event"] == "pull_request" for row in projected)
    assert all(row["head_sha"] == head for row in projected)
    assert all(
        row["integration_id"] == driver.guard.INTEGRATION_ID
        for row in projected
    )
    duplicate = deepcopy(raw)
    duplicate[1]["name"] = duplicate[0]["name"]
    with pytest.raises(driver.GovernanceMutationError, match="duplicate"):
        driver.project_check_rows(
            duplicate,
            workflow_runs_by_suite_id=run_metadata,
        )


def test_precondition_assertion_is_pure_and_fails_on_drift() -> None:
    driver = load_driver()
    _fixtures, _policy, policy_raw, before, _after, _named = transaction_inputs(
        driver
    )
    digest = driver.guard.sha256_bytes(policy_raw)
    original = deepcopy(before)
    driver.assert_before_preconditions(before, policy_sha256=digest)
    assert before == original
    drift = deepcopy(before)
    drift["projections"]["repository"]["visibility"] = "private"
    with pytest.raises(driver.GovernanceMutationError, match="precondition"):
        driver.assert_before_preconditions(drift, policy_sha256=digest)


def test_abort_classification_exactly_covers_registered_outcomes() -> None:
    driver = load_driver()
    expected = {
        "ambiguous_unresolved": {
            "classification": "failed",
            "phase": "postcondition",
            "required_post_count": 1,
        },
        "dispatch_not_attempted": {
            "classification": "inconclusive",
            "phase": "dispatch",
            "required_post_count": 0,
        },
        "mismatched_created_ruleset": {
            "classification": "failed",
            "phase": "postcondition",
            "required_post_count": 1,
        },
        "postcondition_drift": {
            "classification": "inconclusive",
            "phase": "postcondition",
            "required_post_count": 1,
        },
        "postcondition_unobserved": {
            "classification": "inconclusive",
            "phase": "postcondition",
            "required_post_count": 1,
        },
        "precondition_drift": {
            "classification": "inconclusive",
            "phase": "precondition",
            "required_post_count": 0,
        },
    }
    assert {
        reason: driver.classify_abort(reason)
        for reasons in driver.guard.ABORT_OUTCOMES.values()
        for reason in reasons
    } == expected
    with pytest.raises(driver.GovernanceMutationError, match="reason"):
        driver.classify_abort("invented")


def test_dispatch_attempt_is_exactly_bound_to_fsynced_intent() -> None:
    driver = load_driver()
    _fixtures, _policy, _policy_raw, _before, _after, _named = transaction_inputs(
        driver
    )
    intent_raw = b'{"canonical":"intent"}\n'
    dispatch = driver.build_dispatch_attempt(
        source_commit=SOURCE,
        mutation_intent_sha256=driver.guard.sha256_bytes(intent_raw),
        consumed_at="2026-07-19T12:00:02Z",
    )
    assert driver.guard.dispatch_attempt_failures(
        dispatch,
        label="dispatch",
        source_commit=SOURCE,
        mutation_intent_sha256=driver.guard.sha256_bytes(intent_raw),
    ) == []


def test_transaction_fsyncs_before_intent_and_dispatch_before_post(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    driver = load_driver()
    monkeypatch.setattr(driver, "ROOT", tmp_path)
    _fixtures, policy, policy_raw, before, after, named = transaction_inputs(driver)
    proof_root = tmp_path / "proof"
    captures = CaptureScript(before=before, after=after)
    writer = RecordingWriter(driver)

    def before_post() -> None:
        assert writer.names[:3] == [
            "before_state.json",
            "mutation_intent.json",
            DISPATCH_STAGE,
        ]
        assert (proof_root / "before_state.json").is_file()
        assert (proof_root / "mutation_intent.json").is_file()
        assert (proof_root / DISPATCH_STAGE).is_file()

    client = RecordingClient(
        post_projection=named,
        on_post=before_post,
    )
    receipt_write_observed_stage = False

    def before_write(path: Path) -> None:
        nonlocal receipt_write_observed_stage
        if path.name == "mutation_receipt.json":
            receipt_write_observed_stage = (proof_root / DISPATCH_STAGE).is_file()

    writer.before_write = before_write
    invoke_transaction(
        driver,
        client=client,
        proof_root=proof_root,
        policy=policy,
        policy_raw=policy_raw,
        captures=captures,
        writer=writer,
        recover=False,
    )
    assert client.post_calls == 1
    assert receipt_write_observed_stage is True
    assert not (proof_root / DISPATCH_STAGE).exists()
    assert writer.names == [
        "before_state.json",
        "mutation_intent.json",
        DISPATCH_STAGE,
        "after_state.json",
        "mutation_receipt.json",
    ]


def test_applied_transaction_artifacts_are_validator_compatible(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    driver = load_driver()
    monkeypatch.setattr(driver, "ROOT", tmp_path)
    _fixtures, policy, policy_raw, before, after, named = transaction_inputs(driver)
    proof_root = tmp_path / "proof"
    captures = CaptureScript(before=before, after=after)
    writer = RecordingWriter(driver)
    client = RecordingClient(post_projection=named)
    invoke_transaction(
        driver,
        client=client,
        proof_root=proof_root,
        policy=policy,
        policy_raw=policy_raw,
        captures=captures,
        writer=writer,
        recover=False,
    )

    policy_digest = driver.guard.sha256_bytes(policy_raw)
    retained_before, before_raw = load_retained(
        driver,
        proof_root / "before_state.json",
    )
    intent, intent_raw = load_retained(
        driver,
        proof_root / "mutation_intent.json",
    )
    retained_after, after_raw = load_retained(
        driver,
        proof_root / "after_state.json",
    )
    receipt, _receipt_raw = load_retained(
        driver,
        proof_root / "mutation_receipt.json",
    )
    assert driver.guard.before_state_failures(
        retained_before,
        policy_sha256=policy_digest,
    ) == []
    assert driver.guard.mutation_intent_failures(
        intent,
        policy_sha256=policy_digest,
        before=retained_before,
        before_raw=before_raw,
        policy=policy,
    ) == []
    assert driver.guard.after_state_failures(
        retained_after,
        policy_sha256=policy_digest,
        before=retained_before,
        policy=policy,
    ) == []
    assert driver.guard.mutation_receipt_failures(
        receipt,
        policy_sha256=policy_digest,
        before=retained_before,
        before_raw=before_raw,
        intent=intent,
        intent_raw=intent_raw,
        after=retained_after,
        after_raw=after_raw,
        policy=policy,
    ) == []


@pytest.mark.parametrize("http_status", [None, 201, 202, 302, 408, 429, 500])
def test_ambiguous_post_uses_one_after_capture_and_never_retries(
    http_status: int | None,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    driver = load_driver()
    monkeypatch.setattr(driver, "ROOT", tmp_path)
    _fixtures, policy, policy_raw, before, after, _named = transaction_inputs(driver)
    proof_root = tmp_path / "proof"
    captures = CaptureScript(before=before, after=after)
    writer = RecordingWriter(driver)
    client = RecordingClient(
        post_error=driver.AmbiguousPostError(
            "ambiguous",
            http_status=http_status,
        )
    )
    invoke_transaction(
        driver,
        client=client,
        proof_root=proof_root,
        policy=policy,
        policy_raw=policy_raw,
        captures=captures,
        writer=writer,
        recover=False,
    )
    receipt, _raw = load_retained(
        driver,
        proof_root / "mutation_receipt.json",
    )
    assert client.post_calls == 1
    assert captures.after_calls == 1
    assert receipt["outcome"] == "ambiguous_applied"
    expected_classification = (
        "ambiguous_transport"
        if http_status is None
        else "ambiguous_http_response"
    )
    assert receipt["post_response"] == {
        "classification": expected_classification,
        "http_status": http_status,
        "projection": None,
        "projection_sha256": None,
    }


def test_precondition_drift_retains_abort_and_never_dispatches(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    driver = load_driver()
    monkeypatch.setattr(driver, "ROOT", tmp_path)
    _fixtures, policy, policy_raw, before, after, named = transaction_inputs(driver)
    before["projections"]["repository"]["visibility"] = "private"
    captures = CaptureScript(before=before, after=after)
    client = RecordingClient(post_projection=named)
    writer = RecordingWriter(driver)
    result = invoke_transaction(
        driver,
        client=client,
        proof_root=tmp_path / "proof",
        policy=policy,
        policy_raw=policy_raw,
        captures=captures,
        writer=writer,
        recover=False,
    )
    assert result["abort_record"]["classification"] == "inconclusive"
    assert result["abort_record"]["reason_code"] == "precondition_drift"
    assert result["abort_record"]["request_counts"]["POST"] == 0
    assert result["abort_record"]["dispatch_attempt"] is None
    assert client.post_calls == 0
    assert captures.after_calls == 0
    assert not (tmp_path / "proof/mutation_intent.json").exists()


def retain_restart_inputs(
    driver,
    *,
    proof_root: Path,
    before: dict[str, Any],
    policy: dict[str, Any],
    policy_raw: bytes,
    with_dispatch: bool,
) -> tuple[bytes, bytes]:
    before_raw = driver.materialize_once(
        proof_root / "before_state.json",
        before,
    )
    intent = load_fixtures().good_intent(
        driver.guard,
        policy,
        driver.guard.sha256_bytes(policy_raw),
        before_raw,
    )
    intent_raw = driver.materialize_once(
        proof_root / "mutation_intent.json",
        intent,
    )
    if with_dispatch:
        dispatch = driver.build_dispatch_attempt(
            source_commit=SOURCE,
            mutation_intent_sha256=driver.guard.sha256_bytes(intent_raw),
            consumed_at="2026-07-19T12:00:02Z",
        )
        driver.materialize_once(
            proof_root / DISPATCH_STAGE,
            dispatch,
        )
    return before_raw, intent_raw


def test_recovery_without_dispatch_never_posts_or_claims_acceptance(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    driver = load_driver()
    monkeypatch.setattr(driver, "ROOT", tmp_path)
    _fixtures, policy, policy_raw, before, after, named = transaction_inputs(driver)
    proof_root = tmp_path / "proof"
    before_raw, intent_raw = retain_restart_inputs(
        driver,
        proof_root=proof_root,
        before=before,
        policy=policy,
        policy_raw=policy_raw,
        with_dispatch=False,
    )
    captures = CaptureScript(before=before, after=after)
    client = RecordingClient(post_projection=named)
    result = invoke_transaction(
        driver,
        client=client,
        proof_root=proof_root,
        policy=policy,
        policy_raw=policy_raw,
        captures=captures,
        writer=RecordingWriter(driver),
        recover=True,
    )
    assert client.post_calls == 0
    assert captures.before_calls == 0
    assert captures.after_calls == 0
    assert result["abort_record"]["reason_code"] == "dispatch_not_attempted"
    assert result["abort_record"]["dispatch_attempt"] is None
    assert result["abort_record"]["request_counts"]["POST"] == 0
    assert not (proof_root / "mutation_receipt.json").exists()
    assert (proof_root / "before_state.json").read_bytes() == before_raw
    assert (proof_root / "mutation_intent.json").read_bytes() == intent_raw


def test_recovery_with_dispatch_is_diagnostic_and_never_accepted(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    driver = load_driver()
    monkeypatch.setattr(driver, "ROOT", tmp_path)
    _fixtures, policy, policy_raw, before, after, named = transaction_inputs(driver)
    proof_root = tmp_path / "proof"
    before_raw, intent_raw = retain_restart_inputs(
        driver,
        proof_root=proof_root,
        before=before,
        policy=policy,
        policy_raw=policy_raw,
        with_dispatch=True,
    )
    stage_raw = (proof_root / DISPATCH_STAGE).read_bytes()
    captures = CaptureScript(before=before, after=after)
    client = RecordingClient(post_projection=named)
    writer = RecordingWriter(driver)
    with pytest.raises(
        driver.GovernanceMutationError,
        match="incident|restart|cannot accept",
    ):
        invoke_transaction(
            driver,
            client=client,
            proof_root=proof_root,
            policy=policy,
            policy_raw=policy_raw,
            captures=captures,
            writer=writer,
            recover=True,
        )
    assert client.post_calls == 0
    assert captures.before_calls == 0
    assert captures.after_calls == 1
    assert not (proof_root / "mutation_receipt.json").exists()
    assert not (proof_root / "after_state.json").exists()
    assert not (proof_root / "abort_record.json").exists()
    assert (proof_root / DISPATCH_STAGE).read_bytes() == stage_raw
    assert (proof_root / "before_state.json").read_bytes() == before_raw
    assert (proof_root / "mutation_intent.json").read_bytes() == intent_raw
    assert writer.names == []


@pytest.mark.parametrize(
    "existing",
    [
        ("before_state",),
        ("mutation_intent",),
        ("before_state", "after_state"),
        ("mutation_intent", "dispatch"),
        ("before_state", "mutation_intent", "mutation_receipt"),
    ],
)
def test_partial_evidence_never_triggers_another_post(
    existing: tuple[str, ...],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    driver = load_driver()
    monkeypatch.setattr(driver, "ROOT", tmp_path)
    fixtures, policy, policy_raw, before, after, named = transaction_inputs(driver)
    proof_root = tmp_path / "proof"
    proof_root.mkdir()
    documents = {
        "before_state": before,
        "after_state": after,
        "mutation_intent": fixtures.good_intent(
            driver.guard,
            policy,
            driver.guard.sha256_bytes(policy_raw),
            driver.guard.canonical_json_bytes(before),
        ),
        "mutation_receipt": {"partial": True},
        "dispatch": {"partial": True},
    }
    paths = {
        "before_state": proof_root / "before_state.json",
        "after_state": proof_root / "after_state.json",
        "mutation_intent": proof_root / "mutation_intent.json",
        "mutation_receipt": proof_root / "mutation_receipt.json",
        "dispatch": proof_root / DISPATCH_STAGE,
    }
    originals: dict[Path, bytes] = {}
    for label in existing:
        raw = driver.guard.canonical_json_bytes(documents[label])
        paths[label].write_bytes(raw)
        originals[paths[label]] = raw
    captures = CaptureScript(before=before, after=after)
    client = RecordingClient(post_projection=named)
    with pytest.raises(driver.GovernanceMutationError, match="partial|recover"):
        invoke_transaction(
            driver,
            client=client,
            proof_root=proof_root,
            policy=policy,
            policy_raw=policy_raw,
            captures=captures,
            writer=RecordingWriter(driver),
            recover=False,
        )
    assert client.post_calls == 0
    assert captures.before_calls == 0
    assert captures.after_calls == 0
    for path, raw in originals.items():
        assert path.read_bytes() == raw


def test_transaction_lock_is_nonblocking_and_released(
    tmp_path: Path,
) -> None:
    driver = load_driver()
    proof_root = tmp_path / "proof"
    with driver.repository_transaction_lock(proof_root):
        with pytest.raises(driver.GovernanceMutationError, match="active"):
            with driver.repository_transaction_lock(proof_root):
                pytest.fail("a concurrent transaction acquired the same lock")
    with driver.repository_transaction_lock(proof_root):
        pass


def test_operational_merge_requires_fresh_same_identity_transition() -> None:
    driver = load_driver()
    fixtures = load_fixtures()
    policy, policy_raw = fixtures.load_policy(driver.guard)
    digest = driver.guard.sha256_bytes(policy_raw)
    expected = fixtures.good_operational(driver.guard, policy, digest)
    merged = driver.merge_operational_phases(
        pending=deepcopy(expected["pending"]),
        success=deepcopy(expected["success"]),
        policy_sha256=digest,
        pull_request=deepcopy(expected["pull_request"]),
        ruleset_source_commit=SOURCE,
    )
    assert merged == expected
    after_state = {
        "projections": {
            key: deepcopy(expected["pending"][key])
            for key in (
                "branch",
                "effective_rules",
                "named_ruleset",
                "rulesets",
            )
        }
    }
    assert driver.guard.operational_check_failures(
        merged,
        policy_sha256=digest,
        source_commit=SOURCE,
        expected_pull_request_number=87,
        after_state=after_state,
    ) == []

    stale = deepcopy(expected["success"])
    stale["observed_at"] = expected["pending"]["observed_at"]
    with pytest.raises(driver.GovernanceMutationError, match="fresh|precede"):
        driver.merge_operational_phases(
            pending=deepcopy(expected["pending"]),
            success=stale,
            policy_sha256=digest,
            pull_request=deepcopy(expected["pull_request"]),
            ruleset_source_commit=SOURCE,
        )

    substituted = deepcopy(expected["success"])
    substituted["checks"][0]["check_run_id"] += 1
    with pytest.raises(driver.GovernanceMutationError, match="same check"):
        driver.merge_operational_phases(
            pending=deepcopy(expected["pending"]),
            success=substituted,
            policy_sha256=digest,
            pull_request=deepcopy(expected["pull_request"]),
            ruleset_source_commit=SOURCE,
        )

    other_head = deepcopy(expected["success"])
    other_head["source_commit"] = "c" * 40
    other_head["pull_request"]["head_sha"] = "c" * 40
    for row in other_head["checks"]:
        row["head_sha"] = "c" * 40
    with pytest.raises(driver.GovernanceMutationError, match="same head"):
        driver.merge_operational_phases(
            pending=deepcopy(expected["pending"]),
            success=other_head,
            policy_sha256=digest,
            pull_request=deepcopy(expected["pull_request"]),
            ruleset_source_commit=SOURCE,
        )


@pytest.mark.parametrize("phase_name", ["pending", "success"])
def test_operational_phase_binds_seven_fresh_get_projections(
    phase_name: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    driver = load_driver()
    fixtures = load_fixtures()
    policy, policy_raw, evidence = fixtures.good_bundle(driver.guard)
    after, _after_raw = evidence["after_state"]
    expected = fixtures.good_operational(
        driver.guard,
        policy,
        driver.guard.sha256_bytes(policy_raw),
    )[phase_name]
    raw_pull = {
        "base": {
            "ref": expected["pull_request"]["base_ref"],
            "repo": {
                "full_name": expected["pull_request"]["base_repository"]
            },
        },
        "draft": expected["pull_request"]["draft"],
        "head": {
            "ref": expected["pull_request"]["head_ref"],
            "repo": {
                "full_name": expected["pull_request"]["head_repository"]
            },
            "sha": expected["pull_request"]["head_sha"],
        },
        "mergeable": expected["pull_request"]["mergeable"],
        "mergeable_state": expected["pull_request"]["mergeable_state"],
        "review_comments": 0,
        "state": "open",
    }

    class Client:
        def __init__(self) -> None:
            self.counts = {
                method: 0
                for method in driver.guard.HTTP_METHODS
            }

        def add(self, count: int) -> None:
            self.counts["GET"] += count

    client = Client()

    def one_trace(target: Client, value: Any, count: int = 1):
        target.add(count)
        trace = driver.EndpointTrace([200] * count, count)
        return deepcopy(value), trace

    monkeypatch.setattr(
        driver,
        "get_single",
        lambda target, *_args, **_kwargs: (
            200,
            deepcopy(raw_pull),
            one_trace(target, {}, 1)[1],
        ),
    )
    monkeypatch.setattr(
        driver,
        "get_paginated",
        lambda target, *_args, **_kwargs: one_trace(target, [], 1),
    )
    monkeypatch.setattr(
        driver,
        "capture_checks",
        lambda target, *_args, **_kwargs: one_trace(
            target,
            expected["checks"],
            2,
        ),
    )
    monkeypatch.setattr(
        driver,
        "_capture_branch",
        lambda target, *_args, **_kwargs: one_trace(
            target,
            expected["branch"],
        ),
    )
    monkeypatch.setattr(
        driver,
        "capture_ruleset_inventory",
        lambda target, *_args, **_kwargs: one_trace(
            target,
            expected["rulesets"],
            2,
        ),
    )
    monkeypatch.setattr(
        driver,
        "capture_named_ruleset",
        lambda target, *_args, **_kwargs: one_trace(
            target,
            expected["named_ruleset"],
        ),
    )
    monkeypatch.setattr(
        driver,
        "_capture_effective_rules",
        lambda target, *_args, **_kwargs: one_trace(
            target,
            expected["effective_rules"],
        ),
    )
    observed = driver.capture_operational_phase(
        client,
        phase_name=phase_name,
        pull_request_number=87,
        source_commit=OPERATIONAL_HEAD,
        policy=policy,
        after_state=after,
    )
    assert set(observed["pagination"]) == {
        "branch",
        "checks",
        "effective_rules",
        "named_ruleset",
        "pull_request",
        "review_comments",
        "rulesets",
    }
    assert observed["request_counts"]["GET"] == 9
    assert observed["request_counts"] == client.counts
    assert observed["pull_request"] == expected["pull_request"]
    assert observed["merge_permitted"] is (phase_name == "success")

    extra_client = Client()
    extra_client.add(1)
    with pytest.raises(driver.GovernanceMutationError, match="transport counts"):
        driver.capture_operational_phase(
            extra_client,
            phase_name=phase_name,
            pull_request_number=87,
            source_commit=OPERATIONAL_HEAD,
            policy=policy,
            after_state=after,
        )


@pytest.mark.parametrize(
    ("arguments", "expected_allow_post", "expected_result"),
    [
        ([], False, 0),
        (["--execute"], True, 0),
        (["--recover"], False, 1),
        (["--capture-operational", "pending"], False, 0),
        (["--capture-operational", "success"], False, 0),
    ],
)
def test_main_dispatches_each_mode_with_exact_write_authority(
    arguments: list[str],
    expected_allow_post: bool,
    expected_result: int,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    driver = load_driver()
    created: list[dict[str, Any]] = []

    class Client:
        def __init__(self, **kwargs: Any) -> None:
            created.append(kwargs)

    monkeypatch.setattr(driver, "GitHubClient", Client)
    monkeypatch.setattr(driver, "github_token", lambda: "token")
    monkeypatch.setattr(driver, "load_policy", lambda: ({}, b"policy\n"))
    monkeypatch.setattr(
        driver,
        "local_source_commit",
        lambda **_kwargs: SOURCE,
    )
    monkeypatch.setattr(
        driver,
        "operational_source_commit",
        lambda **_kwargs: OPERATIONAL_HEAD,
    )
    monkeypatch.setattr(
        driver,
        "_assert_fresh_transaction_paths",
        lambda _root: None,
    )
    monkeypatch.setattr(driver, "transaction_lock", nullcontext)
    monkeypatch.setattr(
        driver,
        "run_read_only_preflight",
        lambda *_args, **_kwargs: {"request_counts": {"GET": 14}},
    )

    def transaction(*_args: Any, **kwargs: Any) -> dict[str, Any]:
        if kwargs.get("recover"):
            return {
                "abort_record": {
                    "classification": "inconclusive",
                    "reason_code": "dispatch_not_attempted",
                }
            }
        return {
            "mutation_receipt": {
                "outcome": "applied",
                "ruleset_id": 239,
            }
        }

    monkeypatch.setattr(driver, "run_governance_transaction", transaction)
    monkeypatch.setattr(
        driver,
        "capture_operational_transition",
        lambda *_args, **kwargs: {
            "source_commit": kwargs["source_commit"]
        },
    )
    assert driver.main(arguments) == expected_result
    assert len(created) == 1
    assert created[0]["allow_post"] is expected_allow_post
    if arguments[:1] == ["--capture-operational"]:
        assert (
            created[0]["method_budgets"]
            == driver.OPERATIONAL_METHOD_BUDGETS
        )
