"""Adversarial tests for iter239's credential-free governance validator."""

from __future__ import annotations

from copy import deepcopy
import importlib.util
from pathlib import Path
import shutil
import subprocess

import pytest


ROOT = Path(__file__).resolve().parents[1]
POLICY_PATH = (
    ROOT / "experiments/iter239_repository_governance/policy.json"
)
FIXTURE_PATH = (
    ROOT
    / "tests/fixtures/iter239_repository_governance/known_bad_cases.json"
)
SOURCE = "a" * 40
OPERATIONAL_HEAD = "b" * 40
KNOWN_BAD_EXPECTED_ERRORS = {
    "ambiguous_without_reconciliation": "exact GET reconciliation",
    "approval_count_omitted": "pull-request parameters",
    "approval_count_one": "pull-request parameters",
    "conversation_resolution_disabled": "pull-request parameters",
    "disabled_enforcement": "enforcement must be active",
    "duplicate_check": "required checks must be the exact",
    "duplicate_json_key": "duplicate JSON keys",
    "extra_check": "required checks must be the exact",
    "incomplete_pagination": "pagination must be complete",
    "inactive_enforcement": "enforcement must be active",
    "independent_review_claim": "falsely claims independent review",
    "linear_history_extra": "rule types must be exactly",
    "missing_check": "required checks must be the exact",
    "missing_deletion": "rule types must be exactly",
    "missing_non_fast_forward": "rule types must be exactly",
    "missing_ref_selector": "refs must be exactly",
    "nonempty_bypass": "bypass actors must be exactly empty",
    "nonfinite_json_value": "non-finite JSON value",
    "push_context_substitution": "required checks must be the exact",
    "rebase_allowed": "pull-request parameters",
    "second_mutation_request": "retained dispatch attempt",
    "squash_allowed": "pull-request parameters",
    "stale_default_branch": "frozen precondition drift",
    "stale_source_head": "check head is stale",
    "unspecified_check_app": "required checks must be the exact",
    "wildcard_ref": "refs must be exactly",
    "workflow_command_drift": "bytes differ beyond",
    "workflow_continue_on_error": "bytes differ beyond",
    "workflow_dependency_drift": "bytes differ beyond",
    "workflow_job_condition": "bytes differ beyond",
    "workflow_matrix_drift": "bytes differ beyond",
    "workflow_path_filter": "bytes differ beyond",
    "workflow_permission_drift": "bytes differ beyond",
    "workflow_runner_drift": "bytes differ beyond",
    "workflow_step_condition": "bytes differ beyond",
    "workflow_trigger_drift": "bytes differ beyond",
    "wrong_check_app": "required checks must be the exact",
    "wrong_ref": "refs must be exactly",
}


def load_guard():
    path = ROOT / "scripts/validate_iter239_repository_governance.py"
    spec = importlib.util.spec_from_file_location(
        "validate_iter239_repository_governance",
        path,
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_policy(guard) -> tuple[dict, bytes]:
    return guard.load_canonical_json(POLICY_PATH)


def pagination(
    guard,
    keys: set[str],
    projections: dict,
    *,
    status_overrides: dict[str, int] | None = None,
) -> dict:
    def item_count(key: str) -> int:
        projection = projections[key]
        if isinstance(projection, list):
            return len(projection)
        if key == "ruleset_history":
            return len(projection["entries"])
        return 1

    return {
        key: {
            "complete": True,
            "http_statuses": [
                (status_overrides or {}).get(key, 200)
            ],
            "item_count": item_count(key),
            "page_count": 1,
            "projection_sha256": guard.canonical_sha256(projections[key]),
            "request_count": 1,
        }
        for key in sorted(keys)
    }


def check_rows(
    guard,
    *,
    head: str,
    pending: bool = False,
    include_push: bool = True,
) -> list[dict]:
    names = [
        ("verify pull_request py3.11", "pull_request"),
        ("verify pull_request py3.12", "pull_request"),
    ]
    if include_push:
        names.extend(
            [
                ("verify push py3.11", "push"),
                ("verify push py3.12", "push"),
            ]
        )
    return [
        {
            "attempt": 1,
            "check_run_id": 3000 + index,
            "check_suite_id": 5000 if event == "pull_request" else 6000,
            "conclusion": None if pending else "success",
            "event": event,
            "head_sha": head,
            "integration_id": guard.INTEGRATION_ID,
            "name": name,
            "status": "in_progress" if pending else "completed",
            "workflow_id": guard.WORKFLOW_ID,
            "workflow_path": guard.WORKFLOW_RELATIVE.as_posix(),
            "workflow_run_id": 1000 if event == "pull_request" else 2000,
        }
        for index, (name, event) in enumerate(names)
    ]


def good_before(guard, policy_digest: str) -> dict:
    projections = deepcopy(guard.EXPECTED_BEFORE_PROJECTIONS)
    projections.update(
        {
            "checks": check_rows(guard, head=SOURCE),
            "open_pull_request": {
                "base_ref": guard.DEFAULT_BRANCH,
                "base_repository": guard.REPOSITORY,
                "head_ref": "agent/iter239-repository-governance",
                "head_repository": guard.REPOSITORY,
                "head_sha": SOURCE,
                "number": 87,
                "state": "open",
            },
            "source_ref": {
                "ref": "refs/heads/agent/iter239-repository-governance",
                "sha": SOURCE,
            },
        }
    )
    return {
        "api_version": guard.API_VERSION,
        "observed_at": "2026-07-19T12:00:00Z",
        "pagination": pagination(
            guard,
            guard.PAGINATION_KEYS_BEFORE,
            projections,
            status_overrides={"classic_protection": 404},
        ),
        "policy_sha256": policy_digest,
        "projections": projections,
        "repository": guard.REPOSITORY,
        "request_counts": {
            "DELETE": 0,
            "GET": 14,
            "PATCH": 0,
            "POST": 0,
            "PUT": 0,
        },
        "schema_version": guard.BEFORE_SCHEMA,
        "source_commit": SOURCE,
    }


def good_intent(
    guard,
    policy: dict,
    policy_digest: str,
    before_raw: bytes,
) -> dict:
    return {
        "api_version": guard.API_VERSION,
        "before_state_sha256": guard.sha256_bytes(before_raw),
        "endpoint": guard.CREATE_ENDPOINT,
        "method": "POST",
        "persisted_at": "2026-07-19T12:00:01Z",
        "policy_sha256": policy_digest,
        "repository": guard.REPOSITORY,
        "request_body": deepcopy(policy["request_body"]),
        "request_body_sha256": policy["request_body_sha256"],
        "schema_version": guard.INTENT_SCHEMA,
        "source_commit": SOURCE,
        "write_guards": {
            "directory_fsync_completed": True,
            "exclusive_create": True,
            "file_fsync_completed": True,
        },
    }


def ruleset_projection(guard, policy: dict) -> dict:
    request_policy = deepcopy(policy["request_body"])
    server_policy = deepcopy(request_policy)
    del server_policy["bypass_actors"]
    pull = next(
        rule
        for rule in server_policy["rules"]
        if rule["type"] == "pull_request"
    )
    pull["parameters"]["dismissal_restriction"] = {
        "allowed_actors": [],
        "enabled": False,
    }
    pull["parameters"]["required_reviewers"] = []
    normalization, normalized = guard.server_policy_normalization(
        request_policy,
        server_policy,
    )
    assert normalized == request_policy
    return {
        "id": 239,
        "normalization": normalization,
        "request_policy": request_policy,
        "server_metadata": {
            "created_at": "2026-07-19T15:00:02.123+03:00",
            "current_user_can_bypass": "never",
            "current_user_can_bypass_present": True,
            "links": {
                "html": {
                    "href": (
                        "https://github.com/manfromnowhere143/telos/rules/239"
                    )
                },
                "self": {
                    "href": (
                        "https://api.github.com/repos/"
                        "manfromnowhere143/telos/rulesets/239"
                    )
                },
            },
            "node_id": "RRS_fixture",
            "updated_at": "2026-07-19T15:00:02.123+03:00",
        },
        "server_policy": server_policy,
        "source": "manfromnowhere143/telos",
        "source_type": "Repository",
    }


def good_after(
    guard,
    policy: dict,
    policy_digest: str,
    before: dict,
) -> dict:
    before_projections = before["projections"]
    projections = {
        key: deepcopy(before_projections[key])
        for key in guard.UNCHANGED_PROJECTIONS
    }
    named = ruleset_projection(guard, policy)
    projections.update(
        {
            "branch": {
                "name": guard.DEFAULT_BRANCH,
                "protected": True,
                "sha": guard.MERGED_MASTER_ANCHOR,
            },
            "effective_rules": guard.expected_effective_rules(named),
            "named_ruleset": named,
            "ruleset_history": {
                "entries": [
                    {
                        "actor": {
                            "id": 1,
                            "type": "User",
                        },
                        "updated_at": "2026-07-19T15:00:02.123+03:00",
                        "version_id": 1,
                    }
                ],
                "latest_version": {
                    "actor": {
                        "id": 1,
                        "type": "User",
                    },
                    "state": guard.ruleset_history_state(named),
                    "updated_at": "2026-07-19T15:00:02.123+03:00",
                    "version_id": 1,
                },
                "ruleset_id": 239,
            },
            "rulesets": [deepcopy(named)],
        }
    )
    return {
        "api_version": guard.API_VERSION,
        "before_comparison": {
            "drift": [],
            "unchanged": deepcopy(guard.UNCHANGED_PROJECTIONS),
        },
        "created_ruleset_id": 239,
        "observed_at": "2026-07-19T12:00:03Z",
        "pagination": pagination(
            guard,
            guard.PAGINATION_KEYS_AFTER,
            projections,
        ),
        "policy_sha256": policy_digest,
        "projections": projections,
        "repository": guard.REPOSITORY,
        "request_counts": {
            "DELETE": 0,
            "GET": len(guard.PAGINATION_KEYS_AFTER),
            "PATCH": 0,
            "POST": 0,
            "PUT": 0,
        },
        "schema_version": guard.AFTER_SCHEMA,
        "source_commit": SOURCE,
    }


def good_receipt(
    guard,
    policy: dict,
    policy_digest: str,
    before_raw: bytes,
    intent_raw: bytes,
    after_raw: bytes,
) -> dict:
    counts = {
        key: 0
        for key in guard.HTTP_METHODS | guard.SEMANTIC_MUTATIONS
    }
    counts["GET"] = 14 + len(guard.PAGINATION_KEYS_AFTER)
    counts["POST"] = 1
    return {
        "after_state_sha256": guard.sha256_bytes(after_raw),
        "ambiguous_reconciliation": "not_required",
        "before_state_sha256": guard.sha256_bytes(before_raw),
        "dispatch_attempt": {
            "consumed_at": "2026-07-19T12:00:02Z",
            "endpoint": guard.CREATE_ENDPOINT,
            "method": "POST",
            "mutation_intent_sha256": guard.sha256_bytes(intent_raw),
            "schema_version": guard.DISPATCH_SCHEMA,
            "source_commit": SOURCE,
            "write_guards": {
                "directory_fsync_completed": True,
                "exclusive_create": True,
                "file_fsync_completed": True,
            },
        },
        "finished_at": "2026-07-19T12:00:04Z",
        "mutation_intent_sha256": guard.sha256_bytes(intent_raw),
        "outcome": "applied",
        "policy_sha256": policy_digest,
        "post_response": {
            "classification": "accepted_created",
            "http_status": 201,
            "projection": ruleset_projection(guard, policy),
            "projection_sha256": guard.canonical_sha256(
                ruleset_projection(guard, policy)
            ),
        },
        "repository": guard.REPOSITORY,
        "request_body_sha256": policy["request_body_sha256"],
        "request_counts": counts,
        "ruleset_id": 239,
        "schema_version": guard.RECEIPT_SCHEMA,
        "source_commit": SOURCE,
        "started_at": "2026-07-19T12:00:00Z",
    }


def good_operational(guard, policy: dict, policy_digest: str) -> dict:
    named = ruleset_projection(guard, policy)
    governance = {
        "branch": {
            "name": guard.DEFAULT_BRANCH,
            "protected": True,
            "sha": guard.MERGED_MASTER_ANCHOR,
        },
        "effective_rules": guard.expected_effective_rules(named),
        "named_ruleset": named,
        "rulesets": [deepcopy(named)],
    }

    def phase(*, pending: bool, observed_at: str) -> dict:
        checks = check_rows(
            guard,
            head=OPERATIONAL_HEAD,
            pending=pending,
            include_push=False,
        )
        pull_request = {
            "base_ref": guard.DEFAULT_BRANCH,
            "base_repository": guard.REPOSITORY,
            "draft": False,
            "head_ref": "agent/iter239-repository-governance",
            "head_repository": guard.REPOSITORY,
            "head_sha": OPERATIONAL_HEAD,
            "mergeable": True,
            "mergeable_state": "blocked" if pending else "clean",
            "review_comment_count": 0,
            "state": "open",
        }
        projections = {
            **deepcopy(governance),
            "checks": checks,
            "pull_request": pull_request,
            "review_comments": [],
        }
        return {
            **deepcopy(governance),
            "checks": checks,
            "merge_permitted": not pending,
            "non_check_requirements_satisfied": True,
            "observed_at": observed_at,
            "pagination": pagination(guard, set(projections), projections),
            "pull_request": pull_request,
            "request_counts": {
                "DELETE": 0,
                "GET": len(projections),
                "PATCH": 0,
                "POST": 0,
                "PUT": 0,
            },
            "review_comments": [],
            "required_check_rollup_state": "PENDING" if pending else "SUCCESS",
            "source_commit": OPERATIONAL_HEAD,
        }

    return {
        "api_version": guard.API_VERSION,
        "independent_review_status": "blocked",
        "pending": phase(pending=True, observed_at="2026-07-19T12:10:00Z"),
        "policy_sha256": policy_digest,
        "pull_request": {
            "base_ref": guard.DEFAULT_BRANCH,
            "base_repository": guard.REPOSITORY,
            "head_ref": "agent/iter239-repository-governance",
            "head_repository": guard.REPOSITORY,
            "number": 87,
        },
        "repository": guard.REPOSITORY,
        "ruleset_source_commit": SOURCE,
        "schema_version": guard.OPERATIONAL_SCHEMA,
        "source_commit": OPERATIONAL_HEAD,
        "success": phase(pending=False, observed_at="2026-07-19T12:11:00Z"),
    }


def good_bundle(guard) -> tuple[dict, bytes, dict[str, tuple[dict, bytes]]]:
    policy, policy_raw = load_policy(guard)
    policy_digest = guard.sha256_bytes(policy_raw)
    before = good_before(guard, policy_digest)
    before_raw = guard.canonical_json_bytes(before)
    intent = good_intent(guard, policy, policy_digest, before_raw)
    intent_raw = guard.canonical_json_bytes(intent)
    after = good_after(guard, policy, policy_digest, before)
    after_raw = guard.canonical_json_bytes(after)
    receipt = good_receipt(
        guard,
        policy,
        policy_digest,
        before_raw,
        intent_raw,
        after_raw,
    )
    operational = good_operational(guard, policy, policy_digest)
    return policy, policy_raw, {
        "after_state": (after, after_raw),
        "before_state": (before, before_raw),
        "mutation_intent": (intent, intent_raw),
        "mutation_receipt": (receipt, guard.canonical_json_bytes(receipt)),
        "operational_check": (
            operational,
            guard.canonical_json_bytes(operational),
        ),
    }


def write_policy_root(tmp_path: Path) -> Path:
    destination = tmp_path / "experiments/iter239_repository_governance"
    destination.mkdir(parents=True)
    shutil.copy2(POLICY_PATH, destination / "policy.json")
    return tmp_path


def test_repository_policy_is_canonical_and_exact() -> None:
    guard = load_guard()
    policy, _raw = load_policy(guard)
    assert guard.policy_failures(policy) == []


def test_repository_contract_is_phase_aware() -> None:
    guard = load_guard()
    present = [
        (ROOT / relative).is_file()
        for relative in guard.EVIDENCE_RELATIVES.values()
    ]
    if any(present):
        assert all(present)
        assert (ROOT / guard.RESULT_RELATIVE).is_file()
        assert guard.collect_failures() == []
        assert guard.collect_failures(require_complete=True) == []
        assert "complete retained" in guard.success_message(
            evidence_present=True
        )
    else:
        assert guard.collect_failures() == []
        message = guard.success_message(evidence_present=False)
        assert "prospective implementation" in message
        assert "live evidence absent" in message
        assert "acceptance unestablished" in message
        failures = guard.collect_failures(require_complete=True)
        assert failures == [
            "iter239 live evidence is absent; --require-complete cannot "
            "accept a prospective implementation"
        ]


def test_prospective_phase_accepts_no_evidence_but_not_partial(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    guard = load_guard()
    root = write_policy_root(tmp_path)
    monkeypatch.setattr(guard, "current_ci_failures", lambda _root: [])
    assert guard.collect_failures(root=root) == []
    assert "live evidence is absent" in guard.collect_failures(
        root=root,
        require_complete=True,
    )[0]

    relative = guard.EVIDENCE_RELATIVES["before_state"]
    path = root / relative
    path.parent.mkdir(parents=True)
    path.write_bytes(guard.canonical_json_bytes({"incomplete": True}))
    failures = guard.collect_failures(root=root)
    assert len(failures) == 1
    assert "live evidence is partial" in failures[0]


def test_complete_synthetic_bundle_passes_g0_through_g5(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    guard = load_guard()
    policy, policy_raw, evidence = good_bundle(guard)
    monkeypatch.setattr(
        guard,
        "source_commit_failures",
        lambda *_args, **_kwargs: [],
    )
    monkeypatch.setattr(
        guard,
        "operational_source_failures",
        lambda *_args, **_kwargs: [],
    )
    assert (
        guard.evidence_bundle_failures(
            root=ROOT,
            policy=policy,
            policy_raw=policy_raw,
            evidence=evidence,
        )
        == []
    )


@pytest.mark.parametrize("token", ["NaN", "Infinity", "-Infinity"])
def test_strict_json_rejects_duplicate_nonfinite_and_noncanonical(
    token: str,
) -> None:
    guard = load_guard()
    with pytest.raises(guard.GovernanceError, match="duplicate JSON keys"):
        guard.load_canonical_json_bytes(
            b'{"value": 1, "value": 2}\n',
            label="known-bad duplicate",
        )
    with pytest.raises(guard.GovernanceError, match="non-finite JSON value"):
        guard.load_canonical_json_bytes(
            f'{{"value": {token}}}\n'.encode(),
            label="known-bad nonfinite",
        )
    with pytest.raises(guard.GovernanceError, match="canonical JSON"):
        guard.load_canonical_json_bytes(
            b'{"value": 1e400}\n',
            label="known-bad overflow",
        )
    with pytest.raises(guard.GovernanceError, match="not canonical"):
        guard.load_canonical_json_bytes(
            b'{"value":1}\n',
            label="known-bad noncanonical",
        )


def test_json_contracts_do_not_coerce_booleans_and_integers() -> None:
    guard = load_guard()
    policy, policy_raw, evidence = good_bundle(guard)
    digest = guard.sha256_bytes(policy_raw)

    count_as_bool = deepcopy(policy["request_body"])
    count_as_bool["rules"][2]["parameters"][
        "required_approving_review_count"
    ] = False
    assert any(
        "frozen policy" in failure
        for failure in guard.request_body_failures(
            count_as_bool,
            label="known-bad bool count",
        )
    )
    bool_as_int = deepcopy(policy["request_body"])
    bool_as_int["rules"][2]["parameters"][
        "dismiss_stale_reviews_on_push"
    ] = 0
    assert any(
        "frozen policy" in failure
        for failure in guard.request_body_failures(
            bool_as_int,
            label="known-bad int boolean",
        )
    )
    self_hashed_policy = deepcopy(policy)
    self_hashed_policy["request_body"] = count_as_bool
    self_hashed_policy["request_body_sha256"] = guard.canonical_sha256(
        count_as_bool
    )
    assert guard.policy_failures(self_hashed_policy)

    enabled_as_int = deepcopy(policy)
    enabled_as_int["expected_before"]["actions"]["enabled"] = 1
    assert any(
        "frozen pre-mutation projection differs" in failure
        for failure in guard.policy_failures(enabled_as_int)
    )

    before, before_raw = evidence["before_state"]
    action_type_drift = deepcopy(before)
    action_type_drift["projections"]["actions"]["enabled"] = 1
    action_type_drift["pagination"]["actions"]["projection_sha256"] = (
        guard.canonical_sha256(
            action_type_drift["projections"]["actions"]
        )
    )
    assert any(
        "frozen precondition drift" in failure
        for failure in guard.before_state_failures(
            action_type_drift,
            policy_sha256=digest,
        )
    )
    branch_type_drift = deepcopy(before)
    branch_type_drift["projections"]["branch"]["protected"] = 0
    branch_type_drift["pagination"]["branch"]["projection_sha256"] = (
        guard.canonical_sha256(
            branch_type_drift["projections"]["branch"]
        )
    )
    assert any(
        "frozen precondition drift" in failure
        for failure in guard.before_state_failures(
            branch_type_drift,
            policy_sha256=digest,
        )
    )

    intent, _intent_raw = evidence["mutation_intent"]
    guard_type_drift = deepcopy(intent)
    guard_type_drift["write_guards"]["file_fsync_completed"] = 1
    assert any(
        "fsync" in failure
        for failure in guard.mutation_intent_failures(
            guard_type_drift,
            policy_sha256=digest,
            before=before,
            before_raw=before_raw,
            policy=policy,
        )
    )
    false_count = deepcopy(before)
    false_count["request_counts"]["GET"] = False
    assert any(
        "GET must be a nonnegative integer" in failure
        for failure in guard.before_state_failures(
            false_count,
            policy_sha256=digest,
        )
    )
    boolean_attempt = deepcopy(before)
    boolean_attempt["projections"]["checks"][0]["attempt"] = True
    boolean_attempt["pagination"]["checks"]["projection_sha256"] = (
        guard.canonical_sha256(boolean_attempt["projections"]["checks"])
    )
    assert any(
        "attempt one" in failure
        for failure in guard.before_state_failures(
            boolean_attempt,
            policy_sha256=digest,
        )
    )

    after, _after_raw = evidence["after_state"]
    server_type_drift = deepcopy(
        after["projections"]["named_ruleset"]
    )
    server_type_drift["server_policy"]["rules"][2]["parameters"][
        "dismiss_stale_reviews_on_push"
    ] = 0
    assert any(
        "semantic differences" in failure
        for failure in guard._ruleset_projection_failures(
            server_type_drift,
            label="known-bad server policy",
        )
    )
    effective_type_drift = deepcopy(after)
    effective_parameters = deepcopy(
        effective_type_drift["projections"]["effective_rules"][2][
            "parameters"
        ]
    )
    effective_parameters["dismiss_stale_reviews_on_push"] = 0
    effective_type_drift["projections"]["effective_rules"][2][
        "parameters"
    ] = effective_parameters
    effective_type_drift["pagination"]["effective_rules"][
        "projection_sha256"
    ] = guard.canonical_sha256(
        effective_type_drift["projections"]["effective_rules"]
    )
    assert any(
        "technical floor" in failure
        for failure in guard.after_state_failures(
            effective_type_drift,
            policy_sha256=digest,
            before=before,
            policy=policy,
        )
    )


def body_mutations(guard) -> dict[str, dict]:
    mutations: dict[str, dict] = {}

    def candidate() -> dict:
        return deepcopy(guard.EXPECTED_REQUEST_BODY)

    value = candidate()
    value["bypass_actors"] = [{"actor_id": 1, "actor_type": "RepositoryRole"}]
    mutations["nonempty_bypass"] = value
    value = candidate()
    value["enforcement"] = "evaluate"
    mutations["inactive_enforcement"] = value
    value = candidate()
    value["enforcement"] = "disabled"
    mutations["disabled_enforcement"] = value
    value = candidate()
    value["conditions"]["ref_name"]["include"][1] = "refs/heads/main"
    mutations["wrong_ref"] = value
    value = candidate()
    value["conditions"]["ref_name"]["include"].pop()
    mutations["missing_ref_selector"] = value
    value = candidate()
    value["conditions"]["ref_name"]["include"][1] = "refs/heads/*"
    mutations["wildcard_ref"] = value
    value = candidate()
    value["rules"].pop(0)
    mutations["missing_deletion"] = value
    value = candidate()
    value["rules"].pop(1)
    mutations["missing_non_fast_forward"] = value
    value = candidate()
    value["rules"][2]["parameters"]["required_approving_review_count"] = 1
    mutations["approval_count_one"] = value
    value = candidate()
    del value["rules"][2]["parameters"]["required_approving_review_count"]
    mutations["approval_count_omitted"] = value
    value = candidate()
    value["rules"][2]["parameters"]["allowed_merge_methods"].append("squash")
    mutations["squash_allowed"] = value
    value = candidate()
    value["rules"][2]["parameters"]["allowed_merge_methods"].append("rebase")
    mutations["rebase_allowed"] = value
    value = candidate()
    value["rules"].append({"type": "required_linear_history"})
    mutations["linear_history_extra"] = value
    value = candidate()
    value["rules"][2]["parameters"]["required_review_thread_resolution"] = False
    mutations["conversation_resolution_disabled"] = value
    value = candidate()
    value["rules"][3]["parameters"]["required_status_checks"].pop()
    mutations["missing_check"] = value
    value = candidate()
    value["rules"][3]["parameters"]["required_status_checks"].append(
        {"context": "extra", "integration_id": guard.INTEGRATION_ID}
    )
    mutations["extra_check"] = value
    value = candidate()
    value["rules"][3]["parameters"]["required_status_checks"][1] = deepcopy(
        value["rules"][3]["parameters"]["required_status_checks"][0]
    )
    mutations["duplicate_check"] = value
    value = candidate()
    value["rules"][3]["parameters"]["required_status_checks"][0][
        "integration_id"
    ] = 1
    mutations["wrong_check_app"] = value
    value = candidate()
    del value["rules"][3]["parameters"]["required_status_checks"][0][
        "integration_id"
    ]
    mutations["unspecified_check_app"] = value
    value = candidate()
    value["rules"][3]["parameters"]["required_status_checks"][0][
        "context"
    ] = "verify push py3.11"
    mutations["push_context_substitution"] = value
    return mutations


def test_every_request_body_known_bad_is_rejected() -> None:
    guard = load_guard()
    for fixture_id, value in body_mutations(guard).items():
        failures = guard.request_body_failures(
            value,
            label=f"known-bad {fixture_id}",
        )
        assert any(
            KNOWN_BAD_EXPECTED_ERRORS[fixture_id] in failure
            for failure in failures
        ), fixture_id


def ci_mutations(expected: bytes) -> dict[str, bytes]:
    return {
        "workflow_trigger_drift": expected + b"\non:\n  workflow_dispatch:\n",
        "workflow_permission_drift": expected + b"\npermissions: write-all\n",
        "workflow_runner_drift": expected + b"\nruns-on: self-hosted\n",
        "workflow_matrix_drift": expected + b"\npython-version: [\"3.13\"]\n",
        "workflow_dependency_drift": expected + b"\nuses: actions/checkout@main\n",
        "workflow_command_drift": expected + b"\nrun: true\n",
        "workflow_step_condition": expected + b"\nif: success()\n",
        "workflow_job_condition": expected + b"\njobs:\n  verify:\n    if: always()\n",
        "workflow_continue_on_error": expected + b"\ncontinue-on-error: true\n",
        "workflow_path_filter": expected + b"\npaths:\n  - scripts/**\n",
    }


def test_ci_guard_accepts_only_the_one_exact_name_substitution() -> None:
    guard = load_guard()
    before = b"name: ci\nname: verify py${{ matrix.python-version }}\n"
    expected = before.replace(guard.BEFORE_JOB_NAME, guard.AFTER_JOB_NAME)
    assert guard.ci_evolution_failures(before, expected) == []
    for fixture_id, value in ci_mutations(expected).items():
        failures = guard.ci_evolution_failures(before, value)
        assert any(
            KNOWN_BAD_EXPECTED_ERRORS[fixture_id] in failure
            for failure in failures
        ), fixture_id


def test_before_state_rejects_stale_heads_and_incomplete_pagination() -> None:
    guard = load_guard()
    _policy, policy_raw = load_policy(guard)
    before = good_before(guard, guard.sha256_bytes(policy_raw))
    assert guard.before_state_failures(
        before,
        policy_sha256=guard.sha256_bytes(policy_raw),
    ) == []
    joined = deepcopy(before)
    joined["pagination"]["checks"]["request_count"] = 3
    joined["pagination"]["checks"]["http_statuses"] = [200, 200, 200]
    joined["request_counts"]["GET"] += 2
    assert guard.before_state_failures(
        joined,
        policy_sha256=guard.sha256_bytes(policy_raw),
    ) == []

    stale_default = deepcopy(before)
    stale_default["projections"]["branch"]["sha"] = "0" * 40
    assert any(
        "frozen precondition drift" in failure
        for failure in guard.before_state_failures(
            stale_default,
            policy_sha256=guard.sha256_bytes(policy_raw),
        )
    )
    stale_source = deepcopy(before)
    stale_source["projections"]["checks"][0]["head_sha"] = "0" * 40
    assert any(
        "check head is stale" in failure
        for failure in guard.before_state_failures(
            stale_source,
            policy_sha256=guard.sha256_bytes(policy_raw),
        )
    )
    incomplete = deepcopy(before)
    incomplete["pagination"]["rulesets"]["complete"] = False
    assert any(
        "pagination must be complete" in failure
        for failure in guard.before_state_failures(
            incomplete,
            policy_sha256=guard.sha256_bytes(policy_raw),
        )
    )


def test_receipt_rejects_second_post_unrelated_mutation_and_false_ambiguity() -> None:
    guard = load_guard()
    policy, policy_raw, evidence = good_bundle(guard)
    policy_digest = guard.sha256_bytes(policy_raw)
    before, before_raw = evidence["before_state"]
    intent, intent_raw = evidence["mutation_intent"]
    after, after_raw = evidence["after_state"]
    receipt, _receipt_raw = evidence["mutation_receipt"]

    def failures(value: dict) -> list[str]:
        return guard.mutation_receipt_failures(
            value,
            policy_sha256=policy_digest,
            before=before,
            before_raw=before_raw,
            intent=intent,
            intent_raw=intent_raw,
            after=after,
            after_raw=after_raw,
            policy=policy,
        )

    assert failures(receipt) == []
    second = deepcopy(receipt)
    second["request_counts"]["POST"] = 2
    assert any(
        "retained dispatch attempt" in failure
        for failure in failures(second)
    )
    unrelated = deepcopy(receipt)
    unrelated["request_counts"]["collaborator_invite"] = 1
    assert any("collaborator_invite" in failure for failure in failures(unrelated))
    ambiguous = deepcopy(receipt)
    ambiguous["outcome"] = "ambiguous_applied"
    assert any("exact GET reconciliation" in failure for failure in failures(ambiguous))
    wrong_status = deepcopy(receipt)
    wrong_status["post_response"]["http_status"] = 200
    assert any("HTTP 201" in failure for failure in failures(wrong_status))
    wrong_projection_digest = deepcopy(receipt)
    wrong_projection_digest["post_response"]["projection_sha256"] = "0" * 64
    assert any(
        "POST response projection digest differs" in failure
        for failure in failures(wrong_projection_digest)
    )
    missing_dispatch = deepcopy(receipt)
    del missing_dispatch["dispatch_attempt"]
    assert any(
        "dispatch attempt" in failure
        for failure in failures(missing_dispatch)
    )
    fabricated_count = deepcopy(receipt)
    fabricated_count["request_counts"]["POST"] = 0
    assert any(
        "retained dispatch attempt" in failure
        for failure in failures(fabricated_count)
    )


def test_receipt_retains_transport_and_http_response_ambiguity() -> None:
    guard = load_guard()
    policy, policy_raw, evidence = good_bundle(guard)
    policy_digest = guard.sha256_bytes(policy_raw)
    before, before_raw = evidence["before_state"]
    intent, intent_raw = evidence["mutation_intent"]
    after, after_raw = evidence["after_state"]
    receipt, _receipt_raw = evidence["mutation_receipt"]

    def failures(value: dict) -> list[str]:
        return guard.mutation_receipt_failures(
            value,
            policy_sha256=policy_digest,
            before=before,
            before_raw=before_raw,
            intent=intent,
            intent_raw=intent_raw,
            after=after,
            after_raw=after_raw,
            policy=policy,
        )

    ambiguous = deepcopy(receipt)
    ambiguous["outcome"] = "ambiguous_applied"
    ambiguous["ambiguous_reconciliation"] = "exact_get_match"
    ambiguous["post_response"] = {
        "classification": "ambiguous_transport",
        "http_status": None,
        "projection": None,
        "projection_sha256": None,
    }
    assert failures(ambiguous) == []

    ambiguous["post_response"] = {
        "classification": "ambiguous_http_response",
        "http_status": 429,
        "projection": None,
        "projection_sha256": None,
    }
    assert failures(ambiguous) == []

    mismatched_status = deepcopy(ambiguous)
    mismatched_status["post_response"]["http_status"] = None
    assert any(
        "known status" in failure
        for failure in failures(mismatched_status)
    )
    fabricated_transport_status = deepcopy(ambiguous)
    fabricated_transport_status["post_response"] = {
        "classification": "ambiguous_transport",
        "http_status": 408,
        "projection": None,
        "projection_sha256": None,
    }
    assert any(
        "known status" in failure
        for failure in failures(fabricated_transport_status)
    )
    invalid_status = deepcopy(ambiguous)
    invalid_status["post_response"]["http_status"] = 700
    assert any(
        "known status" in failure
        for failure in failures(invalid_status)
    )


def test_intent_is_bound_to_exact_tls_endpoint_body_and_fsynced_prewrite() -> None:
    guard = load_guard()
    policy, policy_raw, evidence = good_bundle(guard)
    digest = guard.sha256_bytes(policy_raw)
    before, before_raw = evidence["before_state"]
    intent, _intent_raw = evidence["mutation_intent"]

    def failures(value: dict) -> list[str]:
        return guard.mutation_intent_failures(
            value,
            policy_sha256=digest,
            before=before,
            before_raw=before_raw,
            policy=policy,
        )

    assert failures(intent) == []
    wrong_origin = deepcopy(intent)
    wrong_origin["endpoint"] = "http://api.github.com/repos/x/y/rulesets"
    assert any("fixed TLS endpoint" in failure for failure in failures(wrong_origin))
    wrong_method = deepcopy(intent)
    wrong_method["method"] = "PATCH"
    assert any("method must be POST" in failure for failure in failures(wrong_method))
    not_fsynced = deepcopy(intent)
    not_fsynced["write_guards"]["file_fsync_completed"] = False
    assert any("fsync" in failure for failure in failures(not_fsynced))


def test_after_state_rejects_unrelated_drift_and_ineffective_rules() -> None:
    guard = load_guard()
    policy, policy_raw, evidence = good_bundle(guard)
    digest = guard.sha256_bytes(policy_raw)
    before, _before_raw = evidence["before_state"]
    after, _after_raw = evidence["after_state"]

    def failures(value: dict) -> list[str]:
        return guard.after_state_failures(
            value,
            policy_sha256=digest,
            before=before,
            policy=policy,
        )

    assert failures(after) == []
    drift = deepcopy(after)
    drift["projections"]["repository"]["visibility"] = "private"
    assert any("unrelated drift" in failure for failure in failures(drift))
    ineffective = deepcopy(after)
    ineffective["projections"]["effective_rules"].pop()
    ineffective["pagination"]["effective_rules"]["item_count"] -= 1
    ineffective["pagination"]["effective_rules"]["projection_sha256"] = (
        guard.canonical_sha256(ineffective["projections"]["effective_rules"])
    )
    assert any(
        "technical floor" in failure
        for failure in failures(ineffective)
    )
    false_digest = deepcopy(after)
    false_digest["pagination"]["rulesets"]["projection_sha256"] = "0" * 64
    assert any(
        "projection_sha256 differs" in failure
        for failure in failures(false_digest)
    )
    mixed_source = deepcopy(after)
    mixed_source["projections"]["effective_rules"][0]["ruleset_id"] = 999
    mixed_source["pagination"]["effective_rules"]["projection_sha256"] = (
        guard.canonical_sha256(
            mixed_source["projections"]["effective_rules"]
        )
    )
    assert any(
        "created-ruleset provenance" in failure
        for failure in failures(mixed_source)
    )
    null_history = deepcopy(after)
    null_history["projections"]["ruleset_history"]["entries"] = [None]
    null_history["pagination"]["ruleset_history"]["projection_sha256"] = (
        guard.canonical_sha256(
            null_history["projections"]["ruleset_history"]
        )
    )
    assert any(
        "entries[0]: must be an object" in failure
        for failure in failures(null_history)
    )
    boolean_latest_version = deepcopy(after)
    boolean_latest_version["projections"]["ruleset_history"][
        "latest_version"
    ]["version_id"] = True
    boolean_latest_version["pagination"]["ruleset_history"][
        "projection_sha256"
    ] = guard.canonical_sha256(
        boolean_latest_version["projections"]["ruleset_history"]
    )
    assert any(
        "latest history version_id must be positive" in failure
        for failure in failures(boolean_latest_version)
    )
    discarded_metadata = deepcopy(after)
    del discarded_metadata["projections"]["named_ruleset"]["server_metadata"]
    discarded_metadata["projections"]["rulesets"] = [
        deepcopy(discarded_metadata["projections"]["named_ruleset"])
    ]
    for key in ("named_ruleset", "rulesets"):
        discarded_metadata["pagination"][key]["projection_sha256"] = (
            guard.canonical_sha256(
                discarded_metadata["projections"][key]
            )
        )
    assert any(
        "server_metadata" in failure
        for failure in failures(discarded_metadata)
    )
    bypass_capability = deepcopy(after)
    bypass_capability["projections"]["named_ruleset"]["server_metadata"][
        "current_user_can_bypass"
    ] = "always"
    assert any(
        "current_user_can_bypass=never" in failure
        for failure in failures(bypass_capability)
    )
    semantic_server_drift = deepcopy(after)
    pull_rule = next(
        rule
        for rule in semantic_server_drift["projections"]["named_ruleset"][
            "server_policy"
        ]["rules"]
        if rule["type"] == "pull_request"
    )
    pull_rule["parameters"]["required_reviewers"] = [{"type": "Team"}]
    assert any(
        "semantic differences" in failure
        for failure in failures(semantic_server_drift)
    )


def test_operational_check_requires_same_head_fail_closed_transition() -> None:
    guard = load_guard()
    _policy, policy_raw = load_policy(guard)
    digest = guard.sha256_bytes(policy_raw)
    operational = good_operational(guard, _policy, digest)
    after_state = {
        "projections": {
            key: deepcopy(operational["pending"][key])
            for key in (
                "branch",
                "effective_rules",
                "named_ruleset",
                "rulesets",
            )
        }
    }
    assert guard.operational_check_failures(
        operational,
        policy_sha256=digest,
        source_commit=SOURCE,
        expected_pull_request_number=87,
        after_state=after_state,
    ) == []

    premature = deepcopy(operational)
    premature["pending"]["merge_permitted"] = True
    assert any(
        "does not follow raw gate evidence" in failure
        for failure in guard.operational_check_failures(
            premature,
            policy_sha256=digest,
            source_commit=SOURCE,
            expected_pull_request_number=87,
            after_state=after_state,
        )
    )
    wrong_app = deepcopy(operational)
    wrong_app["success"]["checks"][0]["integration_id"] = 1
    assert any(
        "not bound to app 15368" in failure
        for failure in guard.operational_check_failures(
            wrong_app,
            policy_sha256=digest,
            source_commit=SOURCE,
            expected_pull_request_number=87,
            after_state=after_state,
        )
    )
    wrong_workflow = deepcopy(operational)
    wrong_workflow["success"]["checks"][0]["workflow_id"] = 1
    assert any(
        "CI workflow 309260095" in failure
        for failure in guard.operational_check_failures(
            wrong_workflow,
            policy_sha256=digest,
            source_commit=SOURCE,
            expected_pull_request_number=87,
            after_state=after_state,
        )
    )
    unrelated_pr = deepcopy(operational)
    unrelated_pr["pull_request"]["number"] = 88
    assert any(
        "differs from before_state" in failure
        for failure in guard.operational_check_failures(
            unrelated_pr,
            policy_sha256=digest,
            source_commit=SOURCE,
            expected_pull_request_number=87,
            after_state=after_state,
        )
    )
    comments = deepcopy(operational)
    comments["pending"]["review_comments"] = [{"id": 1}]
    comments["pending"]["pagination"]["review_comments"]["item_count"] = 1
    comments["pending"]["pagination"]["review_comments"][
        "projection_sha256"
    ] = guard.canonical_sha256(comments["pending"]["review_comments"])
    assert any(
        "conversation-resolution evidence" in failure
        for failure in guard.operational_check_failures(
            comments,
            policy_sha256=digest,
            source_commit=SOURCE,
            expected_pull_request_number=87,
            after_state=after_state,
        )
    )
    split_run = deepcopy(operational)
    split_run["success"]["checks"][1]["workflow_run_id"] += 1
    assert any(
        "do not share one workflow run" in failure
        for failure in guard.operational_check_failures(
            split_run,
            policy_sha256=digest,
            source_commit=SOURCE,
            expected_pull_request_number=87,
            after_state=after_state,
        )
    )
    substituted = deepcopy(operational)
    substituted["success"]["checks"][0]["check_run_id"] += 100
    assert any(
        "do not follow the same check run" in failure
        for failure in guard.operational_check_failures(
            substituted,
            policy_sha256=digest,
            source_commit=SOURCE,
            expected_pull_request_number=87,
            after_state=after_state,
        )
    )
    deleted_rule = deepcopy(operational)
    deleted_rule["pending"]["rulesets"] = []
    deleted_rule["pending"]["pagination"]["rulesets"]["item_count"] = 0
    deleted_rule["pending"]["pagination"]["rulesets"][
        "projection_sha256"
    ] = guard.canonical_sha256([])
    assert any(
        "live governance projection differs" in failure
        for failure in guard.operational_check_failures(
            deleted_rule,
            policy_sha256=digest,
            source_commit=SOURCE,
            expected_pull_request_number=87,
            after_state=after_state,
        )
    )


def test_review_prose_cannot_upgrade_blocked_independence() -> None:
    guard = load_guard()
    failures = guard.review_prose_failures(
        {
            "known-bad": {
                "status": "The repository is independently reviewed."
            }
        }
    )
    assert failures
    assert "falsely claims independent review" in failures[0]
    assert (
        guard.review_prose_failures(
            {"known-good": {"independent_review_status": "blocked"}}
        )
        == []
    )


def test_result_cannot_precede_evidence_or_overclaim(tmp_path: Path) -> None:
    guard = load_guard()
    result = tmp_path / guard.RESULT_RELATIVE
    assert guard.result_failures(tmp_path, evidence_complete=False) == []
    assert guard.result_failures(tmp_path, evidence_complete=True) == [
        "iter239 RESULT.md is required when complete G0-G5 evidence exists"
    ]
    result.parent.mkdir(parents=True)
    result.write_text(
        "\n".join(
            [
                "technical-control status: supported",
                "independent-review status: blocked",
                "overall governance status: blocked",
                "",
            ]
        ),
        encoding="utf-8",
    )
    assert guard.result_failures(tmp_path, evidence_complete=True) == []
    assert any(
        "complete G0-G5 evidence is absent" in failure
        for failure in guard.result_failures(
            tmp_path,
            evidence_complete=False,
        )
    )
    result.write_text(
        result.read_text(encoding="utf-8") + "The repository is secure.\n",
        encoding="utf-8",
    )
    assert any(
        "forbidden overclaim" in failure
        for failure in guard.result_failures(
            tmp_path,
            evidence_complete=True,
        )
    )


def test_abort_record_is_structurally_validated_but_never_accepted(
    tmp_path: Path,
) -> None:
    guard = load_guard()
    _policy, policy_raw = load_policy(guard)
    policy_sha256 = guard.sha256_bytes(policy_raw)
    before_path = tmp_path / guard.EVIDENCE_RELATIVES["before_state"]
    before_path.parent.mkdir(parents=True)
    before_path.write_bytes(
        guard.canonical_json_bytes(
            {
                "policy_sha256": policy_sha256,
                "repository": guard.REPOSITORY,
                "schema_version": guard.BEFORE_SCHEMA,
                "source_commit": SOURCE,
            }
        )
    )
    available = {
        label: (
            guard.sha256_bytes(before_path.read_bytes())
            if label == "before_state"
            else None
        )
        for label in guard.EVIDENCE_RELATIVES
    }
    counts = {
        key: 0
        for key in guard.HTTP_METHODS | guard.SEMANTIC_MUTATIONS
    }
    counts["GET"] = 14
    abort = {
        "available_evidence_sha256": available,
        "classification": "inconclusive",
        "dispatch_attempt": None,
        "phase": "precondition",
        "policy_sha256": policy_sha256,
        "reason_code": "precondition_drift",
        "recorded_at": "2026-07-19T12:00:00Z",
        "repository": guard.REPOSITORY,
        "request_counts": counts,
        "schema_version": guard.ABORT_SCHEMA,
        "source_commit": SOURCE,
    }
    assert guard.abort_record_failures(
        root=tmp_path,
        abort=abort,
        policy_sha256=policy_sha256,
    ) == []
    false_success = deepcopy(abort)
    false_success["request_counts"]["POST"] = 1
    assert any(
        "dispatch attempt (0)" in failure
        for failure in guard.abort_record_failures(
            root=tmp_path,
            abort=false_success,
            policy_sha256=policy_sha256,
        )
    )
    before_path.write_bytes(b"drift evidence\n")
    malformed = deepcopy(abort)
    malformed["available_evidence_sha256"]["before_state"] = (
        guard.sha256_bytes(before_path.read_bytes())
    )
    assert any(
        "canonical JSON" in failure or "strict JSON" in failure
        for failure in guard.abort_record_failures(
            root=tmp_path,
            abort=malformed,
            policy_sha256=policy_sha256,
        )
    )


def test_abort_record_classifies_unobserved_postcondition_as_inconclusive(
    tmp_path: Path,
) -> None:
    guard = load_guard()
    _policy, policy_raw = load_policy(guard)
    policy_sha256 = guard.sha256_bytes(policy_raw)
    retained = {
        "before_state": guard.canonical_json_bytes(
            {
                "policy_sha256": policy_sha256,
                "repository": guard.REPOSITORY,
                "schema_version": guard.BEFORE_SCHEMA,
                "source_commit": SOURCE,
            }
        ),
        "mutation_intent": guard.canonical_json_bytes(
            {
                "policy_sha256": policy_sha256,
                "repository": guard.REPOSITORY,
                "schema_version": guard.INTENT_SCHEMA,
                "source_commit": SOURCE,
            }
        ),
    }
    available = {
        label: None
        for label in guard.EVIDENCE_RELATIVES
    }
    for label, raw in retained.items():
        path = tmp_path / guard.EVIDENCE_RELATIVES[label]
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)
        available[label] = guard.sha256_bytes(raw)
    counts = {
        key: 0
        for key in guard.HTTP_METHODS | guard.SEMANTIC_MUTATIONS
    }
    counts["GET"] = 15
    counts["POST"] = 1
    abort = {
        "available_evidence_sha256": available,
        "classification": "inconclusive",
        "dispatch_attempt": {
            "consumed_at": "2026-07-19T12:00:02Z",
            "endpoint": guard.CREATE_ENDPOINT,
            "method": "POST",
            "mutation_intent_sha256": available["mutation_intent"],
            "schema_version": guard.DISPATCH_SCHEMA,
            "source_commit": SOURCE,
            "write_guards": {
                "directory_fsync_completed": True,
                "exclusive_create": True,
                "file_fsync_completed": True,
            },
        },
        "phase": "postcondition",
        "policy_sha256": policy_sha256,
        "reason_code": "postcondition_unobserved",
        "recorded_at": "2026-07-19T12:00:00Z",
        "repository": guard.REPOSITORY,
        "request_counts": counts,
        "schema_version": guard.ABORT_SCHEMA,
        "source_commit": SOURCE,
    }
    assert guard.abort_record_failures(
        root=tmp_path,
        abort=abort,
        policy_sha256=policy_sha256,
    ) == []

    after_raw = guard.canonical_json_bytes(
        {
            "policy_sha256": policy_sha256,
            "repository": guard.REPOSITORY,
            "schema_version": guard.AFTER_SCHEMA,
            "source_commit": SOURCE,
        }
    )
    after_path = tmp_path / guard.EVIDENCE_RELATIVES["after_state"]
    after_path.write_bytes(after_raw)
    with_after = deepcopy(abort)
    with_after["available_evidence_sha256"]["after_state"] = (
        guard.sha256_bytes(after_raw)
    )
    assert guard.abort_record_failures(
        root=tmp_path,
        abort=with_after,
        policy_sha256=policy_sha256,
    ) == []


def test_abort_record_retains_unattempted_dispatch_without_post(
    tmp_path: Path,
) -> None:
    guard = load_guard()
    _policy, policy_raw = load_policy(guard)
    policy_sha256 = guard.sha256_bytes(policy_raw)
    available = {
        label: None
        for label in guard.EVIDENCE_RELATIVES
    }
    for label, schema in (
        ("before_state", guard.BEFORE_SCHEMA),
        ("mutation_intent", guard.INTENT_SCHEMA),
    ):
        raw = guard.canonical_json_bytes(
            {
                "policy_sha256": policy_sha256,
                "repository": guard.REPOSITORY,
                "schema_version": schema,
                "source_commit": SOURCE,
            }
        )
        path = tmp_path / guard.EVIDENCE_RELATIVES[label]
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)
        available[label] = guard.sha256_bytes(raw)
    counts = {
        key: 0
        for key in guard.HTTP_METHODS | guard.SEMANTIC_MUTATIONS
    }
    counts["GET"] = 14
    abort = {
        "available_evidence_sha256": available,
        "classification": "inconclusive",
        "dispatch_attempt": None,
        "phase": "dispatch",
        "policy_sha256": policy_sha256,
        "reason_code": "dispatch_not_attempted",
        "recorded_at": "2026-07-19T12:00:02Z",
        "repository": guard.REPOSITORY,
        "request_counts": counts,
        "schema_version": guard.ABORT_SCHEMA,
        "source_commit": SOURCE,
    }
    assert guard.abort_record_failures(
        root=tmp_path,
        abort=abort,
        policy_sha256=policy_sha256,
    ) == []

    fabricated = deepcopy(abort)
    fabricated["request_counts"]["POST"] = 1
    assert any(
        "dispatch attempt (0)" in failure
        for failure in guard.abort_record_failures(
            root=tmp_path,
            abort=fabricated,
            policy_sha256=policy_sha256,
        )
    )


def test_source_commits_bind_transaction_operational_and_current_instruments(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    guard = load_guard()
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(
        ["git", "config", "user.email", "iter239@example.invalid"],
        cwd=tmp_path,
        check=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "iter239 fixture"],
        cwd=tmp_path,
        check=True,
    )
    fixture_relatives = {
        *guard.SOURCE_BOUND_RELATIVES,
        guard.DRIVER_TEST_RELATIVE,
    }
    for relative in fixture_relatives:
        path = tmp_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f"activation {relative.as_posix()}\n", encoding="utf-8")
    subprocess.run(["git", "add", "."], cwd=tmp_path, check=True)
    subprocess.run(
        ["git", "commit", "-qm", "activation"],
        cwd=tmp_path,
        check=True,
    )
    activation = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=tmp_path,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    monkeypatch.setattr(guard, "ACTIVATION_COMMIT", activation)
    driver = tmp_path / "scripts/configure_repository_governance.py"
    driver.write_text("transaction implementation\n", encoding="utf-8")
    subprocess.run(["git", "add", "."], cwd=tmp_path, check=True)
    subprocess.run(
        ["git", "commit", "-qm", "transaction implementation"],
        cwd=tmp_path,
        check=True,
    )
    transaction_source = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=tmp_path,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    monkeypatch.setattr(
        guard,
        "TRANSACTION_SOURCE_COMMIT",
        transaction_source,
    )
    monkeypatch.setattr(
        guard,
        "TRANSACTION_INSTRUMENT_SHA256",
        {
            relative: guard.sha256_bytes(
                guard._git_blob(tmp_path, transaction_source, relative)
            )
            for relative in guard.SOURCE_BOUND_RELATIVES
        },
    )

    driver.write_text("operational implementation\n", encoding="utf-8")
    driver_test = tmp_path / guard.DRIVER_TEST_RELATIVE
    driver_test.write_text("operational regression\n", encoding="utf-8")
    subprocess.run(["git", "add", "."], cwd=tmp_path, check=True)
    subprocess.run(
        ["git", "commit", "-qm", "operational correction"],
        cwd=tmp_path,
        check=True,
    )
    operational_source = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=tmp_path,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    monkeypatch.setattr(
        guard,
        "OPERATIONAL_SOURCE_COMMIT",
        operational_source,
    )
    monkeypatch.setattr(
        guard,
        "OPERATIONAL_INSTRUMENT_SHA256",
        {
            relative: guard.sha256_bytes(
                guard._git_blob(tmp_path, operational_source, relative)
            )
            for relative in guard.SOURCE_BOUND_RELATIVES
        },
    )

    assert guard.source_commit_failures(
        tmp_path,
        source_commit=transaction_source,
    ) == []
    assert guard.operational_source_failures(
        tmp_path,
        ruleset_source=transaction_source,
        operational_source=operational_source,
    ) == []

    assert any(
        "exact retained transaction" in failure
        for failure in guard.source_commit_failures(
            tmp_path,
            source_commit=operational_source,
        )
    )

    policy = tmp_path / guard.POLICY_RELATIVE
    stable_policy = policy.read_bytes()
    policy.write_text("stable drift\n", encoding="utf-8")
    assert any(
        "exact current stable bytes" in failure
        for failure in guard.operational_source_failures(
            tmp_path,
            ruleset_source=transaction_source,
            operational_source=operational_source,
        )
    )
    policy.write_bytes(stable_policy)

    validator = tmp_path / "scripts/validate_iter239_repository_governance.py"
    validator_at_operational = validator.read_bytes()
    validator.write_text("uncommitted correction\n", encoding="utf-8")
    assert any(
        "differs from committed HEAD bytes" in failure
        for failure in guard.operational_source_failures(
            tmp_path,
            ruleset_source=transaction_source,
            operational_source=operational_source,
        )
    )
    validator.write_bytes(validator_at_operational)
    validator.write_text("committed provenance correction\n", encoding="utf-8")
    subprocess.run(["git", "add", "."], cwd=tmp_path, check=True)
    subprocess.run(
        ["git", "commit", "-qm", "validator provenance correction"],
        cwd=tmp_path,
        check=True,
    )
    assert guard.operational_source_failures(
        tmp_path,
        ruleset_source=transaction_source,
        operational_source=operational_source,
    ) == []


def test_known_bad_manifest_is_canonical_and_fully_exercised() -> None:
    guard = load_guard()
    manifest, _raw = guard.load_canonical_json(FIXTURE_PATH)
    assert manifest["schema_version"] == "telos.iter239.known_bad_manifest.v1"
    observed = {row["id"] for row in manifest["cases"]}
    assert len(observed) == len(manifest["cases"])
    exercised = (
        set(body_mutations(guard))
        | set(ci_mutations(b"x"))
        | {
            "ambiguous_without_reconciliation",
            "duplicate_json_key",
            "incomplete_pagination",
            "independent_review_claim",
            "nonfinite_json_value",
            "second_mutation_request",
            "stale_default_branch",
            "stale_source_head",
        }
    )
    assert observed == exercised == set(KNOWN_BAD_EXPECTED_ERRORS)
