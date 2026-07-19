#!/usr/bin/env python3
"""Validate iter239's repository-governance policy and retained evidence.

The default mode is phase aware.  It accepts a committed implementation whose
five live-evidence files are all absent, but it never treats that prospective
state as acceptance.  Once any live-evidence file exists, the complete
five-file bundle is required and validated as one linked transaction.
``--require-complete`` additionally refuses the prospective state.

This module is deliberately credential free.  It reads repository bytes and
Git objects only; it does not import a GitHub client or inspect the network.
"""

from __future__ import annotations

import argparse
from copy import deepcopy
from datetime import datetime
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[1]
ITERATION_ROOT = Path("experiments/iter239_repository_governance")
POLICY_RELATIVE = ITERATION_ROOT / "policy.json"
PROOF_ROOT = ITERATION_ROOT / "proof"
RESULT_RELATIVE = ITERATION_ROOT / "RESULT.md"

POLICY_SCHEMA = "telos.iter239.repository_governance_policy.v1"
BEFORE_SCHEMA = "telos.iter239.before_state.v1"
INTENT_SCHEMA = "telos.iter239.mutation_intent.v1"
AFTER_SCHEMA = "telos.iter239.after_state.v1"
RECEIPT_SCHEMA = "telos.iter239.mutation_receipt.v1"
OPERATIONAL_SCHEMA = "telos.iter239.operational_check.v1"
ABORT_SCHEMA = "telos.iter239.abort_record.v1"
DISPATCH_SCHEMA = "telos.iter239.dispatch_attempt.v1"

REPOSITORY = "manfromnowhere143/telos"
DEFAULT_BRANCH = "master"
MERGED_MASTER_ANCHOR = "fb87af7eb15b5235a722a7bb3fd3a48962019188"
ACTIVATION_COMMIT = "746f225f6c3718a1c2190dc00496386600fb2c5c"
TRANSACTION_SOURCE_COMMIT = "6f06e0254ee47e70fdb632f902e5d7b450d5791a"
OPERATIONAL_SOURCE_COMMIT = "f593b5048585052671276c03940ef4df9154724c"
TRANSACTION_INSTRUMENT_SHA256 = {
    POLICY_RELATIVE: (
        "c0cd140f004f760c568c02c3857c80d252c098fa1590453f3930480904b4531c"
    ),
    Path(".github/workflows/ci.yml"): (
        "befe8d6e9ca5228d5d8d694ee343ca9f93cb2b912470f358f4aca1ee1b8f1267"
    ),
    Path("scripts/configure_repository_governance.py"): (
        "1b077763df27f2a7a533523dacb90400671c8097a3e8f50de2552270d6f56590"
    ),
    Path("scripts/validate_iter239_ci_workflow_delta.py"): (
        "44422e671b3a2dc096556821a10ec9497877a7b563459fedae51ca3486336157"
    ),
    Path("scripts/validate_iter239_repository_governance.py"): (
        "bc65107b7fc568c3bf68aac12af6108493a594069be056be24d8d49368075bfe"
    ),
}
OPERATIONAL_INSTRUMENT_SHA256 = {
    POLICY_RELATIVE: (
        "c0cd140f004f760c568c02c3857c80d252c098fa1590453f3930480904b4531c"
    ),
    Path(".github/workflows/ci.yml"): (
        "befe8d6e9ca5228d5d8d694ee343ca9f93cb2b912470f358f4aca1ee1b8f1267"
    ),
    Path("scripts/configure_repository_governance.py"): (
        "58d90362fa076cfce76e0a1a232a6fc35e4d1fcf5299909e4d11d4e8c468ec1a"
    ),
    Path("scripts/validate_iter239_ci_workflow_delta.py"): (
        "44422e671b3a2dc096556821a10ec9497877a7b563459fedae51ca3486336157"
    ),
    Path("scripts/validate_iter239_repository_governance.py"): (
        "bc65107b7fc568c3bf68aac12af6108493a594069be056be24d8d49368075bfe"
    ),
}
API_ORIGIN = "https://api.github.com"
API_VERSION = "2026-03-10"
CREATE_ENDPOINT = f"{API_ORIGIN}/repos/{REPOSITORY}/rulesets"
RULESET_NAME = "telos-default-branch-technical-floor-v1"
INTEGRATION_ID = 15368
WORKFLOW_ID = 309260095
WORKFLOW_RELATIVE = Path(".github/workflows/ci.yml")
SOURCE_BOUND_RELATIVES = (
    POLICY_RELATIVE,
    WORKFLOW_RELATIVE,
    Path("scripts/configure_repository_governance.py"),
    Path("scripts/validate_iter239_ci_workflow_delta.py"),
    Path("scripts/validate_iter239_repository_governance.py"),
)
GOVERNANCE_DRIVER_RELATIVE = Path(
    "scripts/configure_repository_governance.py"
)
GOVERNANCE_VALIDATOR_RELATIVE = Path(
    "scripts/validate_iter239_repository_governance.py"
)
DRIVER_TEST_RELATIVE = Path(
    "tests/test_iter239_repository_governance_driver.py"
)
INSTRUMENT_TRANSITION_RELATIVES = (
    GOVERNANCE_DRIVER_RELATIVE,
    DRIVER_TEST_RELATIVE,
)
OPERATIONAL_STABLE_RELATIVES = tuple(
    relative
    for relative in SOURCE_BOUND_RELATIVES
    if relative != GOVERNANCE_VALIDATOR_RELATIVE
) + (DRIVER_TEST_RELATIVE,)
BEFORE_JOB_NAME = b"verify py${{ matrix.python-version }}"
AFTER_JOB_NAME = b"verify ${{ github.event_name }} py${{ matrix.python-version }}"
HEX40 = re.compile(r"^[0-9a-f]{40}$")
HEX64 = re.compile(r"^[0-9a-f]{64}$")
UTC_SECOND = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
RFC3339 = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}"
    r"(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})$"
)

EVIDENCE_RELATIVES = {
    "after_state": PROOF_ROOT / "after_state.json",
    "before_state": PROOF_ROOT / "before_state.json",
    "mutation_intent": PROOF_ROOT / "mutation_intent.json",
    "mutation_receipt": PROOF_ROOT / "mutation_receipt.json",
    "operational_check": PROOF_ROOT / "operational_check.json",
}
ABORT_RELATIVE = PROOF_ROOT / "abort_record.json"
ABORT_OUTCOMES = {
    "failed": [
        "ambiguous_unresolved",
        "mismatched_created_ruleset",
    ],
    "inconclusive": [
        "dispatch_not_attempted",
        "precondition_drift",
        "postcondition_drift",
        "postcondition_unobserved",
    ],
}
EVIDENCE_SCHEMAS = {
    "after_state": AFTER_SCHEMA,
    "before_state": BEFORE_SCHEMA,
    "mutation_intent": INTENT_SCHEMA,
    "mutation_receipt": RECEIPT_SCHEMA,
    "operational_check": OPERATIONAL_SCHEMA,
}

EXPECTED_REQUEST_BODY: dict[str, Any] = {
    "name": RULESET_NAME,
    "target": "branch",
    "enforcement": "active",
    "bypass_actors": [],
    "conditions": {
        "ref_name": {
            "include": ["~DEFAULT_BRANCH", "refs/heads/master"],
            "exclude": [],
        }
    },
    "rules": [
        {"type": "deletion"},
        {"type": "non_fast_forward"},
        {
            "type": "pull_request",
            "parameters": {
                "allowed_merge_methods": ["merge"],
                "dismiss_stale_reviews_on_push": False,
                "require_code_owner_review": False,
                "require_last_push_approval": False,
                "required_approving_review_count": 0,
                "required_review_thread_resolution": True,
            },
        },
        {
            "type": "required_status_checks",
            "parameters": {
                "do_not_enforce_on_create": False,
                "required_status_checks": [
                    {
                        "context": "verify pull_request py3.11",
                        "integration_id": INTEGRATION_ID,
                    },
                    {
                        "context": "verify pull_request py3.12",
                        "integration_id": INTEGRATION_ID,
                    },
                ],
                "strict_required_status_checks_policy": True,
            },
        },
    ],
}

EXPECTED_BEFORE_PROJECTIONS: dict[str, Any] = {
    "repository": {
        "default_branch": DEFAULT_BRANCH,
        "full_name": REPOSITORY,
        "merge_settings": {
            "allow_merge_commit": True,
            "allow_rebase_merge": True,
            "allow_squash_merge": True,
        },
        "visibility": "public",
    },
    "branch": {
        "name": DEFAULT_BRANCH,
        "protected": False,
        "sha": MERGED_MASTER_ANCHOR,
    },
    "classic_protection": {
        "classification": "absent",
        "http_status": 404,
    },
    "rulesets": [],
    "named_rulesets": [],
    "effective_rules": [],
    "collaborators": [{"login": "manfromnowhere143", "role_name": "admin"}],
    "invitations": [],
    "actions": {
        "allowed_actions": "all",
        "enabled": True,
        "sha_pinning_required": False,
    },
    "default_workflow_permissions": {
        "can_approve_pull_request_reviews": False,
        "default_workflow_permissions": "read",
    },
    "fork_pull_request_policy": {
        "approval_policy": "first_time_contributors",
    },
}

PAGINATION_KEYS_BEFORE = {
    "actions",
    "branch",
    "checks",
    "classic_protection",
    "collaborators",
    "default_workflow_permissions",
    "effective_rules",
    "fork_pull_request_policy",
    "invitations",
    "named_rulesets",
    "open_pull_request",
    "repository",
    "rulesets",
    "source_ref",
}
PAGINATION_KEYS_AFTER = {
    "actions",
    "branch",
    "collaborators",
    "default_workflow_permissions",
    "effective_rules",
    "fork_pull_request_policy",
    "invitations",
    "named_ruleset",
    "repository",
    "ruleset_history",
    "rulesets",
}

HTTP_METHODS = {"DELETE", "GET", "PATCH", "POST", "PUT"}
SEMANTIC_MUTATIONS = {
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
}
UNCHANGED_PROJECTIONS = [
    "actions",
    "collaborators",
    "default_workflow_permissions",
    "fork_pull_request_policy",
    "invitations",
    "repository",
]
FORBIDDEN_REVIEW_PATTERNS = (
    re.compile(r"\bindependent(?:ly)? reviewed\b", re.IGNORECASE),
    re.compile(r"\bindependent review (?:is |was )?(?:established|supported)\b", re.IGNORECASE),
    re.compile(r"\breview assurance (?:is |was )?(?:established|supported)\b", re.IGNORECASE),
    re.compile(r"\bapproved by (?:an )?independent\b", re.IGNORECASE),
)
FORBIDDEN_RESULT_PATTERNS = (
    *FORBIDDEN_REVIEW_PATTERNS,
    re.compile(r"\bscientifically validated\b", re.IGNORECASE),
    re.compile(r"\btamper[- ]proof\b", re.IGNORECASE),
    re.compile(r"\bproduction[- ]ready\b", re.IGNORECASE),
    re.compile(r"\bstate of the art\b", re.IGNORECASE),
    re.compile(r"\bautonomous\b", re.IGNORECASE),
    re.compile(r"\bsecure\b", re.IGNORECASE),
)


class GovernanceError(ValueError):
    """An iter239 artifact is ambiguous or not canonical."""


def canonical_json_bytes(value: Any) -> bytes:
    """Return the one accepted JSON representation."""

    try:
        rendered = json.dumps(
            value,
            indent=2,
            sort_keys=True,
            allow_nan=False,
        )
    except (TypeError, ValueError) as exc:
        raise GovernanceError(f"cannot render canonical JSON: {exc}") from exc
    return (rendered + "\n").encode("utf-8")


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def canonical_sha256(value: Any) -> str:
    return sha256_bytes(canonical_json_bytes(value))


def _json_exact(observed: object, expected: object) -> bool:
    """Compare JSON values without Python's bool/int equality coercion."""

    try:
        return canonical_json_bytes(observed) == canonical_json_bytes(expected)
    except (GovernanceError, TypeError, ValueError):
        return False


def load_canonical_json_bytes(raw: bytes, *, label: str) -> dict[str, Any]:
    """Load one canonical JSON object, rejecting duplicate and non-finite data."""

    duplicates: list[str] = []

    def unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                duplicates.append(key)
            result[key] = value
        return result

    try:
        value = json.loads(
            raw,
            object_pairs_hook=unique_object,
            parse_constant=lambda token: (_ for _ in ()).throw(
                GovernanceError(f"non-finite JSON value: {token}")
            ),
        )
    except (UnicodeError, json.JSONDecodeError, GovernanceError) as exc:
        raise GovernanceError(f"{label}: strict JSON parse failed: {exc}") from exc
    if duplicates:
        raise GovernanceError(
            f"{label}: duplicate JSON keys: {sorted(set(duplicates))}"
        )
    if not isinstance(value, dict):
        raise GovernanceError(f"{label}: JSON root must be an object")
    if raw != canonical_json_bytes(value):
        raise GovernanceError(f"{label}: JSON bytes are not canonical")
    return value


def load_canonical_json(path: Path) -> tuple[dict[str, Any], bytes]:
    try:
        raw = path.read_bytes()
    except OSError as exc:
        raise GovernanceError(f"{path}: cannot read: {exc}") from exc
    return load_canonical_json_bytes(raw, label=str(path)), raw


def _exact_keys(
    value: object,
    expected: Iterable[str],
    *,
    label: str,
) -> list[str]:
    if not isinstance(value, dict):
        return [f"{label}: must be an object"]
    expected_set = set(expected)
    actual = set(value)
    failures: list[str] = []
    missing = sorted(expected_set - actual)
    extra = sorted(actual - expected_set)
    if missing:
        failures.append(f"{label}: missing keys: {missing}")
    if extra:
        failures.append(f"{label}: unexpected keys: {extra}")
    return failures


def _is_int(value: object, *, minimum: int = 0) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= minimum


def _is_utc_second(value: object) -> bool:
    if not isinstance(value, str) or UTC_SECOND.fullmatch(value) is None:
        return False
    try:
        datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ")
    except ValueError:
        return False
    return True


def _is_rfc3339(value: object) -> bool:
    if not isinstance(value, str) or RFC3339.fullmatch(value) is None:
        return False
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return False
    return parsed.tzinfo is not None


def _git(root: Path, *arguments: str) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        ["git", *arguments],
        cwd=root,
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def _git_blob(root: Path, commit: str, relative: Path) -> bytes | None:
    result = _git(root, "show", f"{commit}:{relative.as_posix()}")
    if result.returncode != 0:
        return None
    return result.stdout


def request_body_failures(body: object, *, label: str) -> list[str]:
    """Explain exact technical-floor deviations without normalizing them away."""

    failures = _exact_keys(
        body,
        {
            "bypass_actors",
            "conditions",
            "enforcement",
            "name",
            "rules",
            "target",
        },
        label=label,
    )
    if not isinstance(body, dict):
        return failures
    if body.get("name") != RULESET_NAME:
        failures.append(f"{label}: ruleset name differs")
    if body.get("target") != "branch":
        failures.append(f"{label}: target must be branch")
    if body.get("enforcement") != "active":
        failures.append(f"{label}: enforcement must be active")
    if body.get("bypass_actors") != []:
        failures.append(f"{label}: bypass actors must be exactly empty")

    conditions = body.get("conditions")
    if not isinstance(conditions, dict) or set(conditions) != {"ref_name"}:
        failures.append(f"{label}: conditions must contain only ref_name")
    else:
        ref_name = conditions.get("ref_name")
        expected_ref = {
            "include": ["~DEFAULT_BRANCH", "refs/heads/master"],
            "exclude": [],
        }
        if not _json_exact(ref_name, expected_ref):
            failures.append(
                f"{label}: refs must be exactly the default-branch and master selectors"
            )

    rules = body.get("rules")
    expected_types = [
        "deletion",
        "non_fast_forward",
        "pull_request",
        "required_status_checks",
    ]
    if not isinstance(rules, list):
        failures.append(f"{label}: rules must be an ordered list")
    else:
        types = [
            rule.get("type") if isinstance(rule, dict) else None
            for rule in rules
        ]
        if types != expected_types:
            failures.append(
                f"{label}: rule types must be exactly {expected_types}, observed {types}"
            )
        if len(rules) == 4 and all(isinstance(rule, dict) for rule in rules):
            if not _json_exact(rules[0], {"type": "deletion"}):
                failures.append(f"{label}: deletion rule differs")
            if not _json_exact(rules[1], {"type": "non_fast_forward"}):
                failures.append(f"{label}: non-fast-forward rule differs")
            pull = rules[2]
            pull_parameters = pull.get("parameters")
            expected_pull = EXPECTED_REQUEST_BODY["rules"][2]["parameters"]
            if not _json_exact(pull_parameters, expected_pull):
                failures.append(
                    f"{label}: pull-request parameters must be merge-only, "
                    "conversation-resolved, and zero-approval"
                )
            status = rules[3]
            status_parameters = status.get("parameters")
            expected_status = EXPECTED_REQUEST_BODY["rules"][3]["parameters"]
            if not _json_exact(status_parameters, expected_status):
                failures.append(
                    f"{label}: required checks must be the exact strict "
                    "pull-request contexts bound to app 15368"
                )
    if not _json_exact(body, EXPECTED_REQUEST_BODY):
        failures.append(f"{label}: request body differs from the frozen policy")
    return failures


def policy_failures(policy: object) -> list[str]:
    failures = _exact_keys(
        policy,
        {
            "abort_outcomes",
            "api",
            "artifact_paths",
            "ci",
            "expected_before",
            "mutation_budget",
            "repository",
            "request_body",
            "request_body_sha256",
            "schema_version",
        },
        label="policy",
    )
    if not isinstance(policy, dict):
        return failures
    if policy.get("schema_version") != POLICY_SCHEMA:
        failures.append("policy: schema_version differs")
    if not _json_exact(policy.get("abort_outcomes"), ABORT_OUTCOMES):
        failures.append("policy: abort outcome contract differs")
    expected_repository = {
        "default_branch": DEFAULT_BRANCH,
        "full_name": REPOSITORY,
        "merged_master_anchor": MERGED_MASTER_ANCHOR,
        "visibility": "public",
    }
    if not _json_exact(policy.get("repository"), expected_repository):
        failures.append("policy: repository identity or anchor differs")
    expected_api = {
        "create_endpoint": CREATE_ENDPOINT,
        "origin": API_ORIGIN,
        "version": API_VERSION,
    }
    if not _json_exact(policy.get("api"), expected_api):
        failures.append("policy: fixed TLS API origin, endpoint, or version differs")
    expected_paths = {
        key: relative.as_posix()
        for key, relative in sorted(EVIDENCE_RELATIVES.items())
    }
    expected_paths["abort_record"] = ABORT_RELATIVE.as_posix()
    expected_paths = dict(sorted(expected_paths.items()))
    if not _json_exact(policy.get("artifact_paths"), expected_paths):
        failures.append("policy: evidence artifact paths differ")
    expected_ci = {
        "after_job_name": AFTER_JOB_NAME.decode(),
        "anchor_commit": MERGED_MASTER_ANCHOR,
        "before_job_name": BEFORE_JOB_NAME.decode(),
        "integration_id": INTEGRATION_ID,
        "pull_request_contexts": [
            "verify pull_request py3.11",
            "verify pull_request py3.12",
        ],
        "push_contexts": ["verify push py3.11", "verify push py3.12"],
        "workflow_id": WORKFLOW_ID,
        "workflow_path": WORKFLOW_RELATIVE.as_posix(),
    }
    if not _json_exact(policy.get("ci"), expected_ci):
        failures.append("policy: CI event/context contract differs")
    expected_before = {
        "actions": EXPECTED_BEFORE_PROJECTIONS["actions"],
        "branch": EXPECTED_BEFORE_PROJECTIONS["branch"],
        "classic_protection": EXPECTED_BEFORE_PROJECTIONS["classic_protection"],
        "collaborators": EXPECTED_BEFORE_PROJECTIONS["collaborators"],
        "default_workflow_permissions": EXPECTED_BEFORE_PROJECTIONS[
            "default_workflow_permissions"
        ],
        "effective_rules": [],
        "fork_pull_request_policy": EXPECTED_BEFORE_PROJECTIONS[
            "fork_pull_request_policy"
        ],
        "invitations": [],
        "merge_settings": {
            "allow_merge_commit": True,
            "allow_rebase_merge": True,
            "allow_squash_merge": True,
        },
        "repository": {
            "default_branch": DEFAULT_BRANCH,
            "full_name": REPOSITORY,
            "visibility": "public",
        },
        "rulesets": [],
    }
    if not _json_exact(policy.get("expected_before"), expected_before):
        failures.append("policy: frozen pre-mutation projection differs")
    budget = policy.get("mutation_budget")
    if not _json_exact(
        budget,
        {"DELETE": 0, "GET": 96, "PATCH": 0, "POST": 1, "PUT": 0},
    ):
        failures.append("policy: finite HTTP request budget differs")
    body = policy.get("request_body")
    failures.extend(request_body_failures(body, label="policy request_body"))
    if isinstance(body, dict):
        expected_digest = canonical_sha256(body)
        if policy.get("request_body_sha256") != expected_digest:
            failures.append("policy: request_body_sha256 differs from canonical body")
    return failures


def ci_evolution_failures(before: bytes, after: bytes) -> list[str]:
    """Accept exactly one display-name substitution and no other workflow byte."""

    failures: list[str] = []
    if before.count(BEFORE_JOB_NAME) != 1:
        failures.append("CI anchor: original job display name is absent or duplicated")
        return failures
    if AFTER_JOB_NAME in before:
        failures.append("CI anchor: event-specific job display name already existed")
        return failures
    expected = before.replace(BEFORE_JOB_NAME, AFTER_JOB_NAME, 1)
    if after != expected:
        failures.append(
            "CI workflow: bytes differ beyond the exact event-specific "
            "job-display-name substitution"
        )
    if after.count(AFTER_JOB_NAME) != 1:
        failures.append(
            "CI workflow: event-specific job display name is absent or duplicated"
        )
    if BEFORE_JOB_NAME in after:
        failures.append("CI workflow: ambiguous legacy job display name remains")
    return failures


def current_ci_failures(root: Path) -> list[str]:
    before = _git_blob(root, MERGED_MASTER_ANCHOR, WORKFLOW_RELATIVE)
    if before is None:
        return ["CI workflow: cannot load frozen merged-master anchor blob"]
    try:
        after = (root / WORKFLOW_RELATIVE).read_bytes()
    except OSError as exc:
        return [f"CI workflow: cannot read current bytes: {exc}"]
    return ci_evolution_failures(before, after)


def _identity_failures(
    document: dict[str, Any],
    *,
    schema: str,
    label: str,
    expected_keys: set[str],
    policy_sha256: str,
) -> list[str]:
    failures = _exact_keys(document, expected_keys, label=label)
    if document.get("schema_version") != schema:
        failures.append(f"{label}: schema_version differs")
    if document.get("repository") != REPOSITORY:
        failures.append(f"{label}: repository differs")
    if document.get("policy_sha256") != policy_sha256:
        failures.append(f"{label}: policy_sha256 differs from policy bytes")
    source = document.get("source_commit")
    if not isinstance(source, str) or HEX40.fullmatch(source) is None:
        failures.append(f"{label}: source_commit must be lowercase 40-hex")
    return failures


def _method_count_failures(
    value: object,
    *,
    label: str,
    allow_post: bool,
) -> list[str]:
    failures = _exact_keys(value, HTTP_METHODS, label=label)
    if not isinstance(value, dict):
        return failures
    for method in sorted(HTTP_METHODS):
        count = value.get(method)
        if not _is_int(count):
            failures.append(f"{label}: {method} must be a nonnegative integer")
    if all(_is_int(value.get(method)) for method in HTTP_METHODS):
        if value["GET"] < 1:
            failures.append(f"{label}: GET count must be positive")
        for method in ("DELETE", "PATCH", "PUT"):
            if value[method] != 0:
                failures.append(f"{label}: {method} count must be zero")
        expected_post = 1 if allow_post else 0
        if value["POST"] != expected_post:
            failures.append(f"{label}: POST count must be {expected_post}")
    return failures


def _pagination_failures(
    value: object,
    *,
    expected_endpoints: set[str],
    projections: object,
    label: str,
    status_overrides: dict[str, int] | None = None,
) -> list[str]:
    failures = _exact_keys(value, expected_endpoints, label=label)
    if not isinstance(value, dict):
        return failures
    for endpoint, page in sorted(value.items()):
        page_label = f"{label}.{endpoint}"
        failures.extend(
            _exact_keys(
                page,
                {
                    "complete",
                    "http_statuses",
                    "item_count",
                    "page_count",
                    "projection_sha256",
                    "request_count",
                },
                label=page_label,
            )
        )
        if not isinstance(page, dict):
            continue
        if page.get("complete") is not True:
            failures.append(f"{page_label}: pagination must be complete")
        if not _is_int(page.get("page_count"), minimum=1):
            failures.append(f"{page_label}: page_count must be a positive integer")
        if not _is_int(page.get("request_count"), minimum=1):
            failures.append(
                f"{page_label}: request_count must be a positive integer"
            )
        if (
            _is_int(page.get("page_count"), minimum=1)
            and _is_int(page.get("request_count"), minimum=1)
            and page["request_count"] < page["page_count"]
        ):
            failures.append(
                f"{page_label}: request_count cannot be below page_count"
            )
        if not _is_int(page.get("item_count")):
            failures.append(f"{page_label}: item_count must be nonnegative")
        statuses = page.get("http_statuses")
        if not isinstance(statuses, list) or not all(
            _is_int(status, minimum=100) and status <= 599
            for status in statuses
        ):
            failures.append(
                f"{page_label}: http_statuses must be a list of HTTP status integers"
            )
        elif _is_int(page.get("request_count"), minimum=1):
            if len(statuses) != page["request_count"]:
                failures.append(
                    f"{page_label}: HTTP status count differs from request_count"
                )
            expected_status = (status_overrides or {}).get(endpoint, 200)
            if statuses != [expected_status] * page["request_count"]:
                failures.append(
                    f"{page_label}: HTTP statuses differ from the exact "
                    f"expected {expected_status} responses"
                )
        if isinstance(projections, dict) and endpoint in projections:
            projection = projections[endpoint]
            if isinstance(projection, list):
                expected_count = len(projection)
            elif (
                endpoint == "ruleset_history"
                and isinstance(projection, dict)
                and isinstance(projection.get("entries"), list)
            ):
                expected_count = len(projection["entries"])
            else:
                expected_count = 1
            if page.get("item_count") != expected_count:
                failures.append(
                    f"{page_label}: item_count differs from retained projection"
                )
            if page.get("projection_sha256") != canonical_sha256(projection):
                failures.append(
                    f"{page_label}: projection_sha256 differs from retained projection"
                )
        elif isinstance(page, dict):
            failures.append(f"{page_label}: retained projection is absent")
    return failures


def _check_run_failures(
    value: object,
    *,
    source_commit: str,
    expected_status: str,
    include_push: bool,
    label: str,
) -> list[str]:
    if not isinstance(value, list):
        return [f"{label}: must be a list"]
    failures: list[str] = []
    expected_names = {
        "verify pull_request py3.11": "pull_request",
        "verify pull_request py3.12": "pull_request",
    }
    if include_push:
        expected_names.update(
            {
                "verify push py3.11": "push",
                "verify push py3.12": "push",
            }
        )
    observed: list[str] = []
    for index, row in enumerate(value):
        row_label = f"{label}[{index}]"
        failures.extend(
            _exact_keys(
                row,
                {
                    "attempt",
                    "check_run_id",
                    "check_suite_id",
                    "conclusion",
                    "event",
                    "head_sha",
                    "integration_id",
                    "name",
                    "status",
                    "workflow_id",
                    "workflow_path",
                    "workflow_run_id",
                },
                label=row_label,
            )
        )
        if not isinstance(row, dict):
            continue
        name = row.get("name")
        if isinstance(name, str):
            observed.append(name)
        if name not in expected_names:
            failures.append(f"{row_label}: unexpected or ambiguous check name")
        elif row.get("event") != expected_names[name]:
            failures.append(f"{row_label}: check event does not match its context")
        if row.get("head_sha") != source_commit:
            failures.append(f"{row_label}: check head is stale")
        if row.get("integration_id") != INTEGRATION_ID:
            failures.append(f"{row_label}: check is not bound to app 15368")
        if row.get("workflow_id") != WORKFLOW_ID:
            failures.append(f"{row_label}: check is not bound to CI workflow 309260095")
        if row.get("workflow_path") != WORKFLOW_RELATIVE.as_posix():
            failures.append(f"{row_label}: check workflow path differs")
        if not _is_int(row.get("attempt"), minimum=1) or row.get("attempt") != 1:
            failures.append(f"{row_label}: check must be attempt one")
        for identity in ("check_run_id", "check_suite_id", "workflow_run_id"):
            if not _is_int(row.get(identity), minimum=1):
                failures.append(f"{row_label}: {identity} must be positive")
        if expected_status == "success":
            if row.get("status") != "completed" or row.get("conclusion") != "success":
                failures.append(f"{row_label}: check must be completed success")
        elif expected_status == "pending":
            if row.get("status") not in {"queued", "in_progress", "pending"}:
                failures.append(f"{row_label}: check must be pending")
            if row.get("conclusion") is not None:
                failures.append(f"{row_label}: pending check conclusion must be null")
    if sorted(observed) != sorted(expected_names):
        failures.append(f"{label}: checks must contain each exact context once")
    rows = [row for row in value if isinstance(row, dict)]
    check_run_ids = [row.get("check_run_id") for row in rows]
    if (
        all(_is_int(identity, minimum=1) for identity in check_run_ids)
        and len(check_run_ids) != len(set(check_run_ids))
    ):
        failures.append(f"{label}: check_run_id values must be unique")
    event_groups: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        event = row.get("event")
        if isinstance(event, str):
            event_groups.setdefault(event, []).append(row)
    expected_events = {"pull_request", "push"} if include_push else {"pull_request"}
    if set(event_groups) != expected_events:
        failures.append(f"{label}: event groups differ from {sorted(expected_events)}")
    for event, group in sorted(event_groups.items()):
        if len(group) != 2:
            failures.append(f"{label}: {event} must contain exactly two matrix checks")
            continue
        workflow_run_values = [row.get("workflow_run_id") for row in group]
        suite_values = [row.get("check_suite_id") for row in group]
        if (
            all(_is_int(identity, minimum=1) for identity in workflow_run_values)
            and len(set(workflow_run_values)) != 1
        ):
            failures.append(
                f"{label}: {event} matrix checks do not share one workflow run"
            )
        if (
            all(_is_int(identity, minimum=1) for identity in suite_values)
            and len(set(suite_values)) != 1
        ):
            failures.append(
                f"{label}: {event} matrix checks do not share one check suite"
            )
    if include_push and set(event_groups) == {"pull_request", "push"}:
        pull = event_groups["pull_request"][0]
        push = event_groups["push"][0]
        if pull.get("workflow_run_id") == push.get("workflow_run_id"):
            failures.append(
                f"{label}: push and pull_request must use distinct workflow runs"
            )
        if pull.get("check_suite_id") == push.get("check_suite_id"):
            failures.append(
                f"{label}: push and pull_request must use distinct check suites"
            )
    return failures


def before_state_failures(
    before: dict[str, Any],
    *,
    policy_sha256: str,
) -> list[str]:
    failures = _identity_failures(
        before,
        schema=BEFORE_SCHEMA,
        label="before_state",
        expected_keys={
            "api_version",
            "observed_at",
            "pagination",
            "policy_sha256",
            "projections",
            "repository",
            "request_counts",
            "schema_version",
            "source_commit",
        },
        policy_sha256=policy_sha256,
    )
    if before.get("api_version") != API_VERSION:
        failures.append("before_state: API version differs")
    if not _is_utc_second(before.get("observed_at")):
        failures.append("before_state: observed_at must be a UTC whole second")
    projections = before.get("projections")
    expected_projection_keys = set(EXPECTED_BEFORE_PROJECTIONS) | {
        "checks",
        "open_pull_request",
        "source_ref",
    }
    failures.extend(
        _exact_keys(
            projections,
            expected_projection_keys,
            label="before_state.projections",
        )
    )
    if not isinstance(projections, dict):
        return failures
    failures.extend(
        _method_count_failures(
            before.get("request_counts"),
            label="before_state.request_counts",
            allow_post=False,
        )
    )
    failures.extend(
        _pagination_failures(
            before.get("pagination"),
            expected_endpoints=PAGINATION_KEYS_BEFORE,
            projections=projections,
            label="before_state.pagination",
            status_overrides={"classic_protection": 404},
        )
    )
    counts = before.get("request_counts")
    pages = before.get("pagination")
    if isinstance(counts, dict) and isinstance(pages, dict):
        request_count = sum(
            page.get("request_count", 0)
            for page in pages.values()
            if isinstance(page, dict)
        )
        if counts.get("GET") != request_count:
            failures.append(
                "before_state: GET count must equal retained endpoint request count"
            )
    for key, expected in EXPECTED_BEFORE_PROJECTIONS.items():
        if not _json_exact(projections.get(key), expected):
            failures.append(f"before_state.projections.{key}: frozen precondition drift")
    source = before.get("source_commit")
    source_ref = projections.get("source_ref")
    if not _json_exact(
        source_ref,
        {
            "ref": (
                None
                if not isinstance(source, str)
                else "refs/heads/agent/iter239-repository-governance"
            ),
            "sha": source,
        },
    ):
        failures.append(
            "before_state.projections.source_ref: must be the exact iter239 branch head"
        )
    pull = projections.get("open_pull_request")
    failures.extend(
        _exact_keys(
            pull,
            {
                "base_ref",
                "base_repository",
                "head_ref",
                "head_repository",
                "head_sha",
                "number",
                "state",
            },
            label="before_state.projections.open_pull_request",
        )
    )
    if isinstance(pull, dict):
        if pull.get("base_ref") != DEFAULT_BRANCH:
            failures.append("before_state: open pull request base_ref differs")
        if pull.get("base_repository") != REPOSITORY:
            failures.append("before_state: open pull request base repository differs")
        if pull.get("head_ref") != "agent/iter239-repository-governance":
            failures.append("before_state: open pull request head_ref differs")
        if pull.get("head_repository") != REPOSITORY:
            failures.append("before_state: open pull request head repository differs")
        if pull.get("head_sha") != source:
            failures.append("before_state: open pull request head is stale")
        if pull.get("state") != "open":
            failures.append("before_state: pull request must be open")
        if not _is_int(pull.get("number"), minimum=1):
            failures.append("before_state: pull request number must be positive")
    if isinstance(source, str):
        failures.extend(
            _check_run_failures(
                projections.get("checks"),
                source_commit=source,
                expected_status="success",
                include_push=True,
                label="before_state.projections.checks",
            )
        )
    return failures


def mutation_intent_failures(
    intent: dict[str, Any],
    *,
    policy_sha256: str,
    before: dict[str, Any],
    before_raw: bytes,
    policy: dict[str, Any],
) -> list[str]:
    failures = _identity_failures(
        intent,
        schema=INTENT_SCHEMA,
        label="mutation_intent",
        expected_keys={
            "api_version",
            "before_state_sha256",
            "endpoint",
            "method",
            "persisted_at",
            "policy_sha256",
            "repository",
            "request_body",
            "request_body_sha256",
            "schema_version",
            "source_commit",
            "write_guards",
        },
        policy_sha256=policy_sha256,
    )
    if intent.get("source_commit") != before.get("source_commit"):
        failures.append("mutation_intent: source_commit differs from before_state")
    if intent.get("api_version") != API_VERSION:
        failures.append("mutation_intent: API version differs")
    if intent.get("endpoint") != CREATE_ENDPOINT:
        failures.append("mutation_intent: endpoint differs from fixed TLS endpoint")
    if intent.get("method") != "POST":
        failures.append("mutation_intent: method must be POST")
    if not _is_utc_second(intent.get("persisted_at")):
        failures.append("mutation_intent: persisted_at must be a UTC whole second")
    if intent.get("before_state_sha256") != sha256_bytes(before_raw):
        failures.append("mutation_intent: before_state_sha256 differs")
    failures.extend(
        request_body_failures(intent.get("request_body"), label="mutation_intent.request_body")
    )
    if not _json_exact(
        intent.get("request_body"),
        policy.get("request_body"),
    ):
        failures.append("mutation_intent: request body differs from policy")
    if intent.get("request_body_sha256") != policy.get("request_body_sha256"):
        failures.append("mutation_intent: request_body_sha256 differs from policy")
    expected_guards = {
        "directory_fsync_completed": True,
        "exclusive_create": True,
        "file_fsync_completed": True,
    }
    if not _json_exact(intent.get("write_guards"), expected_guards):
        failures.append(
            "mutation_intent: exclusive creation and file/directory fsync must be recorded"
        )
    return failures


def dispatch_attempt_failures(
    dispatch: object,
    *,
    label: str,
    source_commit: object,
    mutation_intent_sha256: object,
) -> list[str]:
    failures = _exact_keys(
        dispatch,
        {
            "consumed_at",
            "endpoint",
            "method",
            "mutation_intent_sha256",
            "schema_version",
            "source_commit",
            "write_guards",
        },
        label=label,
    )
    if not isinstance(dispatch, dict):
        return failures
    if dispatch.get("schema_version") != DISPATCH_SCHEMA:
        failures.append(f"{label}: schema_version differs")
    if dispatch.get("source_commit") != source_commit:
        failures.append(f"{label}: source_commit differs")
    if dispatch.get("mutation_intent_sha256") != mutation_intent_sha256:
        failures.append(f"{label}: mutation_intent_sha256 differs")
    if dispatch.get("endpoint") != CREATE_ENDPOINT:
        failures.append(f"{label}: endpoint differs from fixed TLS endpoint")
    if dispatch.get("method") != "POST":
        failures.append(f"{label}: method must be POST")
    if not _is_utc_second(dispatch.get("consumed_at")):
        failures.append(f"{label}: consumed_at must be a UTC whole second")
    if not _json_exact(
        dispatch.get("write_guards"),
        {
            "directory_fsync_completed": True,
            "exclusive_create": True,
            "file_fsync_completed": True,
        },
    ):
        failures.append(
            f"{label}: exclusive creation and file/directory fsync must be recorded"
        )
    return failures


def server_policy_normalization(
    request_policy: object,
    server_policy: object,
) -> tuple[dict[str, Any], dict[str, Any] | None]:
    entries: list[dict[str, str]] = []
    semantic_differences: list[str] = []
    if not isinstance(request_policy, dict) or not isinstance(server_policy, dict):
        semantic_differences.append("request or server policy is not an object")
        normalized = None
    else:
        normalized = deepcopy(server_policy)
        if "bypass_actors" not in normalized:
            normalized["bypass_actors"] = []
            entries.append(
                {
                    "classification": "omitted_empty_default",
                    "path": "$.bypass_actors",
                }
            )
        elif normalized.get("bypass_actors") != []:
            semantic_differences.append("server bypass_actors is not exactly empty")

        rules = normalized.get("rules")
        pull_rules = (
            [
                rule
                for rule in rules
                if isinstance(rule, dict) and rule.get("type") == "pull_request"
            ]
            if isinstance(rules, list)
            else []
        )
        if len(pull_rules) != 1:
            semantic_differences.append(
                "server policy does not contain exactly one pull_request rule"
            )
        else:
            parameters = pull_rules[0].get("parameters")
            if not isinstance(parameters, dict):
                semantic_differences.append(
                    "server pull_request parameters are not an object"
                )
            else:
                inert_defaults = {
                    "dismissal_restriction": {
                        "allowed_actors": [],
                        "enabled": False,
                    },
                    "required_reviewers": [],
                }
                for key, expected in inert_defaults.items():
                    if key not in parameters:
                        continue
                    if not _json_exact(parameters.get(key), expected):
                        semantic_differences.append(
                            f"server inert default differs: {key}"
                        )
                        continue
                    del parameters[key]
                    entries.append(
                        {
                            "classification": "inserted_inert_default",
                            "path": (
                                "$.rules[type=pull_request].parameters."
                                f"{key}"
                            ),
                        }
                    )
        if not _json_exact(normalized, request_policy):
            semantic_differences.append(
                "server policy remains different after registered normalization"
            )
    record = {
        "entries": entries,
        "request_policy_sha256": (
            canonical_sha256(request_policy)
            if isinstance(request_policy, dict)
            else None
        ),
        "semantic_differences": semantic_differences,
        "server_policy_sha256": (
            canonical_sha256(server_policy)
            if isinstance(server_policy, dict)
            else None
        ),
    }
    return record, normalized


def _ruleset_projection_failures(
    value: object,
    *,
    label: str,
    require_current_user_bypass: bool = True,
) -> list[str]:
    failures = _exact_keys(
        value,
        {
            "id",
            "normalization",
            "request_policy",
            "server_metadata",
            "server_policy",
            "source",
            "source_type",
        },
        label=label,
    )
    if not isinstance(value, dict):
        return failures
    if not _is_int(value.get("id"), minimum=1):
        failures.append(f"{label}: id must be positive")
    if value.get("source") != REPOSITORY:
        failures.append(f"{label}: repository source differs")
    if value.get("source_type") != "Repository":
        failures.append(f"{label}: source_type must be Repository")
    request_policy = value.get("request_policy")
    server_policy = value.get("server_policy")
    failures.extend(
        request_body_failures(
            request_policy,
            label=f"{label}.request_policy",
        )
    )
    expected_normalization, normalized = server_policy_normalization(
        request_policy,
        server_policy,
    )
    if not _json_exact(value.get("normalization"), expected_normalization):
        failures.append(
            f"{label}: server/request normalization record differs "
            "or has semantic differences"
        )
    if expected_normalization["semantic_differences"] or not _json_exact(
        normalized,
        request_policy,
    ):
        failures.append(
            f"{label}: server policy has unregistered or semantic differences"
        )
    metadata = value.get("server_metadata")
    failures.extend(
        _exact_keys(
            metadata,
            {
                "created_at",
                "current_user_can_bypass",
                "current_user_can_bypass_present",
                "links",
                "node_id",
                "updated_at",
            },
            label=f"{label}.server_metadata",
        )
    )
    if isinstance(metadata, dict):
        if not _is_rfc3339(metadata.get("created_at")):
            failures.append(f"{label}: created_at must be exact RFC3339")
        if not _is_rfc3339(metadata.get("updated_at")):
            failures.append(f"{label}: updated_at must be exact RFC3339")
        if (
            _is_rfc3339(metadata.get("created_at"))
            and _is_rfc3339(metadata.get("updated_at"))
            and datetime.fromisoformat(
                metadata["created_at"].replace("Z", "+00:00")
            )
            > datetime.fromisoformat(
                metadata["updated_at"].replace("Z", "+00:00")
            )
        ):
            failures.append(f"{label}: server timestamps are reversed")
        node_id = metadata.get("node_id")
        if not isinstance(node_id, str) or not node_id.startswith("RRS_"):
            failures.append(f"{label}: server node_id differs")
        links = metadata.get("links")
        failures.extend(
            _exact_keys(
                links,
                {"html", "self"},
                label=f"{label}.server_metadata.links",
            )
        )
        ruleset_id = value.get("id")
        if isinstance(links, dict) and _is_int(ruleset_id, minimum=1):
            expected_links = {
                "html": {
                    "href": f"https://github.com/{REPOSITORY}/rules/{ruleset_id}"
                },
                "self": {"href": f"{CREATE_ENDPOINT}/{ruleset_id}"},
            }
            if not _json_exact(links, expected_links):
                failures.append(f"{label}: server links differ")
        bypass_present = metadata.get("current_user_can_bypass_present")
        bypass_value = metadata.get("current_user_can_bypass")
        if require_current_user_bypass:
            if bypass_present is not True or bypass_value != "never":
                failures.append(
                    f"{label}: named ruleset must report current_user_can_bypass=never"
                )
        elif (
            (bypass_present is True and bypass_value != "never")
            or (bypass_present is False and bypass_value is not None)
            or not isinstance(bypass_present, bool)
        ):
            failures.append(
                f"{label}: POST bypass-capability presence/value is inconsistent"
            )
    return failures


def ruleset_history_state(value: object) -> dict[str, Any] | None:
    if not isinstance(value, dict):
        return None
    return {
        "id": value.get("id"),
        "request_policy": value.get("request_policy"),
        "server_policy": value.get("server_policy"),
        "source": value.get("source"),
        "source_type": value.get("source_type"),
    }


def ruleset_response_core(value: object) -> dict[str, Any] | None:
    if not isinstance(value, dict):
        return None
    metadata = value.get("server_metadata")
    if not isinstance(metadata, dict):
        return None
    core_metadata = {
        key: item
        for key, item in metadata.items()
        if key
        not in {
            "current_user_can_bypass",
            "current_user_can_bypass_present",
        }
    }
    return {
        **ruleset_history_state(value),
        "normalization": value.get("normalization"),
        "server_metadata": core_metadata,
    }


def expected_effective_rules(
    ruleset: object,
) -> list[dict[str, Any]]:
    projected: list[dict[str, Any]] = []
    if not isinstance(ruleset, dict):
        return projected
    ruleset_id = ruleset.get("id")
    server_policy = ruleset.get("server_policy")
    rules = (
        server_policy.get("rules")
        if isinstance(server_policy, dict)
        else None
    )
    if not _is_int(ruleset_id, minimum=1) or not isinstance(rules, list):
        return projected
    for rule in rules:
        if not isinstance(rule, dict):
            return []
        row = {
            "ruleset_id": ruleset_id,
            "ruleset_source": REPOSITORY,
            "ruleset_source_type": "Repository",
            **rule,
        }
        projected.append(row)
    return projected


def after_state_failures(
    after: dict[str, Any],
    *,
    policy_sha256: str,
    before: dict[str, Any],
    policy: dict[str, Any],
) -> list[str]:
    failures = _identity_failures(
        after,
        schema=AFTER_SCHEMA,
        label="after_state",
        expected_keys={
            "api_version",
            "before_comparison",
            "created_ruleset_id",
            "observed_at",
            "pagination",
            "policy_sha256",
            "projections",
            "repository",
            "request_counts",
            "schema_version",
            "source_commit",
        },
        policy_sha256=policy_sha256,
    )
    if after.get("source_commit") != before.get("source_commit"):
        failures.append("after_state: source_commit differs from before_state")
    if after.get("api_version") != API_VERSION:
        failures.append("after_state: API version differs")
    if not _is_utc_second(after.get("observed_at")):
        failures.append("after_state: observed_at must be a UTC whole second")
    ruleset_id = after.get("created_ruleset_id")
    if not _is_int(ruleset_id, minimum=1):
        failures.append("after_state: created_ruleset_id must be positive")
    comparison = after.get("before_comparison")
    failures.extend(
        _exact_keys(
            comparison,
            {"drift", "unchanged"},
            label="after_state.before_comparison",
        )
    )
    if isinstance(comparison, dict):
        if not _json_exact(comparison.get("drift"), []):
            failures.append("after_state: compared-projection drift must be empty")
        if not _json_exact(
            comparison.get("unchanged"),
            UNCHANGED_PROJECTIONS,
        ):
            failures.append("after_state: unchanged projection inventory differs")
    projections = after.get("projections")
    expected_keys = set(UNCHANGED_PROJECTIONS) | {
        "branch",
        "effective_rules",
        "named_ruleset",
        "ruleset_history",
        "rulesets",
    }
    failures.extend(_exact_keys(projections, expected_keys, label="after_state.projections"))
    if not isinstance(projections, dict):
        return failures
    failures.extend(
        _method_count_failures(
            after.get("request_counts"),
            label="after_state.request_counts",
            allow_post=False,
        )
    )
    failures.extend(
        _pagination_failures(
            after.get("pagination"),
            expected_endpoints=PAGINATION_KEYS_AFTER,
            projections=projections,
            label="after_state.pagination",
        )
    )
    counts = after.get("request_counts")
    pages = after.get("pagination")
    if isinstance(counts, dict) and isinstance(pages, dict):
        request_count = sum(
            page.get("request_count", 0)
            for page in pages.values()
            if isinstance(page, dict)
        )
        if counts.get("GET") != request_count:
            failures.append(
                "after_state: GET count must equal retained endpoint request count"
            )
    before_projections = before.get("projections")
    if isinstance(before_projections, dict):
        for key in UNCHANGED_PROJECTIONS:
            if not _json_exact(
                projections.get(key),
                before_projections.get(key),
            ):
                failures.append(f"after_state.projections.{key}: unrelated drift observed")
    expected_branch = {
        "name": DEFAULT_BRANCH,
        "protected": True,
        "sha": MERGED_MASTER_ANCHOR,
    }
    if not _json_exact(projections.get("branch"), expected_branch):
        failures.append("after_state.projections.branch: protected master projection differs")
    named = projections.get("named_ruleset")
    failures.extend(_ruleset_projection_failures(named, label="after_state.named_ruleset"))
    if isinstance(named, dict) and named.get("id") != ruleset_id:
        failures.append("after_state: named ruleset ID differs from created_ruleset_id")
    rulesets = projections.get("rulesets")
    if not isinstance(rulesets, list) or len(rulesets) != 1:
        failures.append("after_state: ruleset inventory must contain exactly one object")
    else:
        failures.extend(
            _ruleset_projection_failures(
                rulesets[0],
                label="after_state.rulesets[0]",
            )
        )
        if not _json_exact(rulesets[0], named):
            failures.append("after_state: inventory and named ruleset projections differ")
    if _is_int(ruleset_id, minimum=1):
        expected_effective = expected_effective_rules(named)
        if not _json_exact(
            projections.get("effective_rules"),
            expected_effective,
        ):
            failures.append(
                "after_state: effective rules do not reproduce the exact "
                "technical floor with created-ruleset provenance"
            )
    history = projections.get("ruleset_history")
    failures.extend(
        _exact_keys(
            history,
            {"entries", "latest_version", "ruleset_id"},
            label="after_state.projections.ruleset_history",
        )
    )
    if isinstance(history, dict):
        history_ruleset_id = history.get("ruleset_id")
        if not _is_int(history_ruleset_id, minimum=1):
            failures.append(
                "after_state: ruleset history ID must be positive"
            )
        elif not _json_exact(history_ruleset_id, ruleset_id):
            failures.append("after_state: ruleset history ID differs")
        entries = history.get("entries")
        if not isinstance(entries, list) or len(entries) != 1:
            failures.append(
                "after_state: new ruleset history must retain exactly one version"
            )
        else:
            entry = entries[0]
            failures.extend(
                _exact_keys(
                    entry,
                    {"actor", "updated_at", "version_id"},
                    label="after_state.projections.ruleset_history.entries[0]",
                )
            )
            if isinstance(entry, dict):
                if not _is_int(entry.get("version_id"), minimum=1):
                    failures.append(
                        "after_state: ruleset history version_id must be positive"
                    )
                if not _is_rfc3339(entry.get("updated_at")):
                    failures.append(
                        "after_state: ruleset history updated_at must be exact RFC3339"
                    )
                actor = entry.get("actor")
                failures.extend(
                    _exact_keys(
                        actor,
                        {"id", "type"},
                        label=(
                            "after_state.projections.ruleset_history."
                            "entries[0].actor"
                        ),
                    )
                )
                if isinstance(actor, dict):
                    if not _is_int(actor.get("id"), minimum=1):
                        failures.append(
                            "after_state: ruleset history actor id must be positive"
                        )
                    if actor.get("type") != "User":
                        failures.append(
                            "after_state: ruleset history actor type differs"
                        )
            latest = history.get("latest_version")
            failures.extend(
                _exact_keys(
                    latest,
                    {"actor", "state", "updated_at", "version_id"},
                    label="after_state.projections.ruleset_history.latest_version",
                )
            )
            if isinstance(latest, dict) and isinstance(entry, dict):
                latest_version_id = latest.get("version_id")
                if not _is_int(latest_version_id, minimum=1):
                    failures.append(
                        "after_state: latest history version_id must be positive"
                    )
                elif not _json_exact(
                    latest_version_id,
                    entry.get("version_id"),
                ):
                    failures.append(
                        "after_state: latest history version_id differs from inventory"
                    )
                if not _json_exact(latest.get("actor"), entry.get("actor")):
                    failures.append(
                        "after_state: latest history actor differs from inventory"
                    )
                if not _json_exact(
                    latest.get("updated_at"),
                    entry.get("updated_at"),
                ):
                    failures.append(
                        "after_state: latest history timestamp differs from inventory"
                    )
                if not _json_exact(
                    latest.get("state"),
                    ruleset_history_state(named),
                ):
                    failures.append(
                        "after_state: latest history state does not reproduce "
                        "the exact created ruleset"
                    )
    return failures


def mutation_receipt_failures(
    receipt: dict[str, Any],
    *,
    policy_sha256: str,
    before: dict[str, Any],
    before_raw: bytes,
    intent: dict[str, Any],
    intent_raw: bytes,
    after: dict[str, Any],
    after_raw: bytes,
    policy: dict[str, Any],
) -> list[str]:
    failures = _identity_failures(
        receipt,
        schema=RECEIPT_SCHEMA,
        label="mutation_receipt",
        expected_keys={
            "after_state_sha256",
            "ambiguous_reconciliation",
            "before_state_sha256",
            "dispatch_attempt",
            "finished_at",
            "mutation_intent_sha256",
            "outcome",
            "policy_sha256",
            "post_response",
            "repository",
            "request_body_sha256",
            "request_counts",
            "ruleset_id",
            "schema_version",
            "source_commit",
            "started_at",
        },
        policy_sha256=policy_sha256,
    )
    if receipt.get("source_commit") != before.get("source_commit"):
        failures.append("mutation_receipt: source_commit differs")
    dispatch = receipt.get("dispatch_attempt")
    failures.extend(
        dispatch_attempt_failures(
            dispatch,
            label="mutation_receipt.dispatch_attempt",
            source_commit=receipt.get("source_commit"),
            mutation_intent_sha256=sha256_bytes(intent_raw),
        )
    )
    if not _is_utc_second(receipt.get("started_at")):
        failures.append("mutation_receipt: started_at must be a UTC whole second")
    if not _is_utc_second(receipt.get("finished_at")):
        failures.append("mutation_receipt: finished_at must be a UTC whole second")
    if receipt.get("outcome") not in {"applied", "ambiguous_applied"}:
        failures.append("mutation_receipt: outcome is not an accepted applied state")
    expected_reconciliation = (
        "exact_get_match"
        if receipt.get("outcome") == "ambiguous_applied"
        else "not_required"
    )
    if receipt.get("ambiguous_reconciliation") != expected_reconciliation:
        failures.append(
            "mutation_receipt: ambiguous write requires exact GET reconciliation"
        )
    post_response = receipt.get("post_response")
    failures.extend(
        _exact_keys(
            post_response,
            {
                "classification",
                "http_status",
                "projection",
                "projection_sha256",
            },
            label="mutation_receipt.post_response",
        )
    )
    if isinstance(post_response, dict):
        if receipt.get("outcome") == "applied":
            if post_response.get("classification") != "accepted_created":
                failures.append(
                    "mutation_receipt: applied POST response classification differs"
                )
            if post_response.get("http_status") != 201:
                failures.append(
                    "mutation_receipt: applied POST must retain HTTP 201"
                )
            projections = after.get("projections")
            named = (
                projections.get("named_ruleset")
                if isinstance(projections, dict)
                else None
            )
            post_projection = post_response.get("projection")
            failures.extend(
                _ruleset_projection_failures(
                    post_projection,
                    label="mutation_receipt.post_response.projection",
                    require_current_user_bypass=False,
                )
            )
            if not _json_exact(
                ruleset_response_core(post_projection),
                ruleset_response_core(named),
            ):
                failures.append(
                    "mutation_receipt: POST response core differs from "
                    "retained named ruleset response"
                )
            if post_response.get("projection_sha256") != canonical_sha256(
                post_projection
            ):
                failures.append(
                    "mutation_receipt: POST response projection digest differs"
                )
        elif receipt.get("outcome") == "ambiguous_applied":
            classification = post_response.get("classification")
            http_status = post_response.get("http_status")
            transport_ambiguity = (
                classification == "ambiguous_transport"
                and http_status is None
            )
            response_ambiguity = (
                classification == "ambiguous_http_response"
                and _is_int(http_status, minimum=100)
                and http_status <= 599
            )
            if (
                not (transport_ambiguity or response_ambiguity)
                or post_response.get("projection") is not None
                or post_response.get("projection_sha256") is not None
            ):
                failures.append(
                    "mutation_receipt: ambiguous POST must retain the exact "
                    "transport or HTTP-response classification and known status"
                )
    ruleset_id = after.get("created_ruleset_id")
    if receipt.get("ruleset_id") != ruleset_id:
        failures.append("mutation_receipt: ruleset_id differs from after_state")
    if receipt.get("before_state_sha256") != sha256_bytes(before_raw):
        failures.append("mutation_receipt: before_state_sha256 differs")
    if receipt.get("mutation_intent_sha256") != sha256_bytes(intent_raw):
        failures.append("mutation_receipt: mutation_intent_sha256 differs")
    if receipt.get("after_state_sha256") != sha256_bytes(after_raw):
        failures.append("mutation_receipt: after_state_sha256 differs")
    if receipt.get("request_body_sha256") != policy.get("request_body_sha256"):
        failures.append("mutation_receipt: request_body_sha256 differs")

    counts = receipt.get("request_counts")
    expected_count_keys = HTTP_METHODS | SEMANTIC_MUTATIONS
    failures.extend(
        _exact_keys(counts, expected_count_keys, label="mutation_receipt.request_counts")
    )
    if isinstance(counts, dict):
        for key in sorted(expected_count_keys):
            if not _is_int(counts.get(key)):
                failures.append(
                    f"mutation_receipt.request_counts.{key}: must be nonnegative integer"
                )
        if all(_is_int(counts.get(method)) for method in HTTP_METHODS):
            expected_post = 1 if isinstance(dispatch, dict) else 0
            if counts["POST"] != expected_post:
                failures.append(
                    "mutation_receipt: POST count must follow the retained "
                    "dispatch attempt"
                )
            if not isinstance(dispatch, dict):
                failures.append(
                    "mutation_receipt: accepted outcome requires a retained "
                    "dispatch attempt"
                )
            if counts["GET"] < 1 or counts["GET"] > policy["mutation_budget"]["GET"]:
                failures.append("mutation_receipt: GET count exceeds finite budget")
            for method in ("DELETE", "PATCH", "PUT"):
                if counts[method] != 0:
                    failures.append(f"mutation_receipt: {method} count must be zero")
            before_counts = before.get("request_counts")
            after_counts = after.get("request_counts")
            if isinstance(before_counts, dict) and isinstance(after_counts, dict):
                minimum_get = before_counts.get("GET", 0) + after_counts.get("GET", 0)
                if counts["GET"] != minimum_get:
                    failures.append(
                        "mutation_receipt: GET total differs from retained phase counts"
                    )
        for operation in sorted(SEMANTIC_MUTATIONS):
            if counts.get(operation) != 0:
                failures.append(
                    f"mutation_receipt: unrelated {operation} requests must be zero"
                )
    return failures


def operational_check_failures(
    operational: dict[str, Any],
    *,
    policy_sha256: str,
    source_commit: str,
    expected_pull_request_number: object,
    after_state: dict[str, Any],
) -> list[str]:
    failures = _identity_failures(
        operational,
        schema=OPERATIONAL_SCHEMA,
        label="operational_check",
        expected_keys={
            "api_version",
            "independent_review_status",
            "pending",
            "policy_sha256",
            "pull_request",
            "repository",
            "ruleset_source_commit",
            "schema_version",
            "source_commit",
            "success",
        },
        policy_sha256=policy_sha256,
    )
    if operational.get("api_version") != API_VERSION:
        failures.append("operational_check: API version differs")
    if operational.get("ruleset_source_commit") != source_commit:
        failures.append("operational_check: ruleset_source_commit differs")
    if operational.get("independent_review_status") != "blocked":
        failures.append("operational_check: independent review must remain blocked")
    head = operational.get("source_commit")
    if not isinstance(head, str) or HEX40.fullmatch(head) is None:
        failures.append("operational_check: source_commit must be lowercase 40-hex")
    if head == source_commit:
        failures.append("operational_check: must use an ordinary new post-activation commit")
    after_projections = after_state.get("projections")
    if not isinstance(after_projections, dict):
        after_projections = {}
    pull = operational.get("pull_request")
    failures.extend(
        _exact_keys(
            pull,
            {
                "base_ref",
                "base_repository",
                "head_ref",
                "head_repository",
                "number",
            },
            label="operational_check.pull_request",
        )
    )
    if isinstance(pull, dict):
        if pull.get("base_ref") != DEFAULT_BRANCH:
            failures.append("operational_check: pull request base differs")
        if pull.get("base_repository") != REPOSITORY:
            failures.append(
                "operational_check: pull request base repository differs"
            )
        if pull.get("head_ref") != "agent/iter239-repository-governance":
            failures.append("operational_check: pull request head ref differs")
        if pull.get("head_repository") != REPOSITORY:
            failures.append(
                "operational_check: pull request head repository differs"
            )
        if not _is_int(pull.get("number"), minimum=1):
            failures.append("operational_check: pull request number must be positive")
        if pull.get("number") != expected_pull_request_number:
            failures.append(
                "operational_check: pull request number differs from before_state"
            )

    for phase_name in ("pending", "success"):
        phase = operational.get(phase_name)
        failures.extend(
            _exact_keys(
                phase,
                {
                    "checks",
                    "branch",
                    "effective_rules",
                    "merge_permitted",
                    "named_ruleset",
                    "non_check_requirements_satisfied",
                    "observed_at",
                    "pagination",
                    "pull_request",
                    "request_counts",
                    "review_comments",
                    "required_check_rollup_state",
                    "rulesets",
                    "source_commit",
                },
                label=f"operational_check.{phase_name}",
            )
        )
        if not isinstance(phase, dict):
            continue
        if not _is_utc_second(phase.get("observed_at")):
            failures.append(
                f"operational_check.{phase_name}: observed_at must be UTC whole second"
            )
        if phase.get("source_commit") != head:
            failures.append(f"operational_check.{phase_name}: head identity differs")
        for projection_name in (
            "branch",
            "effective_rules",
            "named_ruleset",
            "rulesets",
        ):
            if not _json_exact(
                phase.get(projection_name),
                after_projections.get(projection_name),
            ):
                failures.append(
                    f"operational_check.{phase_name}.{projection_name}: "
                    "live governance projection differs from accepted after_state"
                )
        failures.extend(
            _ruleset_projection_failures(
                phase.get("named_ruleset"),
                label=f"operational_check.{phase_name}.named_ruleset",
            )
        )

        raw_pull = phase.get("pull_request")
        failures.extend(
            _exact_keys(
                raw_pull,
                {
                    "base_ref",
                    "base_repository",
                    "draft",
                    "head_ref",
                    "head_repository",
                    "head_sha",
                    "mergeable",
                    "mergeable_state",
                    "review_comment_count",
                    "state",
                },
                label=f"operational_check.{phase_name}.pull_request",
            )
        )
        if isinstance(raw_pull, dict):
            expected_raw = {
                "base_ref": DEFAULT_BRANCH,
                "base_repository": REPOSITORY,
                "draft": False,
                "head_ref": "agent/iter239-repository-governance",
                "head_repository": REPOSITORY,
                "head_sha": head,
                "mergeable": True,
                "review_comment_count": 0,
                "state": "open",
            }
            for key, expected in expected_raw.items():
                if not _json_exact(raw_pull.get(key), expected):
                    failures.append(
                        f"operational_check.{phase_name}.pull_request.{key}: "
                        "raw value differs"
                    )
            expected_merge_state = (
                "CLEAN" if phase_name == "success" else "BLOCKED"
            )
            if raw_pull.get("mergeable_state") != expected_merge_state.lower():
                failures.append(
                    f"operational_check.{phase_name}: raw REST mergeable_state differs"
                )
        review_comments = phase.get("review_comments")
        if not _json_exact(review_comments, []):
            failures.append(
                f"operational_check.{phase_name}: REST review comments "
                "must be exactly empty for conversation-resolution evidence"
            )
        derived_non_check = (
            isinstance(raw_pull, dict)
            and raw_pull.get("base_ref") == DEFAULT_BRANCH
            and raw_pull.get("base_repository") == REPOSITORY
            and raw_pull.get("head_ref")
            == "agent/iter239-repository-governance"
            and raw_pull.get("head_repository") == REPOSITORY
            and raw_pull.get("head_sha") == head
            and raw_pull.get("draft") is False
            and raw_pull.get("mergeable") is True
            and raw_pull.get("review_comment_count") == 0
            and raw_pull.get("state") == "open"
            and review_comments == []
        )
        if (
            phase.get("non_check_requirements_satisfied")
            is not derived_non_check
        ):
            failures.append(
                f"operational_check.{phase_name}: non-check derivation does "
                "not follow raw PR/thread evidence"
            )
        expected_rollup = "SUCCESS" if phase_name == "success" else "PENDING"
        if phase.get("required_check_rollup_state") != expected_rollup:
            failures.append(
                f"operational_check.{phase_name}: required-check rollup differs"
            )
        derived_from_raw = (
            phase.get("required_check_rollup_state") == "SUCCESS"
            and isinstance(raw_pull, dict)
            and raw_pull.get("mergeable_state") == "clean"
            and phase.get("non_check_requirements_satisfied") is True
        )
        if phase.get("merge_permitted") is not derived_from_raw:
            failures.append(
                f"operational_check.{phase_name}: derived merge permission "
                "does not follow raw gate evidence"
            )
        if isinstance(head, str):
            failures.extend(
                _check_run_failures(
                    phase.get("checks"),
                    source_commit=head,
                    expected_status=phase_name,
                    include_push=False,
                    label=f"operational_check.{phase_name}.checks",
                )
            )
        phase_projections = {
            "branch": phase.get("branch"),
            "checks": phase.get("checks"),
            "effective_rules": phase.get("effective_rules"),
            "named_ruleset": phase.get("named_ruleset"),
            "pull_request": raw_pull,
            "review_comments": review_comments,
            "rulesets": phase.get("rulesets"),
        }
        failures.extend(
            _method_count_failures(
                phase.get("request_counts"),
                label=f"operational_check.{phase_name}.request_counts",
                allow_post=False,
            )
        )
        failures.extend(
            _pagination_failures(
                phase.get("pagination"),
                expected_endpoints=set(phase_projections),
                projections=phase_projections,
                label=f"operational_check.{phase_name}.pagination",
            )
        )
        counts = phase.get("request_counts")
        pages = phase.get("pagination")
        if isinstance(counts, dict) and isinstance(pages, dict):
            request_count = sum(
                page.get("request_count", 0)
                for page in pages.values()
                if isinstance(page, dict)
            )
            if counts.get("GET") != request_count:
                failures.append(
                    f"operational_check.{phase_name}: GET count differs "
                    "from retained request count"
                )
    pending = operational.get("pending")
    success = operational.get("success")
    if isinstance(pending, dict) and isinstance(success, dict):
        pending_time = pending.get("observed_at")
        success_time = success.get("observed_at")
        if (
            _is_utc_second(pending_time)
            and _is_utc_second(success_time)
            and pending_time >= success_time
        ):
            failures.append("operational_check: pending observation must precede success")
        pending_checks = pending.get("checks")
        success_checks = success.get("checks")
        if isinstance(pending_checks, list) and isinstance(success_checks, list):
            pending_by_name = {
                row.get("name"): row
                for row in pending_checks
                if isinstance(row, dict) and isinstance(row.get("name"), str)
            }
            success_by_name = {
                row.get("name"): row
                for row in success_checks
                if isinstance(row, dict) and isinstance(row.get("name"), str)
            }
            identity_keys = {
                "attempt",
                "check_run_id",
                "check_suite_id",
                "event",
                "head_sha",
                "integration_id",
                "name",
                "workflow_id",
                "workflow_path",
                "workflow_run_id",
            }
            for name in sorted(set(pending_by_name) | set(success_by_name)):
                pending_row = pending_by_name.get(name)
                success_row = success_by_name.get(name)
                if pending_row is None or success_row is None:
                    failures.append(
                        "operational_check: pending/success check identities differ"
                    )
                    continue
                if not _json_exact(
                    {
                        key: pending_row.get(key)
                        for key in identity_keys
                    },
                    {
                        key: success_row.get(key)
                        for key in identity_keys
                    },
                ):
                    failures.append(
                        "operational_check: pending/success observations do "
                        f"not follow the same check run: {name}"
                    )
    return failures


def _walk_strings(value: Any) -> Iterable[str]:
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for key, item in value.items():
            yield key
            yield from _walk_strings(item)
    elif isinstance(value, list):
        for item in value:
            yield from _walk_strings(item)


def review_prose_failures(
    documents: dict[str, dict[str, Any]],
) -> list[str]:
    failures: list[str] = []
    for label, document in sorted(documents.items()):
        for text in _walk_strings(document):
            if any(pattern.search(text) for pattern in FORBIDDEN_REVIEW_PATTERNS):
                failures.append(
                    f"{label}: prose falsely claims independent review: {text!r}"
                )
    return failures


def abort_record_failures(
    *,
    root: Path,
    abort: dict[str, Any],
    policy_sha256: str,
) -> list[str]:
    failures = _identity_failures(
        abort,
        schema=ABORT_SCHEMA,
        label="abort_record",
        expected_keys={
            "available_evidence_sha256",
            "classification",
            "dispatch_attempt",
            "phase",
            "policy_sha256",
            "reason_code",
            "recorded_at",
            "repository",
            "request_counts",
            "schema_version",
            "source_commit",
        },
        policy_sha256=policy_sha256,
    )
    if not _is_utc_second(abort.get("recorded_at")):
        failures.append("abort_record: recorded_at must be a UTC whole second")
    classification = abort.get("classification")
    reason = abort.get("reason_code")
    if (
        classification not in ABORT_OUTCOMES
        or reason not in ABORT_OUTCOMES.get(classification, [])
    ):
        failures.append("abort_record: classification/reason_code pair differs")
    if reason == "precondition_drift":
        expected_phase = "precondition"
    elif reason == "dispatch_not_attempted":
        expected_phase = "dispatch"
    else:
        expected_phase = "postcondition"
    if abort.get("phase") != expected_phase:
        failures.append("abort_record: phase differs from reason_code")

    available = abort.get("available_evidence_sha256")
    failures.extend(
        _exact_keys(
            available,
            EVIDENCE_RELATIVES,
            label="abort_record.available_evidence_sha256",
        )
    )
    if isinstance(available, dict):
        for label, relative in EVIDENCE_RELATIVES.items():
            path = root / relative
            observed = available.get(label)
            if path.is_file():
                if path.is_symlink():
                    failures.append(
                        f"abort_record: {label} evidence cannot be a symlink"
                    )
                    continue
                raw = path.read_bytes()
                expected = sha256_bytes(raw)
                if observed != expected:
                    failures.append(
                        f"abort_record: {label} digest differs from retained bytes"
                    )
                try:
                    document = load_canonical_json_bytes(
                        raw,
                        label=f"abort_record retained {label}",
                    )
                except GovernanceError as exc:
                    failures.append(str(exc))
                    continue
                if document.get("schema_version") != EVIDENCE_SCHEMAS[label]:
                    failures.append(
                        f"abort_record: {label} retained schema_version differs"
                    )
                if document.get("repository") != REPOSITORY:
                    failures.append(
                        f"abort_record: {label} retained repository differs"
                    )
                if document.get("policy_sha256") != policy_sha256:
                    failures.append(
                        f"abort_record: {label} retained policy_sha256 differs"
                    )
                if document.get("source_commit") != abort.get("source_commit"):
                    failures.append(
                        f"abort_record: {label} retained source_commit differs"
                    )
            elif observed is not None:
                failures.append(
                    f"abort_record: {label} digest exists without retained file"
                )
        if reason == "precondition_drift":
            if available.get("before_state") is None:
                failures.append(
                    "abort_record: precondition drift requires before-state evidence"
                )
            if any(
                available.get(label) is not None
                for label in (
                    "after_state",
                    "mutation_intent",
                    "mutation_receipt",
                    "operational_check",
                )
            ):
                failures.append(
                    "abort_record: precondition drift cannot claim post-intent evidence"
                )
        else:
            if available.get("before_state") is None:
                failures.append(
                    "abort_record: failed mutation requires before-state evidence"
                )
            if available.get("mutation_intent") is None:
                failures.append(
                    "abort_record: failed mutation requires persisted intent evidence"
                )
            if available.get("operational_check") is not None:
                failures.append(
                    "abort_record: failed mutation cannot claim operational acceptance"
                )

    dispatch = abort.get("dispatch_attempt")
    if reason in {"dispatch_not_attempted", "precondition_drift"}:
        if dispatch is not None:
            failures.append(
                "abort_record: pre-dispatch outcome cannot retain a dispatch attempt"
            )
    else:
        expected_intent_digest = (
            available.get("mutation_intent")
            if isinstance(available, dict)
            else None
        )
        failures.extend(
            dispatch_attempt_failures(
                dispatch,
                label="abort_record.dispatch_attempt",
                source_commit=abort.get("source_commit"),
                mutation_intent_sha256=expected_intent_digest,
            )
        )

    counts = abort.get("request_counts")
    expected_count_keys = HTTP_METHODS | SEMANTIC_MUTATIONS
    failures.extend(
        _exact_keys(
            counts,
            expected_count_keys,
            label="abort_record.request_counts",
        )
    )
    if isinstance(counts, dict):
        for key in sorted(expected_count_keys):
            if not _is_int(counts.get(key)):
                failures.append(
                    f"abort_record.request_counts.{key}: must be nonnegative integer"
                )
        if all(_is_int(counts.get(method)) for method in HTTP_METHODS):
            if counts["GET"] < 1 or counts["GET"] > 96:
                failures.append("abort_record: GET count exceeds finite budget")
            expected_post = 1 if isinstance(dispatch, dict) else 0
            if counts["POST"] != expected_post:
                failures.append(
                    "abort_record: POST count must follow the retained "
                    f"dispatch attempt ({expected_post})"
                )
            for method in ("DELETE", "PATCH", "PUT"):
                if counts[method] != 0:
                    failures.append(
                        f"abort_record: {method} count must be zero"
                    )
        for operation in sorted(SEMANTIC_MUTATIONS):
            if counts.get(operation) != 0:
                failures.append(
                    f"abort_record: unrelated {operation} requests must be zero"
                )
    return failures


def result_failures(
    root: Path,
    *,
    evidence_complete: bool,
) -> list[str]:
    path = root / RESULT_RELATIVE
    if not path.exists():
        if evidence_complete:
            return [
                "iter239 RESULT.md is required when complete G0-G5 evidence exists"
            ]
        return []
    failures: list[str] = []
    if not evidence_complete:
        failures.append(
            "iter239 RESULT.md exists while complete G0-G5 evidence is absent"
        )
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        return [*failures, f"iter239 RESULT.md cannot be read as UTF-8: {exc}"]
    required = (
        "technical-control status: supported",
        "independent-review status: blocked",
        "overall governance status: blocked",
    )
    for statement in required:
        if text.count(statement) != 1:
            failures.append(
                f"iter239 RESULT.md must contain exactly once: {statement}"
            )
    for pattern in FORBIDDEN_RESULT_PATTERNS:
        match = pattern.search(text)
        if match is not None:
            failures.append(
                "iter239 RESULT.md contains forbidden overclaim: "
                f"{match.group(0)!r}"
            )
    return failures


def source_commit_failures(
    root: Path,
    *,
    source_commit: object,
) -> list[str]:
    if not isinstance(source_commit, str) or HEX40.fullmatch(source_commit) is None:
        return []
    failures: list[str] = []
    probe = _git(root, "cat-file", "-e", f"{source_commit}^{{commit}}")
    if probe.returncode != 0:
        return ["evidence source_commit is not a local Git commit"]
    if source_commit != TRANSACTION_SOURCE_COMMIT:
        failures.append(
            "evidence source_commit is not the exact retained transaction "
            f"instrument commit {TRANSACTION_SOURCE_COMMIT}"
        )
    if source_commit in {MERGED_MASTER_ANCHOR, ACTIVATION_COMMIT}:
        failures.append(
            "evidence source_commit must be a post-activation implementation commit"
        )
    ancestry = _git(
        root,
        "merge-base",
        "--is-ancestor",
        ACTIVATION_COMMIT,
        source_commit,
    )
    if ancestry.returncode != 0:
        failures.append(
            "evidence source_commit is not a descendant of the exact activation commit"
        )
    head_ancestry = _git(root, "merge-base", "--is-ancestor", source_commit, "HEAD")
    if head_ancestry.returncode != 0:
        failures.append("evidence source_commit is not an ancestor of current HEAD")
    for relative in SOURCE_BOUND_RELATIVES:
        if _git_blob(root, source_commit, relative) is None:
            failures.append(
                "evidence source_commit does not contain transaction instrument: "
                f"{relative.as_posix()}"
            )
    for relative, expected_sha256 in TRANSACTION_INSTRUMENT_SHA256.items():
        historical = _git_blob(root, source_commit, relative)
        if historical is not None and sha256_bytes(historical) != expected_sha256:
            failures.append(
                "transaction instrument digest differs: "
                f"{relative.as_posix()}"
            )
    return failures


def operational_source_failures(
    root: Path,
    *,
    ruleset_source: object,
    operational_source: object,
) -> list[str]:
    if (
        not isinstance(ruleset_source, str)
        or HEX40.fullmatch(ruleset_source) is None
        or not isinstance(operational_source, str)
        or HEX40.fullmatch(operational_source) is None
    ):
        return []
    failures: list[str] = []
    probe = _git(root, "cat-file", "-e", f"{operational_source}^{{commit}}")
    if probe.returncode != 0:
        return ["operational source_commit is not a local Git commit"]
    if ruleset_source != TRANSACTION_SOURCE_COMMIT:
        failures.append(
            "operational ruleset_source_commit is not the exact retained "
            f"transaction instrument commit {TRANSACTION_SOURCE_COMMIT}"
        )
    if operational_source != OPERATIONAL_SOURCE_COMMIT:
        failures.append(
            "operational source_commit is not the exact retained operational "
            f"instrument commit {OPERATIONAL_SOURCE_COMMIT}"
        )
    for relative, expected_sha256 in OPERATIONAL_INSTRUMENT_SHA256.items():
        historical = _git_blob(root, operational_source, relative)
        if historical is None or sha256_bytes(historical) != expected_sha256:
            failures.append(
                "operational instrument digest differs: "
                f"{relative.as_posix()}"
            )
    ancestry = _git(
        root,
        "merge-base",
        "--is-ancestor",
        ruleset_source,
        operational_source,
    )
    if ancestry.returncode != 0:
        failures.append(
            "operational source_commit is not a descendant of ruleset source_commit"
        )
    head_ancestry = _git(
        root,
        "merge-base",
        "--is-ancestor",
        operational_source,
        "HEAD",
    )
    if head_ancestry.returncode != 0:
        failures.append("operational source_commit is not an ancestor of current HEAD")

    transition = _git(
        root,
        "diff",
        "--name-only",
        "--no-renames",
        ruleset_source,
        operational_source,
    )
    if transition.returncode != 0:
        failures.append(
            "transaction-to-operational instrument transition cannot be read"
        )
    else:
        try:
            changed = {
                Path(line.decode("utf-8"))
                for line in transition.stdout.splitlines()
                if line
            }
        except UnicodeDecodeError:
            failures.append(
                "transaction-to-operational instrument paths are not UTF-8"
            )
        else:
            if changed != set(INSTRUMENT_TRANSITION_RELATIVES):
                failures.append(
                    "transaction-to-operational instrument transition paths differ"
                )

    for relative in OPERATIONAL_STABLE_RELATIVES:
        try:
            current = (root / relative).read_bytes()
        except OSError as exc:
            failures.append(
                f"source-bound artifact {relative.as_posix()} cannot be read: {exc}"
            )
            continue
        if _git_blob(root, operational_source, relative) != current:
            failures.append(
                "operational source_commit does not contain exact current stable "
                "bytes: "
                f"{relative.as_posix()}"
            )
    try:
        current_validator = (root / GOVERNANCE_VALIDATOR_RELATIVE).read_bytes()
    except OSError as exc:
        failures.append(f"current governance validator cannot be read: {exc}")
    else:
        if (
            _git_blob(root, "HEAD", GOVERNANCE_VALIDATOR_RELATIVE)
            != current_validator
        ):
            failures.append(
                "current governance validator differs from committed HEAD bytes"
            )
    return failures


def chronology_failures(
    *,
    before: dict[str, Any],
    intent: dict[str, Any],
    after: dict[str, Any],
    receipt: dict[str, Any],
    operational: dict[str, Any],
) -> list[str]:
    points = [
        ("mutation_receipt.started_at", receipt.get("started_at")),
        ("before_state.observed_at", before.get("observed_at")),
        ("mutation_intent.persisted_at", intent.get("persisted_at")),
        (
            "mutation_receipt.dispatch_attempt.consumed_at",
            receipt.get("dispatch_attempt", {}).get("consumed_at")
            if isinstance(receipt.get("dispatch_attempt"), dict)
            else None,
        ),
        ("after_state.observed_at", after.get("observed_at")),
        ("mutation_receipt.finished_at", receipt.get("finished_at")),
        (
            "operational_check.pending.observed_at",
            operational.get("pending", {}).get("observed_at")
            if isinstance(operational.get("pending"), dict)
            else None,
        ),
        (
            "operational_check.success.observed_at",
            operational.get("success", {}).get("observed_at")
            if isinstance(operational.get("success"), dict)
            else None,
        ),
    ]
    if not all(_is_utc_second(value) for _label, value in points):
        return []
    failures: list[str] = []
    for (earlier_label, earlier), (later_label, later) in zip(points, points[1:]):
        if earlier > later:
            failures.append(
                f"evidence chronology reverses {earlier_label} and {later_label}"
            )
    return failures


def evidence_bundle_failures(
    *,
    root: Path,
    policy: dict[str, Any],
    policy_raw: bytes,
    evidence: dict[str, tuple[dict[str, Any], bytes]],
) -> list[str]:
    policy_digest = sha256_bytes(policy_raw)
    before, before_raw = evidence["before_state"]
    intent, intent_raw = evidence["mutation_intent"]
    after, after_raw = evidence["after_state"]
    receipt, _receipt_raw = evidence["mutation_receipt"]
    operational, _operational_raw = evidence["operational_check"]

    failures: list[str] = []
    failures.extend(before_state_failures(before, policy_sha256=policy_digest))
    failures.extend(
        mutation_intent_failures(
            intent,
            policy_sha256=policy_digest,
            before=before,
            before_raw=before_raw,
            policy=policy,
        )
    )
    failures.extend(
        after_state_failures(
            after,
            policy_sha256=policy_digest,
            before=before,
            policy=policy,
        )
    )
    failures.extend(
        mutation_receipt_failures(
            receipt,
            policy_sha256=policy_digest,
            before=before,
            before_raw=before_raw,
            intent=intent,
            intent_raw=intent_raw,
            after=after,
            after_raw=after_raw,
            policy=policy,
        )
    )
    source = before.get("source_commit")
    failures.extend(
        operational_check_failures(
            operational,
            policy_sha256=policy_digest,
            source_commit=source if isinstance(source, str) else "",
            expected_pull_request_number=(
                before.get("projections", {})
                .get("open_pull_request", {})
                .get("number")
                if isinstance(before.get("projections"), dict)
                else None
            ),
            after_state=after,
        )
    )
    failures.extend(
        source_commit_failures(
            root,
            source_commit=source,
        )
    )
    failures.extend(
        operational_source_failures(
            root,
            ruleset_source=source,
            operational_source=operational.get("source_commit"),
        )
    )
    failures.extend(
        chronology_failures(
            before=before,
            intent=intent,
            after=after,
            receipt=receipt,
            operational=operational,
        )
    )
    failures.extend(
        review_prose_failures(
            {
                label: document
                for label, (document, _raw) in evidence.items()
            }
        )
    )
    return failures


def collect_failures(
    *,
    root: Path = ROOT,
    require_complete: bool = False,
) -> list[str]:
    failures: list[str] = []
    try:
        policy, policy_raw = load_canonical_json(root / POLICY_RELATIVE)
    except GovernanceError as exc:
        return [str(exc)]
    failures.extend(policy_failures(policy))
    failures.extend(current_ci_failures(root))
    abort_present = (root / ABORT_RELATIVE).is_file()
    abort: dict[str, Any] | None = None
    if abort_present:
        try:
            abort, _abort_raw = load_canonical_json(root / ABORT_RELATIVE)
        except GovernanceError as exc:
            failures.append(str(exc))
        if abort is not None:
            failures.extend(
                abort_record_failures(
                    root=root,
                    abort=abort,
                    policy_sha256=sha256_bytes(policy_raw),
                )
            )
            failures.extend(
                source_commit_failures(
                    root,
                    source_commit=abort.get("source_commit"),
                )
            )
            failures.append(
                "iter239 acceptance is explicitly unavailable: "
                f"{abort.get('classification')}/{abort.get('reason_code')}"
            )

    present = {
        label: (root / relative).is_file()
        for label, relative in EVIDENCE_RELATIVES.items()
    }
    present_labels = sorted(label for label, exists in present.items() if exists)
    if not present_labels:
        if require_complete:
            failures.append(
                "iter239 live evidence is absent; --require-complete cannot "
                "accept a prospective implementation"
            )
        failures.extend(result_failures(root, evidence_complete=False))
        return failures
    missing_labels = sorted(label for label, exists in present.items() if not exists)
    if missing_labels:
        failures.append(
            "iter239 live evidence is partial; missing complete-bundle files: "
            f"{missing_labels}"
        )
        failures.extend(result_failures(root, evidence_complete=False))
        return failures
    if abort_present:
        failures.append(
            "iter239 abort_record must be absent from a complete accepted bundle"
        )

    evidence: dict[str, tuple[dict[str, Any], bytes]] = {}
    for label, relative in EVIDENCE_RELATIVES.items():
        try:
            evidence[label] = load_canonical_json(root / relative)
        except GovernanceError as exc:
            failures.append(str(exc))
    if len(evidence) != len(EVIDENCE_RELATIVES):
        return failures
    failures.extend(
        evidence_bundle_failures(
            root=root,
            policy=policy,
            policy_raw=policy_raw,
            evidence=evidence,
        )
    )
    failures.extend(result_failures(root, evidence_complete=True))
    return failures


def success_message(*, evidence_present: bool) -> str:
    if not evidence_present:
        return (
            "iter239 repository-governance validation passed "
            "(prospective implementation; live evidence absent; "
            "G0-G5 acceptance unestablished)"
        )
    return (
        "iter239 repository-governance validation passed "
        "(complete retained G0-G5 evidence)"
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--require-complete",
        action="store_true",
        help="require and validate the complete G0-G5 retained evidence bundle",
    )
    args = parser.parse_args()
    failures = collect_failures(require_complete=args.require_complete)
    if failures:
        print("iter239 repository-governance validation failed:", file=sys.stderr)
        for failure in failures:
            print(f"- {failure}", file=sys.stderr)
        return 1
    evidence_present = any(
        (ROOT / relative).is_file()
        for relative in EVIDENCE_RELATIVES.values()
    )
    print(success_message(evidence_present=evidence_present))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
