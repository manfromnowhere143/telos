#!/usr/bin/env python3
"""Independently validate iter241's retained iter240 repository closure."""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
import subprocess
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
EXPERIMENT = ROOT / "experiments/iter241_iter240_repository_closure"
SAFE_FIXTURE = EXPERIMENT / "fixtures/repository_closure_safe.json"
KNOWN_BAD_FIXTURE = EXPERIMENT / "fixtures/repository_closure_known_bad.json"
PROOF = EXPERIMENT / "proof"
RAW_ROOT = PROOF / "raw/iter240_repository_closure"
RECEIPT = PROOF / "iter240_repository_closure.json"
ATTEMPT = RAW_ROOT / "capture_attempt.json"

REPOSITORY = "manfromnowhere143/telos"
API_VERSION = "2026-03-10"
AUTHORIZATION_HEAD = "6a9a4f66ec331011c9dfbe14b3a22259a5b585d5"
AUTHORIZATION_PARENTS = [
    "39e2484cba450fe5346349921572720b0e456fb7",
    "ceb8dfbb2ba451e76c71528a8ca5fcc75f5edc31",
]
AUTHORIZATION_TREE = "76c6791ec2a051804a50f65b5297b709dea4f49c"
SEALED_HEAD = "f954696c935ad0b733dcd613b553e1799a7b3810"
SEALED_PARENT = "a61a005cc7cdc92d72d79c017a650237c3e57faa"
SEALED_TREE = "1a6384324dd3e2a15121d981938a0bcee397c904"
ITER240_TREE = "cb03a4bd15d38f1ffb8ba33682502fa59dac26c2"
PREDECESSOR = "b597b763f2eb52b2f4f2d36e7daaa31654be076b"
MERGE = "39e2484cba450fe5346349921572720b0e456fb7"
RULESET_ID = 19177100
MAX_RESPONSE_BYTES = 5 * 1024 * 1024
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
REQUEST_ID_RE = re.compile(r"^[A-Za-z0-9:-]+$")

ENDPOINTS = (
    ("pull_request_88", f"/repos/{REPOSITORY}/pulls/88", "pull_request_88.json"),
    (
        "pull_request_88_timeline",
        f"/repos/{REPOSITORY}/issues/88/timeline?per_page=100&page=1",
        "pull_request_88_timeline.json",
    ),
    (
        "pull_request_88_reviews",
        f"/repos/{REPOSITORY}/pulls/88/reviews?per_page=100&page=1",
        "pull_request_88_reviews.json",
    ),
    (
        "sealed_push_run",
        f"/repos/{REPOSITORY}/actions/runs/29707762374",
        "sealed_push_run.json",
    ),
    (
        "sealed_pr_run",
        f"/repos/{REPOSITORY}/actions/runs/29707871077",
        "sealed_pr_run.json",
    ),
    (
        "sealed_tip_check_runs",
        f"/repos/{REPOSITORY}/commits/{SEALED_HEAD}/check-runs?filter=all&per_page=100&page=1",
        "sealed_tip_check_runs.json",
    ),
    (
        "gitguardian_check_run",
        f"/repos/{REPOSITORY}/check-runs/88247740246",
        "gitguardian_check_run.json",
    ),
    (
        "merge_commit",
        f"/repos/{REPOSITORY}/git/commits/{MERGE}",
        "merge_commit.json",
    ),
    (
        "merged_master_run",
        f"/repos/{REPOSITORY}/actions/runs/29708028160",
        "merged_master_run.json",
    ),
    (
        "merged_master_check_runs",
        f"/repos/{REPOSITORY}/commits/{MERGE}/check-runs?filter=all&per_page=100&page=1",
        "merged_master_check_runs.json",
    ),
    (
        "master_branch",
        f"/repos/{REPOSITORY}/branches/master",
        "master_branch.json",
    ),
    (
        "ruleset",
        f"/repos/{REPOSITORY}/rulesets/{RULESET_ID}",
        "ruleset.json",
    ),
    (
        "effective_rules",
        f"/repos/{REPOSITORY}/rules/branches/master?per_page=100&page=1",
        "effective_rules.json",
    ),
)

LIMITATIONS = [
    (
        "This is a time-bounded observation of mutable GitHub state; it does "
        "not prove that the state cannot later drift."
    ),
    (
        "Digests, ETags, and GitHub request identifiers bind retained bytes "
        "but do not establish authorship, external chronology, semantic truth, "
        "security approval, or scientific correctness."
    ),
    (
        "The zero write counts cover only this fixed capture instrument, not "
        "every action by every actor."
    ),
    (
        "The non-required GitGuardian check formally failed and remains "
        "unresolved; required Actions success is not an all-checks-green or "
        "security-approval result."
    ),
    (
        "The ruleset and pull request require zero approvals and retain zero "
        "reviews; technical closure is not independent review assurance."
    ),
    (
        "This engineering closure supplies no independent ground truth or "
        "scientific authority and authorizes no provider, model, human, target, "
        "container, GPU, spending, publication, or release action."
    ),
]


class ValidationError(ValueError):
    """Strict retained data is malformed."""


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise ValidationError(f"duplicate JSON key: {key}")
        value[key] = item
    return value


def _reject_nonfinite(value: str) -> None:
    raise ValidationError(f"non-finite JSON number: {value}")


def strict_json_bytes(raw: bytes, *, label: str) -> Any:
    try:
        return json.loads(
            raw,
            object_pairs_hook=_unique_object,
            parse_constant=_reject_nonfinite,
        )
    except (UnicodeError, json.JSONDecodeError, ValueError) as exc:
        raise ValidationError(f"{label} is not strict JSON: {exc}") from exc


def read_json(path: Path, *, label: str | None = None) -> Any:
    return strict_json_bytes(path.read_bytes(), label=label or str(path))


def canonical_json(value: Any) -> bytes:
    return (
        json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n"
    ).encode("utf-8")


def sha256_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def request_plan() -> list[dict[str, str]]:
    return [
        {"method": "GET", "name": name, "request_path": path}
        for name, path, _filename in ENDPOINTS
    ]


def expected_counts() -> dict[str, int]:
    return {"GET": len(ENDPOINTS), "POST": 0, "PUT": 0, "PATCH": 0, "DELETE": 0}


def _regular_0644(path: Path, *, label: str) -> bytes:
    metadata = path.lstat()
    if (
        not stat.S_ISREG(metadata.st_mode)
        or path.is_symlink()
        or stat.S_IMODE(metadata.st_mode) != 0o644
    ):
        raise ValidationError(f"{label} is not a regular nonsymlink 0644 file")
    return path.read_bytes()


def _git(*arguments: str) -> str:
    completed = subprocess.run(
        ["git", "-C", str(ROOT), *arguments],
        capture_output=True,
        check=False,
        text=True,
    )
    if completed.returncode != 0:
        raise ValidationError(
            f"git {' '.join(arguments)} failed: {completed.stderr.strip()}"
        )
    return completed.stdout.strip()


def repository_failures(root: Path = ROOT) -> list[str]:
    failures: list[str] = []
    try:
        if root.resolve() != root:
            failures.append("repository root is noncanonical")
        if _git("rev-parse", "HEAD") != AUTHORIZATION_HEAD:
            failures.append("local HEAD is not the exact iter241 authorization merge")
        if _git("show", "-s", "--format=%T", AUTHORIZATION_HEAD) != AUTHORIZATION_TREE:
            failures.append("authorization merge tree differs")
        parents = _git("show", "-s", "--format=%P", AUTHORIZATION_HEAD).split()
        if parents != AUTHORIZATION_PARENTS:
            failures.append("authorization merge parents differ")
        if _git("show", "-s", "--format=%P", SEALED_HEAD).split() != [SEALED_PARENT]:
            failures.append("sealed iter240 parent differs")
        if _git("show", "-s", "--format=%T", SEALED_HEAD) != SEALED_TREE:
            failures.append("sealed iter240 tree differs")
        if _git("rev-parse", f"{SEALED_HEAD}:experiments/iter240_ground_truth_admission_design") != ITER240_TREE:
            failures.append("sealed iter240 experiment subtree differs")
        if _git("show", "-s", "--format=%P", MERGE).split() != [PREDECESSOR, SEALED_HEAD]:
            failures.append("iter240 merge parents differ")
        if _git("show", "-s", "--format=%T", MERGE) != SEALED_TREE:
            failures.append("iter240 merge tree differs from sealed head")
        diff = subprocess.run(
            [
                "git",
                "-C",
                str(root),
                "diff",
                "--no-ext-diff",
                "--quiet",
                SEALED_HEAD,
                "--",
                "experiments/iter240_ground_truth_admission_design",
            ],
            check=False,
        )
        if diff.returncode != 0:
            failures.append("sealed iter240 experiment bytes drifted in the worktree")
        seal = read_json(root / "mission/seal_registry.json", label="seal registry")
        records = seal.get("records") if isinstance(seal, dict) else None
        matches = [
            row
            for row in records or []
            if isinstance(row, dict)
            and row.get("seal_id") == "iter241-iter240-repository-closure-authorization"
        ]
        expected = {
            "record_type": "prospective_successor_authorization",
            "predecessor_seal_id": "iter240-completed-evidence-seal",
            "reference_commit": MERGE,
            "authorized_path": "experiments/iter241_iter240_repository_closure",
            "must_be_absent_at_reference": True,
            "policy": "additions_only_until_successor_seal",
            "closure_requirement": "exact_tree_successor_path_snapshot",
        }
        if len(matches) != 1 or any(matches[0].get(k) != v for k, v in expected.items()):
            failures.append("iter241 prospective seal authorization differs")
    except (OSError, ValidationError, KeyError, TypeError, ValueError) as exc:
        failures.append(f"repository preflight is unreadable: {exc}")
    return failures


def _run_projection(value: object) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValidationError("workflow run is not an object")
    return {
        "id": value.get("id"),
        "workflow_id": value.get("workflow_id"),
        "attempt": value.get("run_attempt"),
        "event": value.get("event"),
        "status": value.get("status"),
        "conclusion": value.get("conclusion"),
        "head_sha": value.get("head_sha"),
        "check_suite_id": value.get("check_suite_id"),
    }


def _check_projection(value: object) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValidationError("check run is not an object")
    app = value.get("app")
    if not isinstance(app, dict):
        raise ValidationError("check run app is not an object")
    return {
        "id": value.get("id"),
        "name": value.get("name"),
        "app_id": app.get("id"),
        "conclusion": value.get("conclusion"),
        "head_sha": value.get("head_sha"),
    }


def _checks_by_id(value: object, *, label: str) -> dict[int, dict[str, Any]]:
    if not isinstance(value, dict):
        raise ValidationError(f"{label} is not an object")
    rows = value.get("check_runs")
    count = value.get("total_count")
    if not isinstance(rows, list) or type(count) is not int or count != len(rows):
        raise ValidationError(f"{label} count is incomplete")
    result: dict[int, dict[str, Any]] = {}
    for row in rows:
        if not isinstance(row, dict) or type(row.get("id")) is not int:
            raise ValidationError(f"{label} has an invalid check identity")
        if row["id"] in result:
            raise ValidationError(f"{label} repeats a check identity")
        result[row["id"]] = row
    return result


def _request_policy_projection(value: object) -> dict[str, Any]:
    if not isinstance(value, dict) or not isinstance(value.get("rules"), list):
        raise ValidationError("ruleset response is malformed")
    rules: list[dict[str, Any]] = []
    for raw in value["rules"]:
        if not isinstance(raw, dict):
            raise ValidationError("ruleset contains a non-object rule")
        row = deepcopy(raw)
        parameters = row.get("parameters")
        if (
            row.get("type") == "pull_request"
            and isinstance(parameters, dict)
            and parameters.get("required_reviewers") == []
        ):
            del parameters["required_reviewers"]
        rules.append(row)
    return {
        "name": value.get("name"),
        "target": value.get("target"),
        "enforcement": value.get("enforcement"),
        "bypass_actors": value.get("bypass_actors"),
        "conditions": value.get("conditions"),
        "rules": rules,
    }


def _effective_rules_projection(value: object) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        raise ValidationError("effective rules response is not an array")
    result: list[dict[str, Any]] = []
    for raw in value:
        if not isinstance(raw, dict):
            raise ValidationError("effective rule is not an object")
        row = {
            "ruleset_id": raw.get("ruleset_id"),
            "ruleset_source": raw.get("ruleset_source"),
            "ruleset_source_type": raw.get("ruleset_source_type"),
            "type": raw.get("type"),
        }
        if "parameters" in raw:
            row["parameters"] = raw.get("parameters")
        result.append(row)
    return result


def document_projection(documents: dict[str, Any]) -> dict[str, Any]:
    safe = read_json(SAFE_FIXTURE, label="safe fixture")
    if not isinstance(safe, dict):
        raise ValidationError("safe fixture is not an object")

    pull = documents.get("pull_request_88")
    timeline = documents.get("pull_request_88_timeline")
    reviews = documents.get("pull_request_88_reviews")
    if not isinstance(pull, dict) or not isinstance(timeline, list) or not isinstance(reviews, list):
        raise ValidationError("pull-request response family is malformed")
    head = pull.get("head")
    base = pull.get("base")
    if not isinstance(head, dict) or not isinstance(base, dict):
        raise ValidationError("pull-request head/base is malformed")
    merge_events = [row for row in timeline if isinstance(row, dict) and row.get("event") == "merged"]
    timeline_sha = merge_events[0].get("commit_id") if len(merge_events) == 1 else None

    sealed_checks = _checks_by_id(documents.get("sealed_tip_check_runs"), label="sealed check runs")
    merged_checks = _checks_by_id(documents.get("merged_master_check_runs"), label="merged check runs")
    required_sealed_ids = [88247471509, 88247471499, 88247740624, 88247740616]
    required_merged_ids = [88248101958, 88248101954]
    required_sealed = [
        _check_projection(sealed_checks.get(check_id))
        for check_id in required_sealed_ids
    ]
    required_merged = [
        _check_projection(merged_checks.get(check_id))
        for check_id in required_merged_ids
    ]
    if set(sealed_checks) != set(required_sealed_ids + [88247740246]):
        raise ValidationError("sealed check set is not exactly four Actions plus GitGuardian")
    if set(merged_checks) != set(required_merged_ids):
        raise ValidationError("merged check set is not exactly the two required Actions checks")

    guardian = documents.get("gitguardian_check_run")
    if not isinstance(guardian, dict):
        raise ValidationError("GitGuardian check response is malformed")
    guardian_app = guardian.get("app")
    guardian_output = guardian.get("output")
    if not isinstance(guardian_app, dict) or not isinstance(guardian_output, dict):
        raise ValidationError("GitGuardian app/output is malformed")
    if guardian != sealed_checks.get(88247740246):
        raise ValidationError("direct GitGuardian response differs from sealed check-set row")

    merge = documents.get("merge_commit")
    branch = documents.get("master_branch")
    ruleset = documents.get("ruleset")
    if not isinstance(merge, dict) or not isinstance(branch, dict) or not isinstance(ruleset, dict):
        raise ValidationError("merge, branch, or ruleset response is malformed")
    tree = merge.get("tree")
    merge_parents = merge.get("parents")
    branch_commit = branch.get("commit")
    if not isinstance(tree, dict) or not isinstance(merge_parents, list) or not isinstance(branch_commit, dict):
        raise ValidationError("merge topology or branch commit is malformed")

    policy_digest = sha256_bytes(canonical_json(_request_policy_projection(ruleset)))
    effective_digest = sha256_bytes(
        canonical_json(_effective_rules_projection(documents.get("effective_rules")))
    )
    projection = deepcopy(safe)
    projection["pull_request"] = {
        "number": pull.get("number"),
        "state": pull.get("state"),
        "merged": pull.get("merged"),
        "merged_at": pull.get("merged_at"),
        "draft": pull.get("draft"),
        "head_sha": head.get("sha"),
        "base_sha": base.get("sha"),
        "rest_merge_commit_sha": pull.get("merge_commit_sha"),
        "timeline_merge_commit_sha": timeline_sha,
        "review_count": len(reviews),
    }
    projection["merge"] = {
        "sha": merge.get("sha"),
        "parents": [
            row.get("sha") if isinstance(row, dict) else None
            for row in merge_parents
        ],
        "tree": tree.get("sha"),
    }
    projection["ci"] = {
        "sealed_head": {
            "runs": [
                _run_projection(documents.get("sealed_push_run")),
                _run_projection(documents.get("sealed_pr_run")),
            ],
            "required_checks": required_sealed,
            "gitguardian": {
                "id": guardian.get("id"),
                "app_id": guardian_app.get("id"),
                "app_slug": guardian_app.get("slug"),
                "status": guardian.get("status"),
                "conclusion": guardian.get("conclusion"),
                "head_sha": guardian.get("head_sha"),
                "output_title": guardian_output.get("title"),
                "annotations_count": guardian_output.get("annotations_count"),
            },
        },
        "merged_master": {
            "run": _run_projection(documents.get("merged_master_run")),
            "checks": required_merged,
        },
    }
    projection["governance"] = {
        "branch": branch.get("name"),
        "branch_sha": branch_commit.get("sha"),
        "protected": branch.get("protected"),
        "ruleset_id": ruleset.get("id"),
        "ruleset_name": ruleset.get("name"),
        "enforcement": ruleset.get("enforcement"),
        "bypass_actors": ruleset.get("bypass_actors"),
        "current_user_can_bypass": ruleset.get("current_user_can_bypass"),
        "request_policy_sha256": policy_digest,
        "effective_rules_sha256": effective_digest,
    }
    return projection


def projection_failures(projection: object, *, expected: dict[str, Any] | None = None) -> list[str]:
    failures: list[str] = []
    if expected is None:
        expected_value = read_json(SAFE_FIXTURE, label="safe fixture")
        if not isinstance(expected_value, dict):
            return ["safe fixture is not an object"]
        expected = expected_value
    if not isinstance(projection, dict):
        return ["closure projection is not an object"]
    for key, label in (
        ("schema_version", "schema"),
        ("repository", "repository"),
        ("authorization", "authorization"),
        ("merge", "merge topology"),
        ("request_counts", "write count"),
    ):
        if projection.get(key) != expected.get(key):
            failures.append(f"{label} differs")

    integrity = projection.get("capture_integrity")
    if not isinstance(integrity, dict):
        failures.append("capture integrity differs")
    else:
        if integrity.get("raw_body_hashes_match") is not True:
            failures.append("raw body hash integrity differs")
        if integrity.get("raw_header_hashes_match") is not True:
            failures.append("raw header hash integrity differs")
        if integrity.get("unique_request_ids") is not True:
            failures.append("GitHub request ID uniqueness differs")

    observed_pull = projection.get("pull_request")
    expected_pull = expected.get("pull_request")
    if not isinstance(observed_pull, dict) or not isinstance(expected_pull, dict):
        failures.append("pull request differs")
    else:
        rest = observed_pull.get("rest_merge_commit_sha")
        if rest not in {None, MERGE}:
            failures.append("REST merge SHA conflicts with the raw merge event")
        compared = deepcopy(observed_pull)
        compared["rest_merge_commit_sha"] = None
        if compared != expected_pull:
            if observed_pull.get("timeline_merge_commit_sha") != MERGE:
                failures.append("timeline merge event differs")
            if observed_pull.get("review_count") != 0:
                failures.append("review count differs")
            failures.append("pull request differs")

    observed_ci = projection.get("ci")
    expected_ci = expected.get("ci")
    if not isinstance(observed_ci, dict) or not isinstance(expected_ci, dict):
        failures.append("required CI differs")
    else:
        observed_sealed = observed_ci.get("sealed_head")
        expected_sealed = expected_ci.get("sealed_head")
        if not isinstance(observed_sealed, dict) or not isinstance(expected_sealed, dict):
            failures.append("required CI differs")
            failures.append("GitGuardian differs")
        else:
            if observed_sealed.get("runs") != expected_sealed.get("runs") or observed_sealed.get("required_checks") != expected_sealed.get("required_checks"):
                failures.append("required CI differs")
            if observed_sealed.get("gitguardian") != expected_sealed.get("gitguardian"):
                failures.append("GitGuardian unresolved failure differs")
        if observed_ci.get("merged_master") != expected_ci.get("merged_master"):
            failures.append("merged-master CI differs")

    governance = projection.get("governance")
    expected_governance = expected.get("governance")
    if not isinstance(governance, dict) or not isinstance(expected_governance, dict):
        failures.append("ruleset differs")
    else:
        if any(
            governance.get(key) != expected_governance.get(key)
            for key in ("branch", "branch_sha", "protected")
        ):
            failures.append("master branch differs")
        if any(
            governance.get(key) != expected_governance.get(key)
            for key in set(expected_governance) - {"branch", "branch_sha", "protected"}
        ):
            failures.append("ruleset or effective technical floor differs")

    conclusion = projection.get("conclusion")
    expected_conclusion = expected.get("conclusion")
    if not isinstance(conclusion, dict) or not isinstance(expected_conclusion, dict):
        failures.append("bounded conclusion differs")
    else:
        if conclusion.get("all_checks_green") != "contradicted":
            failures.append("all-checks-green conclusion differs")
        if conclusion.get("independent_review") != "blocked":
            failures.append("independent review conclusion differs")
        if conclusion.get("independent_ground_truth") != "blocked":
            failures.append("independent ground truth conclusion differs")
        if conclusion.get("scientific_authority") != "none":
            failures.append("scientific authority conclusion differs")
        if conclusion != expected_conclusion:
            failures.append("bounded conclusion differs")
    return sorted(set(failures))


def _decode_pointer(pointer: str) -> list[str]:
    if not pointer.startswith("/"):
        raise ValidationError("fixture patch is not a JSON pointer")
    return [part.replace("~1", "/").replace("~0", "~") for part in pointer[1:].split("/")]


def apply_fixture_patch(value: dict[str, Any], patch: dict[str, Any]) -> dict[str, Any]:
    candidate = deepcopy(value)
    for pointer, replacement in patch.items():
        parts = _decode_pointer(pointer)
        cursor: Any = candidate
        for part in parts[:-1]:
            cursor = cursor[int(part)] if isinstance(cursor, list) else cursor[part]
        terminal = parts[-1]
        if isinstance(cursor, list):
            cursor[int(terminal)] = deepcopy(replacement)
        else:
            cursor[terminal] = deepcopy(replacement)
    return candidate


def fixture_failures(root: Path = ROOT) -> list[str]:
    failures: list[str] = []
    try:
        safe = read_json(root / SAFE_FIXTURE.relative_to(ROOT), label="safe fixture")
        known_bad = read_json(root / KNOWN_BAD_FIXTURE.relative_to(ROOT), label="known-bad fixture")
        if not isinstance(safe, dict) or safe.get("schema_version") != "telos.iter241.iter240_repository_closure.safe.v1":
            return ["safe fixture schema differs"]
        if projection_failures(safe, expected=safe):
            failures.append("safe fixture does not pass its own exact contract")
        if not isinstance(known_bad, dict) or known_bad.get("schema_version") != "telos.iter241.iter240_repository_closure.known_bad.v1":
            return failures + ["known-bad fixture schema differs"]
        cases = known_bad.get("cases")
        if not isinstance(cases, list) or len(cases) < 22:
            return failures + ["known-bad fixture case census differs"]
        seen: set[str] = set()
        for case in cases:
            if not isinstance(case, dict) or set(case) != {"case_id", "expected_failure", "patch"}:
                failures.append("known-bad fixture case fields differ")
                continue
            case_id = case.get("case_id")
            marker = case.get("expected_failure")
            patch = case.get("patch")
            if not isinstance(case_id, str) or case_id in seen or not isinstance(marker, str) or not isinstance(patch, dict):
                failures.append("known-bad fixture identity differs")
                continue
            seen.add(case_id)
            observed = projection_failures(apply_fixture_patch(safe, patch), expected=safe)
            if not observed or not any(marker.lower() in item.lower() for item in observed):
                failures.append(f"known-bad fixture escaped or failed unclearly: {case_id}: {observed}")
    except (OSError, KeyError, IndexError, TypeError, ValueError, ValidationError) as exc:
        failures.append(f"fixture validation is unreadable: {exc}")
    return failures


def _parse_utc(value: object, *, label: str) -> datetime:
    if not isinstance(value, str) or not value.endswith("Z"):
        raise ValidationError(f"{label} is not canonical UTC")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValidationError(f"{label} is not an ISO instant") from exc
    if parsed.tzinfo != timezone.utc or parsed.microsecond:
        raise ValidationError(f"{label} is not second-resolution UTC")
    return parsed


def _selected_headers(header_document: object) -> dict[str, str | None]:
    if not isinstance(header_document, dict) or set(header_document) != {"schema_version", "headers"} or header_document.get("schema_version") != "telos.iter241.github_response_headers.v1":
        raise ValidationError("raw response-header document fields differ")
    rows = header_document.get("headers")
    if not isinstance(rows, list):
        raise ValidationError("raw response headers are not an array")
    grouped: dict[str, list[str]] = {}
    for row in rows:
        if not isinstance(row, dict) or set(row) != {"name", "value"}:
            raise ValidationError("raw response header row fields differ")
        name = row.get("name")
        value = row.get("value")
        if not isinstance(name, str) or not isinstance(value, str) or "\n" in name + value or "\r" in name + value:
            raise ValidationError("raw response header is unsafe")
        grouped.setdefault(name.lower(), []).append(value.strip())
    for required in ("date", "x-github-api-version-selected", "x-github-request-id", "content-type"):
        if len(grouped.get(required, [])) != 1 or not grouped[required][0]:
            raise ValidationError(f"required response header is ambiguous: {required}")
    if "application/json" not in grouped["content-type"][0].lower():
        raise ValidationError("response Content-Type is not JSON")
    for optional in ("etag", "link", "content-encoding"):
        if len(grouped.get(optional, [])) > 1:
            raise ValidationError(f"response header is duplicated: {optional}")
    if grouped.get("content-encoding", ["identity"])[0].lower() not in {"identity", ""}:
        raise ValidationError("response was content-encoded despite identity request")
    date_value = grouped["date"][0]
    try:
        parsed_date = parsedate_to_datetime(date_value)
    except (TypeError, ValueError) as exc:
        raise ValidationError("GitHub Date header is invalid") from exc
    if parsed_date.tzinfo is None:
        raise ValidationError("GitHub Date header lacks timezone")
    response_date = parsed_date.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    return {
        "response_date": response_date,
        "api_version_selected": grouped["x-github-api-version-selected"][0],
        "github_request_id": grouped["x-github-request-id"][0],
        "etag": grouped.get("etag", [None])[0],
        "link": grouped.get("link", [None])[0],
    }


def validate(
    *,
    root: Path = ROOT,
    receipt_path: Path = RECEIPT,
    raw_root: Path = RAW_ROOT,
    check_repository: bool = True,
) -> list[str]:
    failures: list[str] = []
    if check_repository:
        failures.extend(repository_failures(root))
    failures.extend(fixture_failures(root))
    try:
        receipt = read_json(receipt_path, label="repository-closure receipt")
        marker_path = raw_root / "capture_attempt.json"
        marker_raw = _regular_0644(marker_path, label="attempt marker")
        marker = strict_json_bytes(marker_raw, label="attempt marker")
        if not isinstance(marker, dict):
            raise ValidationError("attempt marker is not an object")
        marker_required = {
            "schema_version", "repository", "api_version", "armed_at", "state",
            "request_plan", "request_plan_sha256", "planned_request_counts",
            "authorization_head", "instruments",
        }
        if set(marker) != marker_required or marker.get("schema_version") != "telos.iter241.iter240_repository_closure.attempt.v1":
            failures.append("attempt marker fields or schema differ")
        if marker.get("repository") != REPOSITORY or marker.get("api_version") != API_VERSION or marker.get("authorization_head") != AUTHORIZATION_HEAD:
            failures.append("attempt marker identity differs")
        if marker.get("state") != "armed_before_first_request":
            failures.append("attempt marker was not armed before request one")
        plan = request_plan()
        if marker.get("request_plan") != plan or marker.get("request_plan_sha256") != sha256_bytes(canonical_json(plan)):
            failures.append("attempt marker request plan differs")
        if marker.get("planned_request_counts") != expected_counts():
            failures.append("attempt marker write count differs")
        instruments = marker.get("instruments")
        if not isinstance(instruments, list) or len(instruments) < 7:
            failures.append("attempt marker instrument inventory differs")
        else:
            seen_paths: set[str] = set()
            for item in instruments:
                if not isinstance(item, dict) or set(item) != {"path", "byte_count", "sha256"}:
                    failures.append("attempt marker instrument fields differ")
                    continue
                relative = item.get("path")
                if not isinstance(relative, str) or relative in seen_paths:
                    failures.append("attempt marker instrument path differs")
                    continue
                seen_paths.add(relative)
                pure = PurePosixPath(relative)
                if pure.is_absolute() or ".." in pure.parts or pure.as_posix() != relative:
                    failures.append("attempt marker instrument path is unsafe")
                    continue
                raw = _regular_0644(root.joinpath(*pure.parts), label=f"instrument {relative}")
                if item.get("byte_count") != len(raw) or item.get("sha256") != sha256_bytes(raw):
                    failures.append(f"attempt marker instrument hash drift: {relative}")

        if not isinstance(receipt, dict):
            raise ValidationError("receipt is not an object")
        required_receipt = {
            "schema_version", "repository", "api_version", "capture",
            "request_counts", "projection", "limitations",
        }
        if set(receipt) != required_receipt or receipt.get("schema_version") != "telos.iter241.iter240_repository_closure.v1":
            failures.append("receipt fields or schema differ")
        if receipt.get("repository") != REPOSITORY or receipt.get("api_version") != API_VERSION:
            failures.append("receipt repository or API version differs")
        if receipt.get("request_counts") != expected_counts():
            failures.append("receipt write count differs")
        if receipt.get("limitations") != LIMITATIONS:
            failures.append("receipt bounded limitations differ")
        capture = receipt.get("capture")
        if not isinstance(capture, dict) or set(capture) != {"started_at", "completed_at", "attempt_marker", "response_inventory"}:
            raise ValidationError("receipt capture fields differ")
        started = _parse_utc(capture.get("started_at"), label="capture started_at")
        completed = _parse_utc(capture.get("completed_at"), label="capture completed_at")
        armed = _parse_utc(marker.get("armed_at"), label="attempt armed_at")
        if armed != started or completed < started or completed - started > timedelta(minutes=5):
            failures.append("capture/arming window differs")
        marker_binding = capture.get("attempt_marker")
        expected_marker_path = "experiments/iter241_iter240_repository_closure/proof/raw/iter240_repository_closure/capture_attempt.json"
        expected_marker_binding = {
            "raw_body_path": expected_marker_path,
            "raw_body_byte_count": len(marker_raw),
            "raw_body_sha256": sha256_bytes(marker_raw),
        }
        if marker_binding != expected_marker_binding:
            failures.append("attempt marker receipt binding differs")
        inventory = capture.get("response_inventory")
        if not isinstance(inventory, list) or len(inventory) != len(ENDPOINTS):
            raise ValidationError("response inventory census differs")
        documents: dict[str, Any] = {}
        request_ids: list[str] = []
        response_dates: list[datetime] = []
        required_inventory_fields = {
            "name", "method", "request_path", "http_status",
            "response_date", "api_version_selected", "github_request_id",
            "etag", "link", "raw_headers_path", "raw_headers_byte_count",
            "raw_headers_sha256", "raw_body_path", "raw_body_byte_count",
            "raw_body_sha256",
        }
        for item, (name, request_path, filename) in zip(inventory, ENDPOINTS, strict=True):
            if not isinstance(item, dict) or set(item) != required_inventory_fields:
                raise ValidationError(f"response inventory fields differ: {name}")
            if item.get("name") != name or item.get("method") != "GET" or item.get("request_path") != request_path or item.get("http_status") != 200:
                failures.append(f"response inventory request identity differs: {name}")
            body_path = raw_root / filename
            headers_filename = filename.removesuffix(".json") + ".headers.json"
            headers_path = raw_root / headers_filename
            body_raw = _regular_0644(body_path, label=f"raw body {name}")
            headers_raw = _regular_0644(headers_path, label=f"raw headers {name}")
            if len(body_raw) > MAX_RESPONSE_BYTES:
                failures.append(f"raw response exceeds size cap: {name}")
            expected_body_path = f"experiments/iter241_iter240_repository_closure/proof/raw/iter240_repository_closure/{filename}"
            expected_headers_path = f"experiments/iter241_iter240_repository_closure/proof/raw/iter240_repository_closure/{headers_filename}"
            if (
                item.get("raw_body_path") != expected_body_path
                or item.get("raw_body_byte_count") != len(body_raw)
                or item.get("raw_body_sha256") != sha256_bytes(body_raw)
            ):
                failures.append(f"raw body hash or path differs: {name}")
            if (
                item.get("raw_headers_path") != expected_headers_path
                or item.get("raw_headers_byte_count") != len(headers_raw)
                or item.get("raw_headers_sha256") != sha256_bytes(headers_raw)
            ):
                failures.append(f"raw header hash or path differs: {name}")
            selected = _selected_headers(strict_json_bytes(headers_raw, label=f"raw headers {name}"))
            for key in ("response_date", "api_version_selected", "github_request_id", "etag", "link"):
                if item.get(key) != selected[key]:
                    failures.append(f"selected response header differs: {name}: {key}")
            if selected["api_version_selected"] != API_VERSION:
                failures.append(f"GitHub selected a different API version: {name}")
            if selected["link"] is not None:
                failures.append(f"unexpected pagination Link: {name}")
            request_id = selected["github_request_id"]
            if not isinstance(request_id, str) or REQUEST_ID_RE.fullmatch(request_id) is None:
                failures.append(f"GitHub request ID is malformed: {name}")
            else:
                request_ids.append(request_id)
            response_date = _parse_utc(selected["response_date"], label=f"response date {name}")
            response_dates.append(response_date)
            if response_date < started - timedelta(minutes=5) or response_date > completed + timedelta(minutes=5):
                failures.append(f"response date lies outside capture window: {name}")
            documents[name] = strict_json_bytes(body_raw, label=f"raw body {name}")
        if len(request_ids) != len(set(request_ids)):
            failures.append("GitHub request IDs are not unique")
        if response_dates != sorted(response_dates):
            failures.append("GitHub response dates are not nondecreasing")
        merged_run = documents.get("merged_master_run")
        if isinstance(merged_run, dict):
            run_completed_raw = merged_run.get("updated_at")
            run_completed = _parse_utc(run_completed_raw, label="merged-master run updated_at")
            if response_dates and run_completed > response_dates[0]:
                failures.append("capture preceded merged-master CI completion")
        else:
            failures.append("merged-master run response is malformed")

        independently_projected = document_projection(documents)
        retained_projection = receipt.get("projection")
        if retained_projection != independently_projected:
            failures.append("retained projection differs from independently parsed raw responses")
        failures.extend(projection_failures(independently_projected))
    except (OSError, KeyError, TypeError, ValueError, ValidationError, subprocess.SubprocessError) as exc:
        failures.append(f"repository-closure evidence is unreadable: {exc}")
    return sorted(set(failures))


def main() -> int:
    failures = validate()
    if failures:
        for failure in failures:
            print(f"iter240 repository closure: {failure}")
        return 1
    print("iter240 repository closure validates: 13 GET, 0 writes; required CI supported; GitGuardian failure retained; zero reviews")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
