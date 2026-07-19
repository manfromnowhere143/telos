#!/usr/bin/env python3
"""Validate Telos's mutable current-state pointer against its public surfaces.

The large ``mission/loop.json``, root ``HANDOFF.md``, and ``CONTINUITY.md`` are
sealed historical evidence. This guard deliberately does not reinterpret or
rewrite them. It checks the small mutable pointer that a new session reads
first and fails when that pointer, AGENTS bootstrap, README, dated handoff,
audit, active gate, or paper revision disagree.
"""

from __future__ import annotations

from datetime import date
import json
import re
import stat
import subprocess
from pathlib import Path
from pathlib import PurePosixPath
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CURRENT = Path("mission/current.json")
AGENTS = Path("AGENTS.md")
README = Path("README.md")
PAPER = Path("paper/telos.tex")
REGISTRY_PATHS = {
    "claim_registry": "mission/claim_registry.json",
    "seal_registry": "mission/seal_registry.json",
    "workflow_registry": "mission/workflow_registry.json",
}
CURRENT_FIELDS = {
    "schema_version",
    "updated",
    "status",
    "active_gate",
    "current_handoff",
    "current_audit",
    *REGISTRY_PATHS,
    "paper_revision",
    "scientific_status",
    "next_authorized_action",
    "claim_boundary",
    "historical_surfaces",
}
REGISTRY_SCHEMAS = {
    "claim_registry": "telos.claim_registry.v2",
    "seal_registry": "telos.seal-registry.v1",
    "workflow_registry": "telos.workflow_registry.v1",
}
SYNC_START = "<!-- telos-current-state:start -->"
SYNC_END = "<!-- telos-current-state:end -->"
AGENTS_POINTER_SENTENCE = (
    "Read `mission/current.json` first, then read the dated handoff named by its "
    "`current_handoff` field."
)
AGENTS_HISTORICAL_SENTENCE = (
    "`HANDOFF.md`, `CONTINUITY.md`, and `mission/loop.json` are sealed historical "
    "TCP-1 artifacts; they remain required evidence inputs but are not the current "
    "operational baton."
)
AGENTS_OTHER_HANDOFFS_SENTENCE = (
    "Every other `docs/HANDOFF-*.md` is a historical baton; embedded current, "
    "active, next, or authority wording is non-operative."
)
AGENTS_AUDIT_SENTENCE = (
    "The exact `current_audit` is dated analysis context, not execution authority; "
    "every other dated audit is historical and non-operative."
)
CURRENT_HANDOFF_PATTERN = re.compile(
    r"docs/HANDOFF-(?P<date>\d{4}-\d{2}-\d{2})-"
    r"iter(?P<iteration>\d+)\.md"
)
CURRENT_AUDIT_PATTERN = re.compile(
    r"docs/TELOS-AUDIT-(?P<date>\d{4}-\d{2}-\d{2})\.md"
)
CURRENT_AUDIT_ROLE = (
    "**DATED ANALYSIS CONTEXT — NOT EXECUTION AUTHORITY.** This audit is the exact"
)
ACTIVE_GATE_PATTERN = re.compile(
    r"experiments/iter(?P<iteration>\d+)_[a-z0-9][a-z0-9_-]*/HYPOTHESIS\.md"
)
EXPERIMENT_DIRECTORY_PATTERN = re.compile(
    r"experiments/iter\d+_[a-z0-9][a-z0-9_-]*"
)

ALLOWED_STATUSES = {
    "proposed",
    "exploratory",
    "preregistered",
    "running",
    "blocked",
    "invalid",
    "null",
    "inconclusive",
    "failed",
    "supported",
    "contradicted",
    "replicated",
    "corrected",
    "retracted",
}
HISTORICAL_SURFACES = ["CONTINUITY.md", "HANDOFF.md", "mission/loop.json"]
DEMOTED_COMPATIBILITY_SURFACES = {
    Path("docs/TELOS-ROADMAP-2026.md"): (
        "HISTORICAL ROADMAP SNAPSHOT — NOT CURRENT AUTHORITY",
        "mission/current.json",
    ),
    Path("docs/NEXT_PHASE.md"): (
        "SUPERSEDED HISTORICAL PLAN — NOT CURRENT AUTHORITY",
        "mission/current.json",
    ),
    Path("docs/MISSION_LOOP.md"): (
        "historical compatibility pointer",
        "mission/current.json",
    ),
    Path("results/README.md"): (
        "not a results authority",
        "mission/current.json",
    ),
    Path("docs/ARCHITECTURE.md"): (
        "Historical foundational design",
        "mission/current.json",
    ),
    Path("docs/LEARNING_ENGINE.md"): (
        "Historical ledger view — not the operational baton",
        "mission/current.json",
    ),
    Path("docs/REPORT.md"): (
        "SUPERSEDED HISTORICAL REPORT",
        "mission/current.json",
    ),
    Path("docs/COMPLETION_VERIFICATION_REPORT.md"): (
        "HISTORICAL SCOPE",
        "mission/current.json",
    ),
    Path("docs/LITERATURE_ALIGNMENT_2026.md"): (
        "DATED HISTORICAL MEMO",
        "mission/current.json",
    ),
}


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _reject_nonfinite(value: str) -> None:
    raise ValueError(f"non-finite JSON number: {value}")


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(
        path.read_text(encoding="utf-8"),
        object_pairs_hook=_unique_object,
        parse_constant=_reject_nonfinite,
    )
    if not isinstance(value, dict):
        raise ValueError("document must be a JSON object")
    return value


def _canonical_relative_path(value: object, field: str) -> tuple[str | None, str | None]:
    if not isinstance(value, str) or not value:
        return None, f"{field} must be a non-empty repository-relative path"
    if (
        "\\" in value
        or any(ord(character) < 0x20 or ord(character) == 0x7F for character in value)
    ):
        return None, f"{field} is not a canonical repository-relative path"
    pure = PurePosixPath(value)
    if (
        pure.is_absolute()
        or pure.as_posix() != value
        or any(part in {"", ".", ".."} for part in pure.parts)
    ):
        return None, f"{field} is not a canonical repository-relative path"
    return value, None


def _git_index_mode(root: Path, relative: str) -> tuple[str | None, str | None]:
    probe = subprocess.run(
        [
            "git",
            "-C",
            str(root),
            "ls-files",
            "--stage",
            "-z",
            "--",
            f":(literal){relative}",
        ],
        capture_output=True,
        check=False,
    )
    if probe.returncode != 0:
        return None, None
    entries = [entry for entry in probe.stdout.split(b"\0") if entry]
    if not entries:
        # New authority files are permitted while an integration commit is being
        # assembled. Once tracked, their index mode is enforced.
        return None, None
    if len(entries) != 1:
        return None, f"{relative} has an ambiguous Git index entry"
    try:
        metadata, observed = entries[0].split(b"\t", 1)
        mode, _, stage = metadata.decode("ascii").split()
        observed_path = observed.decode("utf-8")
    except (UnicodeDecodeError, ValueError):
        return None, f"{relative} has an unreadable Git index entry"
    if observed_path != relative or stage != "0":
        return None, f"{relative} has an ambiguous Git index entry"
    return mode, None


def _relative_file(
    root: Path,
    value: object,
    field: str,
) -> tuple[Path | None, str | None]:
    relative, error = _canonical_relative_path(value, field)
    if error is not None or relative is None:
        return None, error
    pure = PurePosixPath(relative)
    cursor = root
    for part in pure.parts[:-1]:
        cursor = cursor / part
        try:
            metadata = cursor.lstat()
        except OSError:
            return None, f"{field} ancestor is absent: {relative}"
        if not stat.S_ISDIR(metadata.st_mode) or cursor.is_symlink():
            return None, f"{field} ancestor is not a real directory: {relative}"
    path = root.joinpath(*pure.parts)
    try:
        metadata = path.lstat()
    except OSError:
        return None, f"{field} does not name a file: {relative}"
    if (
        not stat.S_ISREG(metadata.st_mode)
        or path.is_symlink()
        or stat.S_IMODE(metadata.st_mode) != 0o644
    ):
        return None, f"{field} must be a regular non-symlink mode-100644 file: {relative}"
    index_mode, index_error = _git_index_mode(root, relative)
    if index_error is not None:
        return None, f"{field}: {index_error}"
    if index_mode is not None and index_mode != "100644":
        return None, f"{field} Git index mode must be 100644: {relative}"
    return path, None


def _is_real_calendar_date(value: object) -> bool:
    if not isinstance(value, str):
        return False
    try:
        return date.fromisoformat(value).isoformat() == value
    except ValueError:
        return False


def _sync_block(document: str, label: str) -> tuple[dict[str, str], list[str]]:
    failures: list[str] = []
    if document.count(SYNC_START) != 1 or document.count(SYNC_END) != 1:
        return {}, [f"{label} must contain one current-state synchronization block"]
    body = document.split(SYNC_START, 1)[1].split(SYNC_END, 1)[0]
    lines = [line.strip() for line in body.splitlines() if line.strip()]
    if lines and lines[0] == "```text":
        lines = lines[1:]
    if lines and lines[-1] == "```":
        lines = lines[:-1]
    values: dict[str, str] = {}
    for line in lines:
        if ": " not in line:
            failures.append(f"{label} current-state block has a malformed line")
            continue
        key, value = line.split(": ", 1)
        if not key or not value or key in values:
            failures.append(f"{label} current-state block has duplicate or empty fields")
            continue
        values[key] = value
    return values, failures


def _markdown_targets(document: str) -> set[str]:
    return {
        target.split("#", 1)[0]
        for target in re.findall(r"\[[^\]]+\]\(([^)]+)\)", document)
    }


def _agents_bootstrap(document: str) -> str | None:
    match = re.search(
        r"(?ms)^## Start of session\s*\n(?P<section>.*?)(?=^## |\Z)",
        document,
    )
    if match is None:
        return None
    return " ".join(match.group("section").split())


def _leading_role_block(document: str) -> str | None:
    """Return the first prose block after one leading Markdown title."""

    lines = document.splitlines()
    cursor = 0
    while cursor < len(lines) and not lines[cursor].strip():
        cursor += 1
    if cursor >= len(lines) or not lines[cursor].startswith("# "):
        return None
    cursor += 1
    while cursor < len(lines) and not lines[cursor].strip():
        cursor += 1
    block: list[str] = []
    while cursor < len(lines) and lines[cursor].strip():
        block.append(lines[cursor].strip())
        cursor += 1
    if not block:
        return None
    return " ".join(block)


def _leading_document_context(document: str) -> str:
    """Return content before the first level-two section."""

    return document.split("\n## ", 1)[0]


def _authorized_directory(value: object, field: str) -> tuple[str | None, str | None]:
    relative, error = _canonical_relative_path(value, field)
    if error is not None or relative is None:
        return None, error
    if EXPERIMENT_DIRECTORY_PATTERN.fullmatch(relative) is None:
        return None, f"{field} is not a canonical experiment directory"
    return relative, None


def _seal_frontier(
    root: Path,
    seal: dict[str, Any],
) -> tuple[str | None, list[str]]:
    """Derive the current gate from the independently checked seal lifecycle."""

    failures: list[str] = []
    records = seal.get("records")
    if not isinstance(records, list) or not records:
        return None, ["seal registry has no lifecycle records"]
    baseline = records[0]
    if not isinstance(baseline, dict) or baseline.get("record_type") != (
        "retrospective_path_snapshot"
    ):
        return None, ["seal registry lifecycle baseline differs"]

    open_authorizations: dict[tuple[str, str], None] = {}
    latest_sealed: str | None = None
    baseline_id = baseline.get("seal_id")
    successors = baseline.get("allowed_additive_successors")
    if not isinstance(baseline_id, str) or not baseline_id:
        failures.append("seal registry baseline seal_id is invalid")
    if not isinstance(successors, list) or not successors:
        failures.append("seal registry baseline has no additive successor")
    else:
        for index, successor in enumerate(successors):
            if not isinstance(successor, dict):
                failures.append(f"seal baseline successor {index} is not an object")
                continue
            path, error = _authorized_directory(
                successor.get("path"),
                f"seal baseline successor {index}",
            )
            if error is not None or path is None or not isinstance(baseline_id, str):
                failures.append(error or f"seal baseline successor {index} is invalid")
                continue
            open_authorizations[(baseline_id, path)] = None

    for index, record in enumerate(records[1:], start=1):
        if not isinstance(record, dict):
            failures.append(f"seal registry record {index} is not an object")
            continue
        record_type = record.get("record_type")
        if record_type == "prospective_successor_authorization":
            seal_id = record.get("seal_id")
            path, error = _authorized_directory(
                record.get("authorized_path"),
                f"seal prospective authorization {index}",
            )
            if (
                error is not None
                or path is None
                or not isinstance(seal_id, str)
                or not seal_id
            ):
                failures.append(error or f"seal prospective authorization {index} is invalid")
                continue
            key = (seal_id, path)
            if key in open_authorizations:
                failures.append("seal lifecycle repeats an open authorization")
            open_authorizations[key] = None
        elif record_type == "successor_path_snapshot":
            predecessor = record.get("predecessor_seal_id")
            protected_sets = record.get("protected_sets")
            paths: list[str] = []
            if isinstance(protected_sets, list):
                for protected in protected_sets:
                    selector = (
                        protected.get("selector")
                        if isinstance(protected, dict)
                        else None
                    )
                    if (
                        isinstance(selector, dict)
                        and selector.get("kind") == "tree"
                    ):
                        path, error = _authorized_directory(
                            selector.get("path"),
                            f"seal successor snapshot {index}",
                        )
                        if error is not None:
                            failures.append(error)
                        elif path is not None:
                            paths.append(path)
            if not isinstance(predecessor, str) or len(paths) != 1:
                failures.append(f"seal successor snapshot {index} is ambiguous")
                continue
            key = (predecessor, paths[0])
            if key not in open_authorizations:
                failures.append(
                    f"seal successor snapshot {index} has no open authorization"
                )
                continue
            del open_authorizations[key]
            latest_sealed = paths[0]

    if len(open_authorizations) > 1:
        failures.append("seal lifecycle has more than one open successor")
        return None, failures
    if open_authorizations:
        _, open_path = next(iter(open_authorizations))
        open_directory = root / open_path
        hypothesis = root / open_path / "HYPOTHESIS.md"
        try:
            open_metadata = open_directory.lstat()
        except OSError:
            if latest_sealed is not None:
                return f"{latest_sealed}/HYPOTHESIS.md", failures
            return f"{open_path}/HYPOTHESIS.md", failures
        if not stat.S_ISDIR(open_metadata.st_mode) or open_directory.is_symlink():
            failures.append(
                "open seal successor materialized as a non-directory before "
                f"preregistration: {open_path}"
            )
            if latest_sealed is not None:
                return f"{latest_sealed}/HYPOTHESIS.md", failures
            return f"{open_path}/HYPOTHESIS.md", failures
        try:
            hypothesis.lstat()
        except OSError:
            failures.append(
                "open seal successor materialized without HYPOTHESIS.md: "
                f"{open_path}"
            )
            if latest_sealed is not None:
                return f"{latest_sealed}/HYPOTHESIS.md", failures
        return f"{open_path}/HYPOTHESIS.md", failures
    if latest_sealed is not None:
        return f"{latest_sealed}/HYPOTHESIS.md", failures
    failures.append("seal lifecycle does not identify a current gate")
    return None, failures


def validate(*, root: Path = ROOT) -> list[str]:
    failures: list[str] = []
    for relative, label in (
        (CURRENT.as_posix(), "current pointer"),
        (AGENTS.as_posix(), "AGENTS bootstrap"),
        (README.as_posix(), "README"),
        (PAPER.as_posix(), "current paper source"),
    ):
        _, authority_error = _relative_file(root, relative, label)
        if authority_error is not None:
            failures.append(authority_error)
    try:
        current = _read_json(root / CURRENT)
    except (OSError, json.JSONDecodeError, ValueError) as error:
        return [f"current pointer is unreadable: {error}"]

    if set(current) != CURRENT_FIELDS:
        failures.append("current pointer fields differ")
    if current.get("schema_version") != "telos.current.v1":
        failures.append("current pointer schema differs")
    updated = current.get("updated")
    if not _is_real_calendar_date(updated):
        failures.append("updated must be an ISO calendar date")
    if current.get("status") not in ALLOWED_STATUSES:
        failures.append("status is not an allowed research status")
    if current.get("historical_surfaces") != HISTORICAL_SURFACES:
        failures.append("sealed historical surfaces are not identified exactly")

    bound_paths: dict[str, tuple[Path | None, str | None]] = {}
    for field in (
        "active_gate",
        "current_handoff",
        "current_audit",
        *REGISTRY_PATHS,
    ):
        bound_paths[field] = _relative_file(root, current.get(field), field)
        if bound_paths[field][1]:
            failures.append(bound_paths[field][1] or "")
    for field, expected in REGISTRY_PATHS.items():
        if current.get(field) != expected:
            failures.append(f"{field} must be the canonical path {expected}")

    active_gate = current.get("active_gate")
    active_gate_match = (
        ACTIVE_GATE_PATTERN.fullmatch(active_gate)
        if isinstance(active_gate, str)
        else None
    )
    if active_gate_match is None:
        failures.append("active_gate is not an iteration hypothesis")
    current_handoff = current.get("current_handoff")
    handoff_match = (
        CURRENT_HANDOFF_PATTERN.fullmatch(current_handoff)
        if isinstance(current_handoff, str)
        else None
    )
    if handoff_match is None:
        failures.append("current_handoff is not a canonical dated iteration handoff")
    else:
        handoff_date = handoff_match.group("date")
        if not _is_real_calendar_date(handoff_date):
            failures.append("current_handoff filename date is not a real calendar date")
        if handoff_date != updated:
            failures.append("current_handoff filename date differs from updated")
        if (
            active_gate_match is not None
            and handoff_match.group("iteration")
            != active_gate_match.group("iteration")
        ):
            failures.append("current_handoff iteration differs from active_gate")
    current_audit = current.get("current_audit")
    audit_match = (
        CURRENT_AUDIT_PATTERN.fullmatch(current_audit)
        if isinstance(current_audit, str)
        else None
    )
    if audit_match is None:
        failures.append("current_audit is not a canonical dated Telos audit")
    else:
        audit_date = audit_match.group("date")
        if not _is_real_calendar_date(audit_date):
            failures.append("current_audit filename date is not a real calendar date")
        if audit_date != updated:
            failures.append("current_audit filename date differs from updated")

    for field in ("scientific_status", "next_authorized_action", "claim_boundary"):
        value = current.get(field)
        if not isinstance(value, str) or not value.strip():
            failures.append(f"{field} must be a non-empty string")

    paper_revision = current.get("paper_revision")
    if not isinstance(paper_revision, str) or not paper_revision:
        failures.append("paper_revision must be a non-empty date label")

    try:
        agents = (root / AGENTS).read_text(encoding="utf-8")
        readme = (root / README).read_text(encoding="utf-8")
        paper = (root / PAPER).read_text(encoding="utf-8")
    except OSError as error:
        failures.append(f"current public surface is unreadable: {error}")
        return failures

    bootstrap = _agents_bootstrap(agents)
    if bootstrap is None or not bootstrap.startswith(AGENTS_POINTER_SENTENCE):
        failures.append("AGENTS bootstrap does not require the canonical current pointer")
    if bootstrap is None or AGENTS_HISTORICAL_SENTENCE not in bootstrap:
        failures.append(
            "AGENTS bootstrap does not identify the exact sealed historical baton"
        )
    if bootstrap is None or AGENTS_OTHER_HANDOFFS_SENTENCE not in bootstrap:
        failures.append(
            "AGENTS bootstrap does not demote every non-current dated handoff"
        )
    if bootstrap is None or AGENTS_AUDIT_SENTENCE not in bootstrap:
        failures.append(
            "AGENTS bootstrap does not demote audits as non-execution authority"
        )

    for relative, required_markers in DEMOTED_COMPATIBILITY_SURFACES.items():
        _, compatibility_error = _relative_file(
            root,
            relative.as_posix(),
            f"demoted compatibility surface {relative.as_posix()}",
        )
        if compatibility_error is not None:
            failures.append(compatibility_error)
            continue
        try:
            content = (root / relative).read_text(encoding="utf-8")
        except OSError as error:
            failures.append(
                f"demoted compatibility surface is unreadable: {relative}: {error}"
            )
            continue
        role_block = _leading_role_block(content)
        if role_block is None or required_markers[0] not in role_block:
            failures.append(
                "demoted compatibility surface lacks leading authority role: "
                f"{relative}: {required_markers[0]}"
            )
        leading_context = _leading_document_context(content)
        for marker in required_markers[1:]:
            if marker not in leading_context:
                failures.append(
                    "demoted compatibility surface lacks leading authority marker: "
                    f"{relative}: {marker}"
                )

    readme_targets = _markdown_targets(readme)
    for field in (
        "active_gate",
        "current_handoff",
        "current_audit",
        *REGISTRY_PATHS,
    ):
        value = current.get(field)
        if isinstance(value, str) and value not in readme_targets:
            failures.append(f"README does not bind {field}: {value}")

    if isinstance(paper_revision, str) and f"\\date{{{paper_revision}}}" not in paper:
        failures.append("paper revision does not match mission/current.json")

    synchronized_fields = (
        "status",
        "scientific_status",
        "claim_boundary",
        "next_authorized_action",
    )
    readme_sync, readme_sync_failures = _sync_block(readme, "README")
    failures.extend(readme_sync_failures)
    for field in synchronized_fields:
        if readme_sync.get(field) != current.get(field):
            failures.append(f"README current-state block does not bind {field}")

    handoff_path = bound_paths.get("current_handoff", (None, None))[0]
    if handoff_path is not None:
        handoff = handoff_path.read_text(encoding="utf-8")
        handoff_sync, handoff_sync_failures = _sync_block(handoff, "current handoff")
        failures.extend(handoff_sync_failures)
        for field in (
            "updated",
            "status",
            "active_gate",
            "current_handoff",
            "current_audit",
            *REGISTRY_PATHS,
            "scientific_status",
            "next_authorized_action",
            "claim_boundary",
        ):
            value = current.get(field)
            if not isinstance(value, str) or handoff_sync.get(field) != value:
                failures.append(f"current handoff does not bind {field}")

    audit_path = bound_paths.get("current_audit", (None, None))[0]
    if audit_path is not None:
        audit = audit_path.read_text(encoding="utf-8")
        audit_role = _leading_role_block(audit)
        if audit_role is None or CURRENT_AUDIT_ROLE not in audit_role:
            failures.append(
                "current audit does not lead with its dated "
                "non-execution-authority role"
            )

    claim_path = bound_paths.get("claim_registry", (None, None))[0]
    workflow_path = bound_paths.get("workflow_registry", (None, None))[0]
    seal_path = bound_paths.get("seal_registry", (None, None))[0]
    registries: dict[str, dict[str, Any] | None] = {
        "claim_registry": None,
        "workflow_registry": None,
        "seal_registry": None,
    }
    for label, path, destination in (
        ("claim_registry", claim_path, "claim_registry"),
        ("workflow_registry", workflow_path, "workflow_registry"),
        ("seal_registry", seal_path, "seal_registry"),
    ):
        if path is None:
            continue
        try:
            registries[destination] = _read_json(path)
        except (OSError, json.JSONDecodeError, ValueError) as error:
            failures.append(f"{label.replace('_', ' ')} is unreadable: {error}")

    claim = registries["claim_registry"]
    workflow = registries["workflow_registry"]
    seal = registries["seal_registry"]
    for field, registry in registries.items():
        if registry is None:
            continue
        if registry.get("schema_version") != REGISTRY_SCHEMAS[field]:
            failures.append(f"{field.replace('_', ' ')} schema differs")
    if claim is not None and claim.get("active_gate") != active_gate:
        failures.append("existing-but-stale active gate: claim registry disagrees")
    if workflow is not None and workflow.get("active_gate") != active_gate:
        failures.append("existing-but-stale active gate: workflow registry disagrees")
    if workflow is not None and workflow.get("updated") != current.get("updated"):
        failures.append("workflow registry does not bind current updated date")
    if (
        workflow is not None
        and workflow.get("seal_registry") != REGISTRY_PATHS["seal_registry"]
    ):
        failures.append("workflow registry does not bind the canonical seal registry")
    if seal is not None:
        expected_gate, lifecycle_failures = _seal_frontier(root, seal)
        failures.extend(lifecycle_failures)
        if expected_gate is not None and active_gate != expected_gate:
            failures.append(
                "existing-but-stale active gate: seal lifecycle identifies "
                f"{expected_gate}"
            )

    return failures


def main() -> int:
    failures = validate()
    if failures:
        for failure in failures:
            print(f"current-state: {failure}")
        return 1
    print(
        "current-state pointer, bootstrap, handoff, README, and paper agree; "
        "audit path and non-execution-authority role are bound"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
