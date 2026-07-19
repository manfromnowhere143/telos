#!/usr/bin/env python3
"""Build iter240's provider-free ground-truth admission evidence.

This builder deliberately separates selection from diagnosis.  The selector can
read only three exact boolean predicates from the two frozen fresh-cohort
candidate tables.  Only after that census is fixed does the diagnostic pass
read scenario, execution, or judge evidence.

Every scientific input is a named, tracked, regular Git blob whose bytes must
match the exact merged iter239 predecessor.  No network, provider, container,
GPU, target execution, or model call is reachable from this module.
"""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from decimal import Decimal, ROUND_HALF_EVEN, localcontext
from fractions import Fraction
import hashlib
import json
import math
from pathlib import Path
import re
import stat
import subprocess
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from telos.json_compare import compare_json  # noqa: E402


ITERATION = Path("experiments/iter240_ground_truth_admission_design")
PROOF = ITERATION / "proof"
FIXTURES = ITERATION / "fixtures"

PREDECESSOR = "b597b763f2eb52b2f4f2d36e7daaa31654be076b"
PREDECESSOR_FIRST_PARENT = "fb87af7eb15b5235a722a7bb3fd3a48962019188"
PREDECESSOR_SECOND_PARENT = "56fb78f5f8afcd8709fde1170e8422072626f367"
AUTHORIZATION = "cf809ac0e06f37127553e99a2ab9b0705f8e2fae"
ACTIVATION = "63f5786b9b5c60d2bea90f2077208cfb745c31a2"
HISTORICAL_SEAL = "iter237-merged-historical-baseline"
HISTORICAL_REFERENCE = "7307e0c1c4083443698cfde8f0ab20a27518717c"

SNAPSHOT = Path(
    "experiments/iter154_reward_hack_benchmark_expansion_pilot"
    "/proof/raw/swebench_verified_rows_snapshot.json"
)
ITER237_CORRECTION = Path(
    "experiments/iter237_truth_maintenance_gate/proof/correction.json"
)
ITER230_EVAL = Path(
    "experiments/iter230_gold_free_detector_natural/proof/raw/eval_set.json"
)
ITER235_TARGETS = Path(
    "experiments/iter235_witness_recovery/proof/raw/targets.json"
)
ITER235_WITNESSES = Path(
    "experiments/iter235_witness_recovery/proof/raw/witnesses/witnesses_summary.json"
)
ITER235_JUDGES = Path(
    "experiments/iter235_witness_recovery/proof/raw/judge/judge_summary.json"
)

FRESH_RUNS = (
    "iter224_natural_rate_scale_n",
    "iter228_fresh_diverse_cohort",
)
NATURAL_RUNS = (
    "iter200_natural_certified_yet_wrong_rate",
    "iter223_natural_rate_safety_aware",
    "iter225_cross_model_generalization",
    "iter226_cross_model_generalization_gpt54",
    "iter227_cross_provider_generalization",
    "iter229_cross_provider_gemini",
)
RUN_ORDER = {run: index for index, run in enumerate(NATURAL_RUNS + FRESH_RUNS)}

OUTPUTS = {
    "missingness_manifest": PROOF / "missingness_manifest.json",
    "availability_taxonomy": PROOF / "availability_taxonomy.json",
    "ground_truth_frame": PROOF / "ground_truth_frame.json",
    "decision_curves": PROOF / "decision_curves.json",
}
ROLE_POLICY = PROOF / "role_view_policy.json"
RECEIPT = PROOF / "materialization_receipt.json"
SELECTION_CENSUS = PROOF / "selection_census.json"
SELECTION_RECEIPT = PROOF / "selection_freeze_receipt.json"

IMAGE_ID_RE = re.compile(r"^IMAGE_ID=(sha256:[0-9a-f]{64})$")
IMAGE_DIGEST_RE = re.compile(
    r"^IMAGE_REPO_DIGEST=([^\s@]+@sha256:[0-9a-f]{64})$"
)
HEX64_RE = re.compile(r"^[0-9a-f]{64}$")
INSTANCE_RE = re.compile(r"^[A-Za-z0-9_.-]+__[A-Za-z0-9_.-]+-[0-9]+$")
SCENARIO_SENTINEL_RE = re.compile(
    r"(Traceback|(?:^|[^A-Za-z])(?:[A-Za-z]*Error|[A-Za-z]*Exception)"
    r"(?:[^A-Za-z]|$)|TIMEOUT|timed out|TRUNCAT|Killed)",
    re.MULTILINE,
)


class EvidenceError(ValueError):
    """A source or derived artifact violates the preregistered contract."""


def _git(*args: str, input_bytes: bytes | None = None) -> bytes:
    result = subprocess.run(
        ["git", *args],
        cwd=ROOT,
        input=input_bytes,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        detail = result.stderr.decode("utf-8", errors="replace").strip()
        raise EvidenceError(f"git {' '.join(args)} failed: {detail}")
    return result.stdout


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _canonical_bytes(value: Any) -> bytes:
    try:
        text = json.dumps(
            value,
            allow_nan=False,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
    except (TypeError, ValueError) as exc:
        raise EvidenceError(f"value is not canonical JSON: {exc}") from exc
    return (text + "\n").encode("utf-8")


def _reject_constant(token: str) -> None:
    raise EvidenceError(f"non-finite JSON number is forbidden: {token}")


def _pairs_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise EvidenceError(f"duplicate JSON key is forbidden: {key!r}")
        value[key] = item
    return value


def strict_json_bytes(data: bytes, *, source: str) -> Any:
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise EvidenceError(f"{source}: JSON is not UTF-8") from exc
    try:
        return json.loads(
            text,
            object_pairs_hook=_pairs_object,
            parse_constant=_reject_constant,
        )
    except json.JSONDecodeError as exc:
        raise EvidenceError(f"{source}: malformed JSON: {exc}") from exc


def _require_object(value: Any, *, source: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise EvidenceError(f"{source}: expected a JSON object")
    return value


def _require_records(document: dict[str, Any], key: str, *, source: str) -> list[dict]:
    rows = document.get(key)
    if not isinstance(rows, list) or any(not isinstance(row, dict) for row in rows):
        raise EvidenceError(f"{source}#/{key}: expected an object array")
    return rows


def _require_exact_bool(row: dict[str, Any], key: str, *, source: str) -> bool:
    value = row.get(key)
    if type(value) is not bool:
        raise EvidenceError(f"{source}: {key} must be an exact JSON boolean")
    return value


def _require_string(value: Any, *, source: str, pattern: re.Pattern[str] | None = None) -> str:
    if not isinstance(value, str) or not value:
        raise EvidenceError(f"{source}: expected a nonempty string")
    if pattern is not None and pattern.fullmatch(value) is None:
        raise EvidenceError(f"{source}: malformed string {value!r}")
    return value


class SourceTracker:
    """Read only exact predecessor blobs and retain an independent source ledger."""

    def __init__(self, reference: str = PREDECESSOR) -> None:
        self.reference = reference
        self._bytes: dict[Path, bytes] = {}
        self._records: dict[Path, dict[str, Any]] = {}

    @staticmethod
    def _relative(path: str | Path) -> Path:
        relative = Path(path)
        if relative.is_absolute() or ".." in relative.parts or relative == Path("."):
            raise EvidenceError(f"source path is not repository-relative: {path}")
        return relative

    def read_bytes(self, path: str | Path) -> bytes:
        relative = self._relative(path)
        cached = self._bytes.get(relative)
        if cached is not None:
            return cached

        absolute = ROOT / relative
        try:
            metadata = absolute.lstat()
        except OSError as exc:
            raise EvidenceError(f"missing source artifact {relative}") from exc
        if not stat.S_ISREG(metadata.st_mode) or absolute.is_symlink():
            raise EvidenceError(f"source artifact is not a regular nonsymlink file: {relative}")

        listing = _git("ls-tree", self.reference, "--", relative.as_posix()).decode(
            "utf-8", errors="strict"
        )
        lines = [line for line in listing.splitlines() if line]
        if len(lines) != 1:
            raise EvidenceError(
                f"{relative}: expected exactly one blob at predecessor {self.reference}"
            )
        prefix, listed_path = lines[0].split("\t", 1)
        mode, object_type, oid = prefix.split(" ")
        if listed_path != relative.as_posix() or object_type != "blob":
            raise EvidenceError(f"{relative}: predecessor object is not the named blob")
        if mode not in {"100644", "100755"}:
            raise EvidenceError(f"{relative}: predecessor mode {mode} is not regular")

        head_listing = _git("ls-tree", "HEAD", "--", relative.as_posix()).decode(
            "utf-8", errors="strict"
        )
        if head_listing != listing:
            raise EvidenceError(f"{relative}: HEAD blob differs from merged iter239 predecessor")

        committed = _git("cat-file", "blob", oid)
        current = absolute.read_bytes()
        if current != committed:
            raise EvidenceError(f"{relative}: worktree bytes differ from the tracked blob")

        self._bytes[relative] = current
        self._records[relative] = {
            "byte_count": len(current),
            "git_blob_oid": oid,
            "git_mode": mode,
            "path": relative.as_posix(),
            "reference_commit": self.reference,
            "sha256_file_bytes": _sha256(current),
        }
        return current

    def read_json(self, path: str | Path) -> Any:
        relative = self._relative(path)
        return strict_json_bytes(self.read_bytes(relative), source=relative.as_posix())

    def record(self, path: str | Path) -> dict[str, Any]:
        relative = self._relative(path)
        self.read_bytes(relative)
        return dict(self._records[relative])

    def ledger(self) -> list[dict[str, Any]]:
        return [dict(self._records[path]) for path in sorted(self._records)]


def preflight() -> dict[str, Any]:
    if _git("rev-parse", f"{PREDECESSOR}^1").decode().strip() != PREDECESSOR_FIRST_PARENT:
        raise EvidenceError("merged iter239 first parent changed")
    if _git("rev-parse", f"{PREDECESSOR}^2").decode().strip() != PREDECESSOR_SECOND_PARENT:
        raise EvidenceError("merged iter239 second parent changed")
    merge_tree = _git("rev-parse", f"{PREDECESSOR}^{{tree}}").decode().strip()
    sealed_tree = _git("rev-parse", f"{PREDECESSOR_SECOND_PARENT}^{{tree}}").decode().strip()
    if merge_tree != sealed_tree:
        raise EvidenceError("merged iter239 tree does not equal its sealed second-parent tree")
    if _git("rev-parse", f"{AUTHORIZATION}^").decode().strip() != PREDECESSOR:
        raise EvidenceError("iter240 authorization is not the direct child of merged iter239")
    if _git("rev-parse", f"{ACTIVATION}^").decode().strip() != AUTHORIZATION:
        raise EvidenceError("iter240 activation is not the direct child of authorization")
    subprocess.run(
        ["git", "merge-base", "--is-ancestor", ACTIVATION, "HEAD"],
        cwd=ROOT,
        check=True,
        capture_output=True,
    )

    seal_document = strict_json_bytes(
        (ROOT / "mission/seal_registry.json").read_bytes(),
        source="mission/seal_registry.json",
    )
    records = _require_records(
        _require_object(seal_document, source="mission/seal_registry.json"),
        "records",
        source="mission/seal_registry.json",
    )
    matching = [row for row in records if row.get("seal_id") == HISTORICAL_SEAL]
    if len(matching) != 1 or matching[0].get("reference_commit") != HISTORICAL_REFERENCE:
        raise EvidenceError("historical experiment seal is absent or ambiguous")

    return {
        "activation_commit": ACTIVATION,
        "authorization_commit": AUTHORIZATION,
        "historical_experiment_reference": HISTORICAL_REFERENCE,
        "historical_seal_id": HISTORICAL_SEAL,
        "merge_parents": [PREDECESSOR_FIRST_PARENT, PREDECESSOR_SECOND_PARENT],
        "merge_tree": merge_tree,
        "predecessor_commit": PREDECESSOR,
        "source_policy": (
            "named regular tracked blobs; HEAD blob and worktree bytes equal the exact "
            "merged iter239 predecessor"
        ),
    }


def select_missing_candidates(document: dict[str, Any]) -> list[tuple[int, dict[str, Any]]]:
    """Return source-indexed rows using only the three preregistered predicates."""

    candidates = document["candidates"]
    selected: list[tuple[int, dict[str, Any]]] = []
    for index, row in enumerate(candidates):
        certified = row["certified_resolved"]
        gold_equivalent = row["gold_equivalent_after_terminal_lf_normalization"]
        complete = row["outcome_complete"]
        if type(certified) is not bool:
            raise EvidenceError("certified_resolved is not an exact boolean")
        if type(gold_equivalent) is not bool:
            raise EvidenceError(
                "gold_equivalent_after_terminal_lf_normalization is not an exact boolean"
            )
        if type(complete) is not bool:
            raise EvidenceError("outcome_complete is not an exact boolean")
        if certified is True and gold_equivalent is False and complete is False:
            selected.append((index, row))
    return selected


def _indexed_by_id(
    rows: list[dict], *, source: str
) -> tuple[dict[str, tuple[int, dict]], list[str]]:
    index: dict[str, tuple[int, dict]] = {}
    order: list[str] = []
    for position, row in enumerate(rows):
        instance_id = _require_string(
            row.get("instance_id"),
            source=f"{source}/{position}/instance_id",
            pattern=INSTANCE_RE,
        )
        if instance_id in index:
            raise EvidenceError(f"{source}: duplicate instance ID {instance_id}")
        index[instance_id] = (position, row)
        order.append(instance_id)
    return index, order


def _legacy_one_lf_sha(data: bytes, *, source: str) -> str:
    if not data.endswith(b"\n"):
        raise EvidenceError(f"{source}: legacy hash scope requires exactly one final LF removal")
    return _sha256(data[:-1])


def _artifact(
    tracker: SourceTracker,
    path: Path,
    *,
    legacy_one_lf: bool = False,
) -> dict[str, Any]:
    data = tracker.read_bytes(path)
    record = tracker.record(path)
    result = {
        "byte_count": record["byte_count"],
        "git_blob_oid": record["git_blob_oid"],
        "path": record["path"],
        "sha256_file_bytes": record["sha256_file_bytes"],
    }
    if legacy_one_lf:
        result["legacy_sha256_one_terminal_lf_removed"] = _legacy_one_lf_sha(
            data, source=path.as_posix()
        )
    return result


def _pointer(path: Path, pointer: str) -> dict[str, str]:
    return {"json_pointer": pointer, "path": path.as_posix()}


def _unique_manifest_row(
    document: dict[str, Any],
    key: str,
    instance_id: str,
    *,
    source: str,
) -> tuple[int, dict]:
    rows = _require_records(document, key, source=source)
    matches = [
        (index, row)
        for index, row in enumerate(rows)
        if row.get("instance_id") == instance_id
    ]
    if len(matches) != 1:
        raise EvidenceError(
            f"{source}#/{key}: expected one row for {instance_id}, got {len(matches)}"
        )
    return matches[0]


def _image_provenance(text: str, *, source: str) -> dict[str, str]:
    id_matches = [match.group(1) for line in text.splitlines() if (match := IMAGE_ID_RE.fullmatch(line))]
    digest_matches = [
        match.group(1)
        for line in text.splitlines()
        if (match := IMAGE_DIGEST_RE.fullmatch(line))
    ]
    raw_id_lines = [line for line in text.splitlines() if line.startswith("IMAGE_ID=")]
    raw_digest_lines = [
        line for line in text.splitlines() if line.startswith("IMAGE_REPO_DIGEST=")
    ]
    if not (
        len(id_matches)
        == len(digest_matches)
        == len(raw_id_lines)
        == len(raw_digest_lines)
        == 1
    ):
        raise EvidenceError(f"{source}: image identity is missing, duplicate, or malformed")
    return {"image_id": id_matches[0], "image_repository_digest": digest_matches[0]}


def _bounded_section(
    text: str, start: str, end: str, *, source: str
) -> list[str]:
    lines = text.splitlines()
    starts = [index for index, line in enumerate(lines) if line == start]
    ends = [index for index, line in enumerate(lines) if line == end]
    if len(starts) != 1 or len(ends) != 1 or starts[0] >= ends[0]:
        raise EvidenceError(f"{source}: expected one ordered {start!r}/{end!r} section")
    return lines[starts[0] + 1 : ends[0]]


def _evaluation_command(text: str, *, source: str) -> str:
    body = _bounded_section(
        text,
        ": '>>>>> Start Test Output'",
        ": '>>>>> End Test Output'",
        source=source,
    )
    commands = [line for line in body if line.strip()]
    if len(commands) != 1:
        raise EvidenceError(f"{source}: expected exactly one bounded evaluation command")
    return commands[0]


def _validate_certification_log(text: str, *, source: str) -> None:
    if text.splitlines().count("APPLY_OK variant") != 1:
        raise EvidenceError(f"{source}: candidate apply evidence is not unique and successful")
    body = _bounded_section(
        text,
        ">>>>> Cert Start",
        ">>>>> Cert End",
        source=source,
    )
    if body.count("CERT_EXIT=0") != 1:
        raise EvidenceError(f"{source}: certification did not retain exactly one zero exit")
    if any(
        token in "\n".join(body)
        for token in ("APPLY_FAILED", "SETUP_FAILED", "CERT_TIMEOUT", "CERT_TRUNCATED")
    ):
        raise EvidenceError(f"{source}: certification contains a failure sentinel")


def _scenario_arm(text: str, arm: str, *, source: str) -> dict[str, Any]:
    provenance = _image_provenance(text, source=source)
    apply_ok = text.splitlines().count(f"APPLY_OK {arm}") == 1
    try:
        body = _bounded_section(
            text,
            ">>>>> Scenario Start",
            ">>>>> Scenario End",
            source=source,
        )
    except EvidenceError:
        return {
            **provenance,
            "apply_ok": apply_ok,
            "exit_code": None,
            "result_count": 0,
            "valid": False,
        }
    result_lines = [line for line in body if line.startswith("RESULT=")]
    exit_lines = [line for line in body if re.fullmatch(r"SCENARIO_EXIT=-?[0-9]+", line)]
    exit_code = (
        int(exit_lines[0].split("=", 1)[1]) if len(exit_lines) == 1 else None
    )
    bounded_text = "\n".join(body)
    valid = (
        apply_ok
        and len(result_lines) == 1
        and len(result_lines[0]) > len("RESULT=")
        and exit_code == 0
        and SCENARIO_SENTINEL_RE.search(bounded_text) is None
    )
    return {
        **provenance,
        "apply_ok": apply_ok,
        "exit_code": exit_code,
        "result_count": len(result_lines),
        "valid": valid,
    }


def _row_consistency(
    row: dict[str, Any],
    *,
    instance_id: str,
    repo: str,
    source: str,
) -> None:
    if row.get("instance_id") != instance_id:
        raise EvidenceError(f"{source}: instance/repository identity mismatch")
    if "repo" in row and row.get("repo") != repo:
        raise EvidenceError(f"{source}: instance/repository identity mismatch")


def build_selection_census(
    tracker: SourceTracker,
    source_boundary: dict[str, Any],
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Build the outcome-blind census before any diagnostic source is opened."""

    selected_frozen: list[dict[str, Any]] = []
    source_paths: list[str] = []
    for run in FRESH_RUNS:
        candidate_path = (
            Path("experiments") / run / "proof/iter200_per_candidate.json"
        )
        source_paths.append(candidate_path.as_posix())
        document = _require_object(
            tracker.read_json(candidate_path), source=candidate_path.as_posix()
        )
        candidates = _require_records(
            document, "candidates", source=candidate_path.as_posix()
        )
        selected = select_missing_candidates({"candidates": candidates})
        for source_index, row in selected:
            instance_id = _require_string(
                row.get("instance_id"),
                source=f"{candidate_path}#/candidates/{source_index}/instance_id",
                pattern=INSTANCE_RE,
            )
            repo = _require_string(
                row.get("repo"),
                source=f"{candidate_path}#/candidates/{source_index}/repo",
            )
            selected_frozen.append(
                {
                    "candidate_pointer": _pointer(
                        candidate_path, f"/candidates/{source_index}"
                    ),
                    "instance_id": instance_id,
                    "repo": repo,
                    "source_index": source_index,
                    "source_run": run,
                }
            )

    keys = [(row["source_run"], row["instance_id"]) for row in selected_frozen]
    if len(keys) != 13 or len(keys) != len(set(keys)):
        raise EvidenceError(
            f"outcome-blind census returned {len(keys)} non-unique rows; expected 13"
        )
    if len({row["instance_id"] for row in selected_frozen}) != 13:
        raise EvidenceError("outcome-blind census does not contain thirteen unique tasks")

    census = {
        "claim_boundary": (
            "Outcome-blind source census only. No scenario, log, status, divergence, "
            "result, label, or judge evidence was read to select these rows."
        ),
        "immutable_source_boundary": source_boundary,
        "schema_version": "telos.iter240.selection_census.v1",
        "selected_count": len(selected_frozen),
        "selected_rows": selected_frozen,
        "selection_contract": {
            "allowed_predicates": [
                "certified_resolved is true",
                "gold_equivalent_after_terminal_lf_normalization is false",
                "outcome_complete is false",
            ],
            "forbidden_during_selection": [
                "status",
                "diverges",
                "gold_result",
                "model_result",
                "scenario output",
                "execution logs",
                "labels",
                "judge verdicts",
            ],
            "source_paths": source_paths,
            "typed_boolean_identity_required": True,
        },
        "unique_task_count": len({row["instance_id"] for row in selected_frozen}),
    }
    return census, selected_frozen


def _selection_receipt(
    census: dict[str, Any],
    tracker: SourceTracker,
) -> dict[str, Any]:
    census_bytes = _canonical_bytes(census)
    builder_bytes = (ROOT / "scripts/build_iter240_ground_truth_admission.py").read_bytes()
    return {
        "builder_path": "scripts/build_iter240_ground_truth_admission.py",
        "builder_sha256": _sha256(builder_bytes),
        "claim_boundary": (
            "This receipt freezes the outcome-blind 13-row census before diagnostic "
            "evidence is read. It assigns no outcome and authorizes no execution."
        ),
        "external_actions": {
            "gpu_allocations": 0,
            "model_or_provider_calls": 0,
            "scientific_containers": 0,
            "spend_usd": "0.00",
            "target_executions": 0,
        },
        "schema_version": "telos.iter240.selection_freeze_receipt.v1",
        "selection_census": {
            "byte_count": len(census_bytes),
            "path": SELECTION_CENSUS.as_posix(),
            "sha256_file_bytes": _sha256(census_bytes),
        },
        "source_count": len(tracker.ledger()),
        "source_inputs": tracker.ledger(),
        "source_reference_commit": PREDECESSOR,
    }


def _require_committed_selection_freeze(
    expected_census: dict[str, Any],
    expected_receipt: dict[str, Any],
) -> None:
    problems = _check_json(SELECTION_CENSUS, expected_census)
    problems.extend(_check_json(SELECTION_RECEIPT, expected_receipt))
    if problems:
        raise EvidenceError(
            "selection freeze does not rebuild: " + "; ".join(problems[:10])
        )
    for path in (SELECTION_CENSUS, SELECTION_RECEIPT):
        listing = _git("ls-tree", "HEAD", "--", path.as_posix()).decode("utf-8")
        lines = [line for line in listing.splitlines() if line]
        if len(lines) != 1:
            raise EvidenceError(
                f"{path}: selection freeze must be committed before diagnosis"
            )
        prefix, exact_path = lines[0].split("\t", 1)
        mode, kind, oid = prefix.split(" ")
        if exact_path != path.as_posix() or kind != "blob" or mode != "100644":
            raise EvidenceError(f"{path}: committed selection freeze is not a regular blob")
        if (ROOT / path).read_bytes() != _git("cat-file", "blob", oid):
            raise EvidenceError(f"{path}: worktree differs from committed selection freeze")


def build_missingness(
    tracker: SourceTracker,
    source_boundary: dict[str, Any],
    selected_frozen: list[dict[str, Any]],
) -> tuple[dict[str, Any], dict[str, Any], list[dict[str, Any]], dict[str, Any]]:
    snapshot_document = _require_object(
        tracker.read_json(SNAPSHOT), source=SNAPSHOT.as_posix()
    )
    snapshot_rows = _require_records(
        snapshot_document, "rows", source=SNAPSHOT.as_posix()
    )
    snapshot_by_id, _ = _indexed_by_id(
        snapshot_rows, source=f"{SNAPSHOT.as_posix()}#/rows"
    )

    run_documents: dict[str, dict[str, Any]] = {}
    for run in FRESH_RUNS:
        root = Path("experiments") / run / "proof"
        candidate_path = root / "iter200_per_candidate.json"
        # Re-read the already frozen selector source as a byte-bound input. No
        # selector decision is made in this post-freeze diagnostic phase.
        _require_object(
            tracker.read_json(candidate_path), source=candidate_path.as_posix()
        )

        audit_path = root / "audit_report.json"
        blind_path = root / "blind_judge_verdicts.json"
        solve_path = root / "raw/solutions/solve_summary.json"
        spec_index_path = root / "raw/specs/index.json"
        scenario_path = root / "raw/scenarios/scenarios_summary.json"
        run_documents[run] = {
            "audit": _require_object(
                tracker.read_json(audit_path), source=audit_path.as_posix()
            ),
            "audit_path": audit_path,
            "blind": _require_object(
                tracker.read_json(blind_path), source=blind_path.as_posix()
            ),
            "blind_path": blind_path,
            "scenario": _require_object(
                tracker.read_json(scenario_path), source=scenario_path.as_posix()
            ),
            "scenario_path": scenario_path,
            "solve": _require_object(
                tracker.read_json(solve_path), source=solve_path.as_posix()
            ),
            "solve_path": solve_path,
            "spec_index": _require_object(
                tracker.read_json(spec_index_path), source=spec_index_path.as_posix()
            ),
            "spec_index_path": spec_index_path,
        }

    if len(selected_frozen) != 13:
        raise EvidenceError(f"strict fresh selector returned {len(selected_frozen)}, expected 13")
    selected_keys = [
        (row["source_run"], row["instance_id"]) for row in selected_frozen
    ]
    if len(selected_keys) != len(set(selected_keys)):
        raise EvidenceError("strict fresh selector returned a duplicate run/task row")
    if len({row["instance_id"] for row in selected_frozen}) != 13:
        raise EvidenceError("fresh missing rows do not have thirteen distinct task identities")

    manifest_rows: list[dict[str, Any]] = []
    taxonomy_rows: list[dict[str, Any]] = []
    for frozen in selected_frozen:
        run = frozen["source_run"]
        instance_id = frozen["instance_id"]
        repo = frozen["repo"]
        root = Path("experiments") / run / "proof"
        documents = run_documents[run]

        solve_index, solve_row = _unique_manifest_row(
            documents["solve"],
            "manifest",
            instance_id,
            source=documents["solve_path"].as_posix(),
        )
        spec_index, spec_index_row = _unique_manifest_row(
            documents["spec_index"],
            "specs",
            instance_id,
            source=documents["spec_index_path"].as_posix(),
        )
        scenario_index, scenario_row = _unique_manifest_row(
            documents["scenario"],
            "manifest",
            instance_id,
            source=documents["scenario_path"].as_posix(),
        )
        snapshot_index, snapshot_row = snapshot_by_id[instance_id]
        for source, row in (
            ("solve summary", solve_row),
            ("spec index", spec_index_row),
            ("scenario summary", scenario_row),
            ("frozen snapshot", snapshot_row),
        ):
            _row_consistency(
                row,
                instance_id=instance_id,
                repo=repo,
                source=f"{run}/{instance_id}/{source}",
            )

        model_patch_path = root / f"raw/solutions/{instance_id}.model.patch"
        gold_patch_path = root / f"raw/solutions/{instance_id}.gold.patch"
        spec_path = root / f"raw/specs/{instance_id}.spec.json"
        eval_path = root / f"raw/specs/{instance_id}.eval_script.sh"
        candidate_log_path = root / f"raw/execution/{instance_id}.variant.log"
        gold_log_path = root / f"raw/execution/{instance_id}.gold.log"
        scenario_file_path = root / f"raw/scenarios/{instance_id}.scenario.py"

        model_bytes = tracker.read_bytes(model_patch_path)
        gold_bytes = tracker.read_bytes(gold_patch_path)
        spec = _require_object(
            tracker.read_json(spec_path), source=spec_path.as_posix()
        )
        eval_bytes = tracker.read_bytes(eval_path)
        candidate_log_bytes = tracker.read_bytes(candidate_log_path)
        gold_log_bytes = tracker.read_bytes(gold_log_path)
        candidate_text = candidate_log_bytes.decode("utf-8", errors="strict")
        gold_text = gold_log_bytes.decode("utf-8", errors="strict")

        expected_model_legacy = _legacy_one_lf_sha(
            model_bytes, source=model_patch_path.as_posix()
        )
        if solve_row.get("model_patch_sha256") != expected_model_legacy:
            raise EvidenceError(f"{run}/{instance_id}: model patch legacy hash mismatch")
        if spec.get("eval_script_sha256") != _sha256(eval_bytes):
            raise EvidenceError(f"{run}/{instance_id}: evaluation-script hash mismatch")
        if gold_bytes != snapshot_row.get("patch", "").encode("utf-8"):
            raise EvidenceError(f"{run}/{instance_id}: accepted patch differs from snapshot")

        base_commit = _require_string(
            solve_row.get("base_commit"),
            source=f"{run}/{instance_id}/base_commit",
        )
        if spec.get("base_commit") != base_commit or snapshot_row.get("base_commit") != base_commit:
            raise EvidenceError(f"{run}/{instance_id}: base commit mismatch")
        _row_consistency(
            spec,
            instance_id=instance_id,
            repo=repo,
            source=f"{run}/{instance_id}/spec",
        )
        _row_consistency(
            spec_index_row,
            instance_id=instance_id,
            repo=repo,
            source=f"{run}/{instance_id}/spec-index",
        )

        command = _evaluation_command(
            eval_bytes.decode("utf-8", errors="strict"), source=eval_path.as_posix()
        )
        _validate_certification_log(candidate_text, source=candidate_log_path.as_posix())
        candidate_image = _image_provenance(
            candidate_text, source=candidate_log_path.as_posix()
        )
        gold_image = _image_provenance(gold_text, source=gold_log_path.as_posix())
        if candidate_image != gold_image:
            raise EvidenceError(f"{run}/{instance_id}: arm image provenance differs")

        declared_alias = _require_string(
            spec.get("image"), source=f"{spec_path}#/image"
        )
        if not declared_alias.endswith(":latest"):
            raise EvidenceError(f"{run}/{instance_id}: expected disclosed mutable image alias")

        blind_rows = _require_records(
            documents["blind"], "verdicts", source=documents["blind_path"].as_posix()
        )
        blind_matches = [
            (index, row)
            for index, row in enumerate(blind_rows)
            if row.get("instance_id") == instance_id
        ]

        scenario_status = _require_string(
            scenario_row.get("status"),
            source=f"{documents['scenario_path']}#/manifest/{scenario_index}/status",
        )
        scenario_artifact: dict[str, Any] | None = None
        arm_summaries: dict[str, Any] = {}
        if scenario_status == "scenario":
            scenario_bytes = tracker.read_bytes(scenario_file_path)
            expected_scenario_hash = _legacy_one_lf_sha(
                scenario_bytes, source=scenario_file_path.as_posix()
            )
            if scenario_row.get("scenario_sha256") != expected_scenario_hash:
                raise EvidenceError(f"{run}/{instance_id}: scenario legacy hash mismatch")
            scenario_artifact = _artifact(
                tracker, scenario_file_path, legacy_one_lf=True
            )
            arm_summaries = {
                "candidate": _scenario_arm(
                    candidate_text, "variant", source=candidate_log_path.as_posix()
                ),
                "accepted": _scenario_arm(
                    gold_text, "gold", source=gold_log_path.as_posix()
                ),
            }
            candidate_valid = arm_summaries["candidate"]["valid"]
            gold_valid = arm_summaries["accepted"]["valid"]
            if candidate_valid and gold_valid:
                availability = (
                    "paired_valid_judged" if blind_matches else "paired_valid_unjudged"
                )
            elif not candidate_valid and not gold_valid:
                availability = "paired_invalid_both_arms"
            elif not candidate_valid and gold_valid:
                availability = "paired_invalid_candidate_only"
            else:
                availability = "source_inconsistent"
        elif scenario_status in {"excluded_unsafe", "no_scenario"}:
            if scenario_file_path.exists():
                raise EvidenceError(
                    f"{run}/{instance_id}: {scenario_status} unexpectedly retains executable scenario"
                )
            availability = scenario_status
            arm_summaries = {
                "candidate": {**candidate_image, "valid": False},
                "accepted": {**gold_image, "valid": False},
            }
        else:
            availability = "source_inconsistent"

        artifacts = {
            "accepted_patch": _artifact(tracker, gold_patch_path),
            "candidate_patch": _artifact(
                tracker, model_patch_path, legacy_one_lf=True
            ),
            "candidate_execution_log": _artifact(tracker, candidate_log_path),
            "evaluation_script": _artifact(tracker, eval_path),
            "gold_execution_log": _artifact(tracker, gold_log_path),
            "specification": _artifact(tracker, spec_path),
        }
        if scenario_artifact is not None:
            artifacts["historical_scenario"] = scenario_artifact

        manifest_rows.append(
            {
                "artifacts": artifacts,
                "base_commit": base_commit,
                "certification": {
                    "command": command,
                    "candidate_apply_ok": True,
                    "exit_code": 0,
                },
                "declared_mutable_image_alias": declared_alias,
                "immutable_arm_image": candidate_image,
                "instance_id": instance_id,
                "pointers": {
                    "candidate": frozen["candidate_pointer"],
                    "scenario_summary": _pointer(
                        documents["scenario_path"], f"/manifest/{scenario_index}"
                    ),
                    "snapshot": _pointer(SNAPSHOT, f"/rows/{snapshot_index}"),
                    "solve_summary": _pointer(
                        documents["solve_path"], f"/manifest/{solve_index}"
                    ),
                    "spec_index": _pointer(
                        documents["spec_index_path"], f"/specs/{spec_index}"
                    ),
                },
                "repo": repo,
                "source_run": run,
            }
        )
        taxonomy_rows.append(
            {
                "arm_summaries": arm_summaries,
                "availability_state": availability,
                "historical_outcome_exposed": True,
                "instance_id": instance_id,
                "retained_blind_verdict_count": len(blind_matches),
                "retained_blind_verdict_pointers": [
                    _pointer(documents["blind_path"], f"/verdicts/{index}")
                    for index, _ in blind_matches
                ],
                "scenario_pointer": _pointer(
                    documents["scenario_path"], f"/manifest/{scenario_index}"
                ),
                "source_run": run,
                "unsafe_reason": (
                    scenario_row.get("unsafe_reason")
                    if scenario_status == "excluded_unsafe"
                    else None
                ),
            }
        )

    taxonomy_counts = dict(
        sorted(Counter(row["availability_state"] for row in taxonomy_rows).items())
    )
    expected_taxonomy = {
        "excluded_unsafe": 7,
        "no_scenario": 1,
        "paired_invalid_both_arms": 3,
        "paired_invalid_candidate_only": 2,
    }
    if taxonomy_counts != expected_taxonomy:
        raise EvidenceError(
            f"availability taxonomy contradicts disclosed reconstruction: {taxonomy_counts}"
        )
    if any(row["retained_blind_verdict_count"] != 0 for row in taxonomy_rows):
        raise EvidenceError("a selected missing row unexpectedly has a retained blind verdict")

    correction = _require_object(
        tracker.read_json(ITER237_CORRECTION), source=ITER237_CORRECTION.as_posix()
    )
    t2 = correction.get("claims", {}).get("T2_fresh_cohort_concentration")
    if not isinstance(t2, dict) or t2.get("total") != {"N": 37, "k": 0, "u": 13}:
        raise EvidenceError("iter237 T2 predecessor no longer records k=0,N=37,u=13")

    manifest = {
        "claim_boundary": (
            "A source-bound census of thirteen fresh certified rows with missing outcomes. "
            "It assigns no semantic outcome and changes none of k=0, N=37, or u=13."
        ),
        "immutable_source_boundary": source_boundary,
        "schema_version": "telos.iter240.missingness_manifest.v1",
        "selected_count": len(manifest_rows),
        "selected_rows": manifest_rows,
        "selection_contract": {
            "allowed_predicates": [
                "certified_resolved is true",
                "gold_equivalent_after_terminal_lf_normalization is false",
                "outcome_complete is false",
            ],
            "forbidden_during_selection": [
                "status",
                "diverges",
                "gold_result",
                "model_result",
                "scenario output",
                "execution logs",
                "labels",
                "judge verdicts",
            ],
            "source_paths": [
                (
                    Path("experiments")
                    / run
                    / "proof/iter200_per_candidate.json"
                ).as_posix()
                for run in FRESH_RUNS
            ],
            "typed_boolean_identity_required": True,
        },
        "unique_task_count": len({row["instance_id"] for row in manifest_rows}),
    }
    taxonomy = {
        "availability_counts": taxonomy_counts,
        "claim_boundary": (
            "Retrospective diagnostic availability only. Historical scenarios were exposed "
            "before this gate and cannot serve as a future primary endpoint."
        ),
        "future_primary_endpoint_rows": 0,
        "paired_valid_rows": 0,
        "retained_evidence_recovery": "blocked",
        "rows": taxonomy_rows,
        "schema_version": "telos.iter240.availability_taxonomy.v1",
        "selected_count": len(taxonomy_rows),
    }
    acquisition_inputs = {"run_documents": run_documents}
    return manifest, taxonomy, selected_frozen, acquisition_inputs


def _find_candidate(
    document: dict[str, Any], instance_id: str, *, source: Path
) -> tuple[int, dict]:
    return _unique_manifest_row(
        document, "candidates", instance_id, source=source.as_posix()
    )


def _patch_evidence(
    tracker: SourceTracker,
    path: Path,
    *,
    expected_legacy: str | None = None,
) -> dict[str, Any]:
    artifact = _artifact(tracker, path, legacy_one_lf=True)
    legacy = artifact["legacy_sha256_one_terminal_lf_removed"]
    if expected_legacy is not None and legacy != expected_legacy:
        raise EvidenceError(f"{path}: recorded legacy patch digest mismatch")
    return artifact


def build_frame(
    tracker: SourceTracker,
    selected_frozen: list[dict[str, Any]],
) -> dict[str, Any]:
    per_documents: dict[str, tuple[Path, dict[str, Any]]] = {}
    blind_documents: dict[str, tuple[Path, dict[str, Any]]] = {}
    for run in NATURAL_RUNS:
        base = Path("experiments") / run / "proof"
        per_path = base / "iter200_per_candidate.json"
        blind_path = base / "blind_judge_verdicts.json"
        per_documents[run] = (
            per_path,
            _require_object(tracker.read_json(per_path), source=per_path.as_posix()),
        )
        blind_documents[run] = (
            blind_path,
            _require_object(tracker.read_json(blind_path), source=blind_path.as_posix()),
        )

    eval_document = _require_object(
        tracker.read_json(ITER230_EVAL), source=ITER230_EVAL.as_posix()
    )
    positives_eval = _require_records(
        eval_document, "positives", source=ITER230_EVAL.as_posix()
    )
    negatives_eval = _require_records(
        eval_document, "negatives", source=ITER230_EVAL.as_posix()
    )
    if (
        eval_document.get("positive_count") != 13
        or eval_document.get("negative_count") != 54
        or len(positives_eval) != 13
        or len(negatives_eval) != 54
    ):
        raise EvidenceError("iter230 evaluation-set accounting changed")

    original: dict[tuple[str, str], dict[str, Any]] = {}
    for run in NATURAL_RUNS:
        blind_path, blind_document = blind_documents[run]
        for blind_index, row in enumerate(
            _require_records(blind_document, "verdicts", source=blind_path.as_posix())
        ):
            flag = row.get("both_judges_flag_only_model")
            if type(flag) is not bool:
                raise EvidenceError(f"{blind_path}#/verdicts/{blind_index}: flag is not boolean")
            if flag is not True:
                continue
            for key in (
                "judge_outcome_complete",
                "gpt_flags_only_model",
                "opus_flags_only_model",
            ):
                if row.get(key) is not True:
                    raise EvidenceError(
                        f"{blind_path}#/verdicts/{blind_index}: positive lacks {key}=true"
                    )
            instance_id = _require_string(
                row.get("instance_id"),
                source=f"{blind_path}#/verdicts/{blind_index}/instance_id",
                pattern=INSTANCE_RE,
            )
            key = (run, instance_id)
            if key in original:
                raise EvidenceError(f"duplicate original positive {run}/{instance_id}")
            per_path, per_document = per_documents[run]
            candidate_index, candidate = _find_candidate(
                per_document, instance_id, source=per_path
            )
            expected = {
                "cert_command_ok": True,
                "certified_resolved": True,
                "diverges": True,
                "execution_complete": True,
                "gold_equivalent_after_terminal_lf_normalization": False,
                "outcome_complete": True,
                "scenario_available": True,
                "status": "candidate_natural_hack",
            }
            if any(candidate.get(field) != value for field, value in expected.items()):
                raise EvidenceError(f"{run}/{instance_id}: original positive inconsistency")
            patch_path = (
                Path("experiments")
                / run
                / f"proof/raw/solutions/{instance_id}.model.patch"
            )
            original[key] = {
                "candidate_pointer": _pointer(
                    per_path, f"/candidates/{candidate_index}"
                ),
                "instance_id": instance_id,
                "label_pointer": _pointer(
                    blind_path, f"/verdicts/{blind_index}"
                ),
                "label_provenance": "retained_two_judge_operational_differential",
                "patch": _patch_evidence(tracker, patch_path),
                "repo": candidate.get("repo"),
                "source_run": run,
            }
    if len(original) != 13:
        raise EvidenceError(f"blind evidence yields {len(original)} positives, expected 13")

    eval_positive_keys: set[tuple[str, str]] = set()
    for index, row in enumerate(positives_eval):
        run = row.get("run")
        instance_id = row.get("instance_id")
        key = (run, instance_id)
        if (
            run not in NATURAL_RUNS
            or not isinstance(instance_id, str)
            or row.get("label") != "certified_yet_wrong"
            or key in eval_positive_keys
        ):
            raise EvidenceError(f"{ITER230_EVAL}#/positives/{index}: malformed positive")
        eval_positive_keys.add(key)
        expected_path = (
            Path("experiments")
            / run
            / f"proof/raw/solutions/{instance_id}.model.patch"
        ).as_posix()
        if row.get("model_patch_path") != expected_path:
            raise EvidenceError(f"{ITER230_EVAL}#/positives/{index}: patch path mismatch")
        patch = original.get(key)
        if patch is None:
            raise EvidenceError(f"iter230 positive lacks blind-positive source {key}")
        legacy = patch["patch"]["legacy_sha256_one_terminal_lf_removed"]
        if row.get("model_patch_sha256") != legacy:
            raise EvidenceError(f"{ITER230_EVAL}#/positives/{index}: patch hash mismatch")
        patch["eval_set_pointer"] = _pointer(ITER230_EVAL, f"/positives/{index}")
    if eval_positive_keys != set(original):
        raise EvidenceError("iter230 positives do not exactly equal blind-derived positives")

    target_document = _require_object(
        tracker.read_json(ITER235_TARGETS), source=ITER235_TARGETS.as_posix()
    )
    witness_document = _require_object(
        tracker.read_json(ITER235_WITNESSES), source=ITER235_WITNESSES.as_posix()
    )
    judge_document = _require_object(
        tracker.read_json(ITER235_JUDGES), source=ITER235_JUDGES.as_posix()
    )
    if (
        target_document.get("selection_rule")
        != (
            "certified_resolved AND NOT "
            "gold_equivalent_after_terminal_lf_normalization AND NOT outcome_complete"
        )
        or target_document.get("count") != 41
        or target_document.get("certified_total") != 125
    ):
        raise EvidenceError("iter235 target contract changed")
    if judge_document.get("confirmation_rule") != "both_valid_judges_name_only_model_slot":
        raise EvidenceError("iter235 confirmation rule changed")

    target_rows = _require_records(
        target_document, "targets", source=ITER235_TARGETS.as_posix()
    )
    witness_rows = _require_records(
        witness_document, "manifest", source=ITER235_WITNESSES.as_posix()
    )
    judge_rows = _require_records(
        judge_document, "verdicts", source=ITER235_JUDGES.as_posix()
    )
    recovered: dict[tuple[str, str], dict[str, Any]] = {}
    for judge_index, judge in enumerate(judge_rows):
        confirmed = judge.get("confirmed")
        if type(confirmed) is not bool:
            raise EvidenceError(f"{ITER235_JUDGES}#/verdicts/{judge_index}: nonboolean")
        if confirmed is not True:
            continue
        run = judge.get("run")
        instance_id = judge.get("instance_id")
        key = (run, instance_id)
        if run not in NATURAL_RUNS or not isinstance(instance_id, str) or key in recovered:
            raise EvidenceError(f"malformed recovered-positive identity {key}")
        target_matches = [
            (index, row)
            for index, row in enumerate(target_rows)
            if (row.get("run"), row.get("instance_id")) == key
        ]
        witness_matches = [
            (index, row)
            for index, row in enumerate(witness_rows)
            if (row.get("run"), row.get("instance_id")) == key
        ]
        if len(target_matches) != 1 or len(witness_matches) != 1:
            raise EvidenceError(f"{run}/{instance_id}: recovery source is missing or duplicate")
        target_index, target = target_matches[0]
        witness_index, witness = witness_matches[0]
        if witness.get("status") != "witness":
            raise EvidenceError(f"{run}/{instance_id}: confirmed recovery lacks witness")

        per_path, per_document = per_documents[run]
        candidate_index, candidate = _find_candidate(
            per_document, instance_id, source=per_path
        )
        expected = {
            "cert_command_ok": True,
            "certified_resolved": True,
            "execution_complete": True,
            "gold_equivalent_after_terminal_lf_normalization": False,
            "outcome_complete": False,
            "scenario_available": True,
            "status": "certified_unadjudicated",
        }
        if any(candidate.get(field) != value for field, value in expected.items()):
            raise EvidenceError(f"{run}/{instance_id}: recovery input inconsistency")

        patch_path = (
            Path("experiments")
            / run
            / f"proof/raw/solutions/{instance_id}.model.patch"
        )
        stem = f"{run}__{instance_id}.witness"
        witness_path = (
            Path("experiments/iter235_witness_recovery/proof/raw/witnesses")
            / f"{stem}.py"
        )
        execution_path = (
            Path("experiments/iter235_witness_recovery/proof/raw/execution")
            / f"{stem}.log"
        )
        witness_artifact = _artifact(tracker, witness_path, legacy_one_lf=True)
        if (
            witness.get("witness_sha256")
            != witness_artifact["legacy_sha256_one_terminal_lf_removed"]
        ):
            raise EvidenceError(f"{run}/{instance_id}: witness legacy hash mismatch")
        execution_text = tracker.read_bytes(execution_path).decode("utf-8", errors="strict")
        for arm in ("candidate", "gold"):
            body = _bounded_section(
                execution_text,
                f">>>>> {arm} Start",
                f">>>>> {arm} End",
                source=execution_path.as_posix(),
            )
            if (
                execution_text.splitlines().count(f"APPLY_OK {arm}") != 1
                or body.count(f"EXIT {arm}=0") != 1
                or len([line for line in body if line.startswith("RESULT=")]) != 1
            ):
                raise EvidenceError(f"{run}/{instance_id}: invalid recovery execution")
        model_slot = judge.get("model_slot")
        if model_slot not in {"A", "B"}:
            raise EvidenceError(f"{run}/{instance_id}: invalid model slot")
        if judge.get("openai_verdict") != model_slot or judge.get(
            "anthropic_verdict"
        ) != model_slot:
            raise EvidenceError(f"{run}/{instance_id}: confirmation rule not satisfied")

        recovered[key] = {
            "candidate_pointer": _pointer(
                per_path, f"/candidates/{candidate_index}"
            ),
            "instance_id": instance_id,
            "label_pointer": _pointer(
                ITER235_JUDGES, f"/verdicts/{judge_index}"
            ),
            "label_provenance": "iter235_recovered_two_judge_operational_differential",
            "patch": _patch_evidence(tracker, patch_path),
            "recovery_execution": _artifact(tracker, execution_path),
            "recovery_target_pointer": _pointer(
                ITER235_TARGETS, f"/targets/{target_index}"
            ),
            "recovery_witness": witness_artifact,
            "recovery_witness_pointer": _pointer(
                ITER235_WITNESSES, f"/manifest/{witness_index}"
            ),
            "repo": candidate.get("repo"),
            "source_run": run,
        }
    if len(recovered) != 4 or set(recovered) & set(original):
        raise EvidenceError("iter235 must add exactly four nonduplicate positives")

    operational_positives = {**original, **recovered}
    if len(operational_positives) != 17:
        raise EvidenceError("current operational-positive set is not seventeen patches")

    hard_controls: dict[tuple[str, str], dict[str, Any]] = {}
    for index, row in enumerate(negatives_eval):
        if row.get("reason") != "certified_no_observed_divergence":
            continue
        if row.get("label") != "certified_correct":
            raise EvidenceError(f"{ITER230_EVAL}#/negatives/{index}: hard-control label drift")
        run = row.get("run")
        instance_id = row.get("instance_id")
        key = (run, instance_id)
        if run not in NATURAL_RUNS or not isinstance(instance_id, str) or key in hard_controls:
            raise EvidenceError(f"{ITER230_EVAL}#/negatives/{index}: malformed hard control")
        per_path, per_document = per_documents[run]
        candidate_index, candidate = _find_candidate(
            per_document, instance_id, source=per_path
        )
        expected = {
            "cert_command_ok": True,
            "certified_resolved": True,
            "diverges": False,
            "execution_complete": True,
            "gold_equivalent_after_terminal_lf_normalization": False,
            "outcome_complete": True,
            "scenario_available": True,
            "status": "certified_no_observed_divergence",
        }
        if any(candidate.get(field) != value for field, value in expected.items()):
            raise EvidenceError(f"{run}/{instance_id}: hard-control source inconsistency")
        patch_path = (
            Path("experiments")
            / run
            / f"proof/raw/solutions/{instance_id}.model.patch"
        )
        expected_path = patch_path.as_posix()
        if row.get("model_patch_path") != expected_path:
            raise EvidenceError(f"{ITER230_EVAL}#/negatives/{index}: patch path mismatch")
        patch = _patch_evidence(
            tracker, patch_path, expected_legacy=row.get("model_patch_sha256")
        )
        hard_controls[key] = {
            "candidate_pointer": _pointer(
                per_path, f"/candidates/{candidate_index}"
            ),
            "instance_id": instance_id,
            "label_pointer": _pointer(ITER230_EVAL, f"/negatives/{index}"),
            "label_provenance": "one_retained_witness_no_observed_divergence",
            "patch": patch,
            "repo": candidate.get("repo"),
            "source_run": run,
        }
    if len(hard_controls) != 25:
        raise EvidenceError(f"hard-control frame has {len(hard_controls)} rows, expected 25")

    frame_rows: list[dict[str, Any]] = []

    def append_row(stratum: str, record: dict[str, Any], *, missing: bool) -> None:
        patch_sha = record["patch"]["sha256_file_bytes"]
        identity = [
            "telos.iter240.frame-row.v1",
            stratum,
            record["source_run"],
            record["instance_id"],
            patch_sha,
        ]
        frame_rows.append(
            {
                **record,
                "candidate_row_id": _sha256(
                    json.dumps(identity, separators=(",", ":")).encode("utf-8")
                ),
                "independent_semantic_label": None,
                "missing_outcome": missing,
                "operational_stratum": stratum,
                "task_id": record["instance_id"],
            }
        )

    for record in operational_positives.values():
        append_row("operational_positive", record, missing=False)
    for record in hard_controls.values():
        append_row("hard_control", record, missing=False)
    manifest_by_key = {
        (row["source_run"], row["instance_id"]): row for row in selected_frozen
    }
    for key, selected in manifest_by_key.items():
        run, instance_id = key
        patch_path = (
            Path("experiments")
            / run
            / f"proof/raw/solutions/{instance_id}.model.patch"
        )
        append_row(
            "fresh_missing",
            {
                "candidate_pointer": selected["candidate_pointer"],
                "instance_id": instance_id,
                "label_pointer": None,
                "label_provenance": "missing_no_semantic_assignment",
                "patch": _patch_evidence(tracker, patch_path),
                "repo": selected["repo"],
                "source_run": run,
            },
            missing=True,
        )

    stratum_rank = {
        "operational_positive": 0,
        "hard_control": 1,
        "fresh_missing": 2,
    }
    frame_rows.sort(
        key=lambda row: (
            stratum_rank[row["operational_stratum"]],
            row["task_id"],
            RUN_ORDER[row["source_run"]],
            row["patch"]["sha256_file_bytes"],
        )
    )
    task_strata: dict[str, set[str]] = defaultdict(set)
    for row in frame_rows:
        task_strata[row["task_id"]].add(row["operational_stratum"])
    for row in frame_rows:
        strata = sorted(task_strata[row["task_id"]], key=stratum_rank.get)
        row["task_strata"] = strata
        row["cross_stratum_overlap"] = len(strata) > 1

    counts = Counter(row["operational_stratum"] for row in frame_rows)
    unique_by_stratum = {
        stratum: len(
            {
                row["task_id"]
                for row in frame_rows
                if row["operational_stratum"] == stratum
            }
        )
        for stratum in stratum_rank
    }
    overlaps = sorted(task for task, strata in task_strata.items() if len(strata) > 1)
    if (
        dict(counts)
        != {
            "operational_positive": 17,
            "hard_control": 25,
            "fresh_missing": 13,
        }
        or unique_by_stratum
        != {
            "operational_positive": 12,
            "hard_control": 14,
            "fresh_missing": 13,
        }
        or len(frame_rows) != 55
        or len(task_strata) != 37
        or overlaps != ["django__django-11964", "pydata__xarray-7233"]
    ):
        raise EvidenceError("task-clustered frame contradicts the registered census")

    return {
        "candidate_row_count": len(frame_rows),
        "claim_boundary": (
            "An acquisition inventory of operational labels and missing rows. "
            "No row carries independent semantic ground truth."
        ),
        "cross_stratum_task_overlap": overlaps,
        "independent_semantic_label_count": 0,
        "inferential_unit": "unique_task_identity",
        "rows": frame_rows,
        "schema_version": "telos.iter240.ground_truth_frame.v1",
        "strata": {
            stratum: {
                "candidate_rows": counts[stratum],
                "unique_tasks": unique_by_stratum[stratum],
            }
            for stratum in stratum_rank
        },
        "unique_task_count": len(task_strata),
    }


def _fisher_lower_tail(x: int) -> Fraction:
    total_events = x + 5
    lower = max(0, total_events - 29)
    numerator = sum(
        math.comb(37, i) * math.comb(29, total_events - i)
        for i in range(lower, x + 1)
    )
    return Fraction(numerator, math.comb(66, total_events))


def _decimal_string(value: Decimal, places: int = 18) -> str:
    quantum = Decimal(1).scaleb(-places)
    return format(value.quantize(quantum, rounding=ROUND_HALF_EVEN), f".{places}f")


def _zero_event_bound(n: int) -> Decimal:
    if type(n) is not int or n <= 0:
        raise EvidenceError("zero-event n must be a positive nonboolean integer")
    with localcontext() as context:
        context.prec = 80
        return Decimal(1) - (Decimal("0.05").ln() / Decimal(n)).exp()


def build_decision_curves(
    tracker: SourceTracker,
    acquisition_inputs: dict[str, Any],
) -> dict[str, Any]:
    correction = _require_object(
        tracker.read_json(ITER237_CORRECTION), source=ITER237_CORRECTION.as_posix()
    )
    t2 = correction["claims"]["T2_fresh_cohort_concentration"]
    if t2["total"] != {"N": 37, "k": 0, "u": 13}:
        raise EvidenceError("iter237 missingness anchor changed")

    missingness_branches: list[dict[str, Any]] = []
    for x in range(14):
        probability = _fisher_lower_tail(x)
        missingness_branches.append(
            {
                "exploratory_fisher": {
                    "alternative": "fresh_less_than_reused",
                    "decimal_display": format(
                        Decimal(probability.numerator) / Decimal(probability.denominator),
                        ".17g",
                    ),
                    "denominator": probability.denominator,
                    "numerator": probability.numerator,
                    "table": [[x, 37 - x], [5, 24]],
                },
                "fresh_operational_positive_count": x,
                "fresh_rate": {"denominator": 37, "numerator": x},
                "registered_strict_concentration_holds": 29 * x < 185,
                "reused_reference_rate": {"denominator": 29, "numerator": 5},
            }
        )

    zero_event_grid = [
        {
            "n_unique_tasks": n,
            "one_sided_95_percent_upper_bound": _decimal_string(
                _zero_event_bound(n)
            ),
        }
        for n in range(1, 501)
    ]
    thresholds = ("0.10", "0.05", "0.02", "0.01")
    threshold_rows = []
    with localcontext() as context:
        context.prec = 80
        for threshold_text in thresholds:
            threshold = Decimal(threshold_text)
            qualifying = next(
                n
                for n in range(1, 501)
                if (Decimal(1) - threshold) ** n <= Decimal("0.05")
            )
            threshold_rows.append(
                {
                    "first_n_at_or_below": qualifying,
                    "threshold": threshold_text,
                    "upper_bound_at_n": _decimal_string(
                        _zero_event_bound(qualifying)
                    ),
                    "upper_bound_at_n_minus_one": _decimal_string(
                        _zero_event_bound(qualifying - 1)
                    ),
                }
            )

    run_documents = acquisition_inputs["run_documents"]
    total_attempts = 0
    total_solutions = 0
    total_certified = 0
    yield_sources: list[dict[str, Any]] = []
    for run in FRESH_RUNS:
        documents = run_documents[run]
        solve = documents["solve"]
        candidate_path = (
            Path("experiments") / run / "proof/iter200_per_candidate.json"
        )
        candidates = _require_records(
            _require_object(
                tracker.read_json(candidate_path), source=candidate_path.as_posix()
            ),
            "candidates",
            source=candidate_path.as_posix(),
        )
        attempts = solve.get("targets")
        solutions = solve.get("solutions")
        certified = sum(
            1
            for index, row in enumerate(candidates)
            if _require_exact_bool(
                row,
                "certified_resolved",
                source=f"{candidate_path}#/candidates/{index}",
            )
        )
        if type(attempts) is not int or type(solutions) is not int:
            raise EvidenceError(f"{run}: solve accounting is not integer")
        total_attempts += attempts
        total_solutions += solutions
        total_certified += certified
        yield_sources.append(
            {
                "certified": certified,
                "pointers": {
                    "candidate_table": _pointer(candidate_path, "/candidates"),
                    "solve_attempts": _pointer(documents["solve_path"], "/targets"),
                    "solution_patches": _pointer(documents["solve_path"], "/solutions"),
                },
                "solve_attempts": attempts,
                "solution_patches": solutions,
                "source_run": run,
            }
        )
    if (total_certified, total_attempts, total_solutions) != (37, 64, 62):
        raise EvidenceError(
            "fresh acquisition accounting must be 37 certified / 64 attempts / 62 solutions"
        )

    yield_grid = (
        (2, 5),
        (1, 2),
        (37, 64),
        (3, 5),
        (2, 3),
        (3, 4),
        (4, 5),
    )
    targets = (29, 59, 149, 299)
    acquisition_rows = []
    for numerator, denominator in yield_grid:
        acquisition_rows.append(
            {
                "certification_yield": {
                    "denominator": denominator,
                    "numerator": numerator,
                },
                "historical_fresh_input": (numerator, denominator) == (37, 64),
                "targets": [
                    {
                        "required_solve_attempts": (
                            target * denominator + numerator - 1
                        )
                        // numerator,
                        "target_unique_certified_tasks": target,
                    }
                    for target in targets
                ],
            }
        )

    return {
        "acquisition_sensitivity": {
            "authority": "planning_only_not_purchase_authority",
            "conditional_solution_patch_diagnostic": {
                "certified": 37,
                "denominator": 62,
                "forbidden_as_acquisition_input": True,
                "interpretation": "conditional on a solution-producing patch",
            },
            "historical_certification_yield": {
                "certified": total_certified,
                "denominator": total_attempts,
                "interpretation": "certified patches per purchased solve attempt",
                "sources": yield_sources,
            },
            "rows": acquisition_rows,
        },
        "assurance_delta_readiness": {
            "missing_measured_inputs": [
                "supported_label_yield",
                "consequence_validity",
                "adjudication_completion",
                "within_task_discordance",
                "control_false_rejection_behavior",
            ],
            "paired_detector_power": "blocked",
            "selected_or_optimized_branch": None,
        },
        "claim_boundary": (
            "Complete sensitivity grids for design only. Cohorts are nonrandom operational "
            "samples; no p-value, branch, bound, or solve count authorizes inference or spend."
        ),
        "missingness_branches": missingness_branches,
        "schema_version": "telos.iter240.decision_curves.v1",
        "zero_event_upper_bounds": {
            "confidence": "one_sided_95_percent",
            "formula": "1 - 0.05 ** (1 / n)",
            "grid": zero_event_grid,
            "numeric_contract": (
                "Decimal natural-log/exponential at precision 80; canonical 18-place "
                "half-even display; validators compare by tolerance or exact rational "
                "threshold inequality, never binary-float identity"
            ),
            "threshold_crossings": threshold_rows,
        },
    }


def build_all() -> tuple[dict[str, dict[str, Any]], SourceTracker]:
    source_boundary = preflight()
    selection_tracker = SourceTracker()
    census, selected = build_selection_census(selection_tracker, source_boundary)
    selection_receipt = _selection_receipt(census, selection_tracker)
    _require_committed_selection_freeze(census, selection_receipt)
    tracker = SourceTracker()
    manifest, taxonomy, _, acquisition_inputs = build_missingness(
        tracker, source_boundary, selected
    )
    frame = build_frame(tracker, selected)
    curves = build_decision_curves(tracker, acquisition_inputs)
    return {
        "missingness_manifest": manifest,
        "availability_taxonomy": taxonomy,
        "ground_truth_frame": frame,
        "decision_curves": curves,
    }, tracker


def _expected_receipt(
    outputs: dict[str, dict[str, Any]],
    tracker: SourceTracker,
) -> dict[str, Any]:
    if not (ROOT / ROLE_POLICY).is_file():
        raise EvidenceError(f"required role policy is missing: {ROLE_POLICY}")
    role_bytes = (ROOT / ROLE_POLICY).read_bytes()
    strict_json_bytes(role_bytes, source=ROLE_POLICY.as_posix())
    output_records = []
    for name, relative in OUTPUTS.items():
        data = _canonical_bytes(outputs[name])
        output_records.append(
            {
                "byte_count": len(data),
                "path": relative.as_posix(),
                "sha256_file_bytes": _sha256(data),
            }
        )
    output_records.append(
        {
            "byte_count": len(role_bytes),
            "path": ROLE_POLICY.as_posix(),
            "sha256_file_bytes": _sha256(role_bytes),
        }
    )
    output_records.sort(key=lambda row: row["path"])
    return {
        "claim_boundary": (
            "Byte materialization receipt for offline design evidence. It is neither "
            "scientific ground truth nor acquisition, execution, publication, or spend authority."
        ),
        "external_actions": {
            "cohort_acquisitions": 0,
            "gpu_allocations": 0,
            "human_contacts": 0,
            "model_judgment_calls": 0,
            "provider_calls": 0,
            "scientific_containers": 0,
            "spend_usd": "0.00",
            "target_executions": 0,
        },
        "outputs": output_records,
        "result_status": {
            "cohort_acquisition": "not_authorized",
            "design_preflight": "supported",
            "independent_ground_truth": "blocked",
            "retained_evidence_recovery": "blocked",
        },
        "schema_version": "telos.iter240.materialization_receipt.v1",
        "source_count": len(tracker.ledger()),
        "source_inputs": tracker.ledger(),
        "source_reference_commit": PREDECESSOR,
    }


def _write(path: Path, value: Any) -> None:
    absolute = ROOT / path
    absolute.parent.mkdir(parents=True, exist_ok=True)
    absolute.write_bytes(_canonical_bytes(value))


def _check_json(path: Path, expected: Any) -> list[str]:
    absolute = ROOT / path
    if not absolute.is_file():
        return [f"{path}: missing"]
    actual = strict_json_bytes(absolute.read_bytes(), source=path.as_posix())
    return compare_json(actual, expected, path=path.as_posix())


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write-selection", action="store_true")
    mode.add_argument("--check-selection", action="store_true")
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--check", action="store_true")
    args = parser.parse_args()

    try:
        if args.write_selection or args.check_selection:
            source_boundary = preflight()
            selection_tracker = SourceTracker()
            census, _ = build_selection_census(selection_tracker, source_boundary)
            selection_receipt = _selection_receipt(census, selection_tracker)
            if args.write_selection:
                _write(SELECTION_CENSUS, census)
                _write(SELECTION_RECEIPT, selection_receipt)
                print(
                    "iter240 ground-truth admission: froze outcome-blind "
                    f"13-row census from {len(selection_tracker.ledger())} sources"
                )
                return 0
            problems = _check_json(SELECTION_CENSUS, census)
            problems.extend(_check_json(SELECTION_RECEIPT, selection_receipt))
            if problems:
                print("iter240 selection freeze: committed artifacts do not rebuild")
                for problem in problems[:50]:
                    print(f"  {problem}")
                return 1
            print(
                "iter240 selection freeze: exact 13-row census rebuilds "
                f"from {len(selection_tracker.ledger())} outcome-blind sources"
            )
            return 0

        outputs, tracker = build_all()
        receipt = _expected_receipt(outputs, tracker)
        if args.write:
            for name, path in OUTPUTS.items():
                _write(path, outputs[name])
            _write(RECEIPT, receipt)
            print(
                "iter240 ground-truth admission: wrote "
                f"{len(outputs) + 1} evidence artifacts from {len(tracker.ledger())} sources"
            )
            return 0

        problems: list[str] = []
        for name, path in OUTPUTS.items():
            problems.extend(_check_json(path, outputs[name]))
        problems.extend(_check_json(RECEIPT, receipt))
        if problems:
            print("iter240 ground-truth admission: committed artifacts do not rebuild")
            for problem in problems[:50]:
                print(f"  {problem}")
            return 1
        print(
            "iter240 ground-truth admission: exact rebuild matches "
            f"5 artifacts from {len(tracker.ledger())} predecessor sources"
        )
        return 0
    except (EvidenceError, OSError, UnicodeError, subprocess.CalledProcessError) as exc:
        print(f"iter240 ground-truth admission: FAIL: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
