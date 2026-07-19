#!/usr/bin/env python3
"""Independently validate iter240's offline ground-truth admission evidence.

The validator intentionally does not import the iter240 builder.  It rebuilds
the selector census, availability states, frame membership, exact Fisher
fractions, zero-event thresholds, acquisition arithmetic, Git source ledger,
and materialization digests through separate code paths.
"""

from __future__ import annotations

import ast
from collections import Counter
from decimal import Decimal, localcontext
from fractions import Fraction
import hashlib
import json
import math
from pathlib import Path
import re
import stat
import subprocess
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
ITERATION = Path("experiments/iter240_ground_truth_admission_design")
PROOF = ITERATION / "proof"
PREDECESSOR = "b597b763f2eb52b2f4f2d36e7daaa31654be076b"
AUTHORIZATION = "cf809ac0e06f37127553e99a2ab9b0705f8e2fae"
ACTIVATION = "63f5786b9b5c60d2bea90f2077208cfb745c31a2"
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
MANIFEST = PROOF / "missingness_manifest.json"
TAXONOMY = PROOF / "availability_taxonomy.json"
FRAME = PROOF / "ground_truth_frame.json"
CURVES = PROOF / "decision_curves.json"
ROLE_POLICY = PROOF / "role_view_policy.json"
RECEIPT = PROOF / "materialization_receipt.json"
SELECTION_CENSUS = PROOF / "selection_census.json"
SELECTION_RECEIPT = PROOF / "selection_freeze_receipt.json"
BUILDER = Path("scripts/build_iter240_ground_truth_admission.py")
RESULT = ITERATION / "RESULT.md"

OUTPUTS = (MANIFEST, TAXONOMY, FRAME, CURVES, ROLE_POLICY)
HEX40 = re.compile(r"^[0-9a-f]{40}$")
HEX64 = re.compile(r"^[0-9a-f]{64}$")
IMAGE_ID = re.compile(r"^IMAGE_ID=(sha256:[0-9a-f]{64})$")
IMAGE_DIGEST = re.compile(
    r"^IMAGE_REPO_DIGEST=([^\s@]+@sha256:[0-9a-f]{64})$"
)
ERROR_SENTINEL = re.compile(
    r"(Traceback|(?:^|[^A-Za-z])(?:[A-Za-z]*Error|[A-Za-z]*Exception)"
    r"(?:[^A-Za-z]|$)|TIMEOUT|timed out|TRUNCAT|Killed)",
    re.MULTILINE,
)


class ValidationError(ValueError):
    """One iter240 acceptance condition failed."""


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _duplicate_guard(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValidationError(f"duplicate JSON key: {key!r}")
        result[key] = value
    return result


def _bad_constant(value: str) -> None:
    raise ValidationError(f"non-finite JSON number: {value}")


def parse_json(data: bytes, *, source: str, canonical: bool = False) -> Any:
    try:
        text = data.decode("utf-8")
        value = json.loads(
            text,
            object_pairs_hook=_duplicate_guard,
            parse_constant=_bad_constant,
        )
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise ValidationError(f"{source}: invalid strict JSON: {exc}") from exc
    if canonical:
        expected = (
            json.dumps(
                value,
                allow_nan=False,
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            )
            + "\n"
        ).encode("utf-8")
        if data != expected:
            raise ValidationError(f"{source}: JSON is not in canonical representation")
    return value


def load_json(path: Path, *, canonical: bool = False) -> Any:
    absolute = ROOT / path
    try:
        metadata = absolute.lstat()
    except OSError as exc:
        raise ValidationError(f"{path}: missing") from exc
    if not stat.S_ISREG(metadata.st_mode) or absolute.is_symlink():
        raise ValidationError(f"{path}: expected a regular nonsymlink file")
    return parse_json(absolute.read_bytes(), source=path.as_posix(), canonical=canonical)


def _object(value: Any, source: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValidationError(f"{source}: expected object")
    return value


def _rows(document: dict[str, Any], key: str, source: str) -> list[dict]:
    value = document.get(key)
    if not isinstance(value, list) or any(not isinstance(row, dict) for row in value):
        raise ValidationError(f"{source}#/{key}: expected object array")
    return value


def _git(*arguments: str) -> bytes:
    result = subprocess.run(
        ["git", *arguments],
        cwd=ROOT,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        raise ValidationError(
            f"git {' '.join(arguments)} failed: "
            + result.stderr.decode("utf-8", errors="replace").strip()
        )
    return result.stdout


def validate_selector_source(source: str) -> list[str]:
    """Require the builder selector to be structurally outcome-blind."""

    try:
        tree = ast.parse(source)
    except SyntaxError as exc:
        return [f"builder is not parseable: {exc.msg}"]
    functions = [
        node
        for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name == "select_missing_candidates"
    ]
    if len(functions) != 1:
        return ["expected exactly one select_missing_candidates function"]
    function = functions[0]
    literals = {
        node.value
        for node in ast.walk(function)
        if isinstance(node, ast.Constant) and isinstance(node.value, str)
    }
    forbidden = {
        "status",
        "diverges",
        "gold_result",
        "model_result",
        "scenario_available",
        "scenario",
        "execution",
        "log",
        "label",
        "judge",
        "verdict",
    }
    problems = []
    contaminated = sorted(
        literal
        for literal in literals
        if any(token in literal.casefold() for token in forbidden)
        and literal
        not in {
            "outcome_complete",
            "outcome_complete is not an exact boolean",
        }
    )
    if contaminated:
        problems.append(
            "selector contains forbidden field/evidence literal(s): "
            + ", ".join(repr(item) for item in contaminated)
        )
    required = {
        "candidates",
        "certified_resolved",
        "gold_equivalent_after_terminal_lf_normalization",
        "outcome_complete",
    }
    missing = sorted(required - literals)
    if missing:
        problems.append("selector lacks exact required literals: " + ", ".join(missing))
    if any(
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr in {"get", "setdefault", "pop"}
        for node in ast.walk(function)
    ):
        problems.append("selector uses permissive mapping access")
    return problems


def select_independently(candidates: Any, *, source: str) -> list[tuple[int, dict]]:
    if not isinstance(candidates, list) or any(not isinstance(row, dict) for row in candidates):
        raise ValidationError(f"{source}: candidate array malformed")
    selected = []
    for index, row in enumerate(candidates):
        values = []
        for field in (
            "certified_resolved",
            "gold_equivalent_after_terminal_lf_normalization",
            "outcome_complete",
        ):
            value = row.get(field)
            if type(value) is not bool:
                raise ValidationError(f"{source}/{index}/{field}: exact boolean required")
            values.append(value)
        if values == [True, False, False]:
            selected.append((index, row))
    return selected


def _section(text: str, start: str, end: str, source: str) -> list[str] | None:
    lines = text.splitlines()
    starts = [i for i, line in enumerate(lines) if line == start]
    ends = [i for i, line in enumerate(lines) if line == end]
    if len(starts) != 1 or len(ends) != 1 or starts[0] >= ends[0]:
        return None
    return lines[starts[0] + 1 : ends[0]]


def _provenance(text: str, source: str) -> tuple[str, str]:
    image_ids = []
    image_digests = []
    raw_ids = []
    raw_digests = []
    for line in text.splitlines():
        if line.startswith("IMAGE_ID="):
            raw_ids.append(line)
            match = IMAGE_ID.fullmatch(line)
            if match:
                image_ids.append(match.group(1))
        if line.startswith("IMAGE_REPO_DIGEST="):
            raw_digests.append(line)
            match = IMAGE_DIGEST.fullmatch(line)
            if match:
                image_digests.append(match.group(1))
    if not (
        len(raw_ids) == len(raw_digests) == len(image_ids) == len(image_digests) == 1
    ):
        raise ValidationError(f"{source}: invalid immutable image evidence")
    return image_ids[0], image_digests[0]


def classify_arm(text: str, arm: str, source: str) -> dict[str, Any]:
    image_id, digest = _provenance(text, source)
    apply_ok = text.splitlines().count(f"APPLY_OK {arm}") == 1
    body = _section(text, ">>>>> Scenario Start", ">>>>> Scenario End", source)
    if body is None:
        return {
            "apply_ok": apply_ok,
            "exit_code": None,
            "image_id": image_id,
            "image_repository_digest": digest,
            "result_count": 0,
            "valid": False,
        }
    results = [line for line in body if line.startswith("RESULT=")]
    exits = [line for line in body if re.fullmatch(r"SCENARIO_EXIT=-?[0-9]+", line)]
    exit_code = int(exits[0].split("=", 1)[1]) if len(exits) == 1 else None
    valid = (
        apply_ok
        and len(results) == 1
        and results[0] != "RESULT="
        and exit_code == 0
        and ERROR_SENTINEL.search("\n".join(body)) is None
    )
    return {
        "apply_ok": apply_ok,
        "exit_code": exit_code,
        "image_id": image_id,
        "image_repository_digest": digest,
        "result_count": len(results),
        "valid": valid,
    }


def _unique_by_id(rows: list[dict], instance_id: str, source: str) -> tuple[int, dict]:
    matches = [
        (index, row)
        for index, row in enumerate(rows)
        if row.get("instance_id") == instance_id
    ]
    if len(matches) != 1:
        raise ValidationError(
            f"{source}: expected one row for {instance_id}, got {len(matches)}"
        )
    return matches[0]


def _fisher(x: int) -> Fraction:
    event_total = x + 5
    start = max(0, event_total - 29)
    return Fraction(
        sum(
            math.comb(37, i) * math.comb(29, event_total - i)
            for i in range(start, x + 1)
        ),
        math.comb(66, event_total),
    )


def _zero(n: int) -> Decimal:
    if type(n) is not int or n < 1:
        raise ValidationError("n must be a positive exact integer")
    with localcontext() as context:
        context.prec = 80
        return Decimal(1) - (Decimal("0.05").ln() / Decimal(n)).exp()


def _assert_close(rendered: Any, expected: Decimal, source: str) -> None:
    if not isinstance(rendered, str):
        raise ValidationError(f"{source}: canonical decimal must be a string")
    try:
        actual = Decimal(rendered)
    except Exception as exc:
        raise ValidationError(f"{source}: malformed decimal") from exc
    if abs(actual - expected) > Decimal("0.0000000000000000006"):
        raise ValidationError(f"{source}: decimal differs beyond the registered tolerance")


def validate_source_ledger(receipt: dict[str, Any]) -> None:
    if receipt.get("source_reference_commit") != PREDECESSOR:
        raise ValidationError("materialization receipt has wrong source commit")
    sources = receipt.get("source_inputs")
    if not isinstance(sources, list) or receipt.get("source_count") != len(sources):
        raise ValidationError("materialization source ledger accounting is malformed")
    paths = [row.get("path") for row in sources if isinstance(row, dict)]
    if len(paths) != len(sources) or paths != sorted(paths) or len(paths) != len(set(paths)):
        raise ValidationError("source ledger paths are missing, duplicate, or unsorted")
    for index, row in enumerate(sources):
        if set(row) != {
            "byte_count",
            "git_blob_oid",
            "git_mode",
            "path",
            "reference_commit",
            "sha256_file_bytes",
        }:
            raise ValidationError(f"source ledger row {index} has wrong schema")
        if type(row["byte_count"]) is not int or row["byte_count"] < 0:
            raise ValidationError(f"source ledger row {index} has non-integer byte count")
        path_text = row["path"]
        path = Path(path_text)
        if path.is_absolute() or ".." in path.parts:
            raise ValidationError(f"source ledger row {index} escapes repository")
        absolute = ROOT / path
        metadata = absolute.lstat()
        if not stat.S_ISREG(metadata.st_mode) or absolute.is_symlink():
            raise ValidationError(f"{path}: source is not regular")
        listing = _git("ls-tree", PREDECESSOR, "--", path_text).decode("utf-8")
        lines = [line for line in listing.splitlines() if line]
        if len(lines) != 1:
            raise ValidationError(f"{path}: absent or ambiguous predecessor blob")
        prefix, exact_path = lines[0].split("\t", 1)
        mode, kind, oid = prefix.split(" ")
        if (
            exact_path != path_text
            or kind != "blob"
            or mode not in {"100644", "100755"}
            or oid != row["git_blob_oid"]
            or mode != row["git_mode"]
            or row["reference_commit"] != PREDECESSOR
            or HEX40.fullmatch(oid) is None
        ):
            raise ValidationError(f"{path}: predecessor Git identity mismatch")
        head = _git("ls-tree", "HEAD", "--", path_text).decode("utf-8")
        if head != listing:
            raise ValidationError(f"{path}: HEAD source blob differs from predecessor")
        committed = _git("cat-file", "blob", oid)
        current = absolute.read_bytes()
        if current != committed:
            raise ValidationError(f"{path}: worktree source differs from Git blob")
        if (
            row["byte_count"] != len(current)
            or row["sha256_file_bytes"] != _sha(current)
            or HEX64.fullmatch(row["sha256_file_bytes"]) is None
        ):
            raise ValidationError(f"{path}: source byte receipt mismatch")


def validate_output_receipt(receipt: dict[str, Any]) -> None:
    expected_paths = sorted(path.as_posix() for path in OUTPUTS)
    records = receipt.get("outputs")
    if not isinstance(records, list):
        raise ValidationError("materialization output ledger is missing")
    paths = [row.get("path") for row in records if isinstance(row, dict)]
    if paths != expected_paths:
        raise ValidationError("materialization output ledger path set/order mismatch")
    for row in records:
        if set(row) != {"byte_count", "path", "sha256_file_bytes"}:
            raise ValidationError("materialization output ledger schema mismatch")
        if type(row["byte_count"]) is not int or row["byte_count"] < 0:
            raise ValidationError("materialization output byte count is not an exact integer")
        data = (ROOT / row["path"]).read_bytes()
        if row["byte_count"] != len(data) or row["sha256_file_bytes"] != _sha(data):
            raise ValidationError(f"{row['path']}: materialized output digest mismatch")
    actions = receipt.get("external_actions")
    expected_actions = {
        "cohort_acquisitions": 0,
        "gpu_allocations": 0,
        "human_contacts": 0,
        "model_judgment_calls": 0,
        "provider_calls": 0,
        "scientific_containers": 0,
        "spend_usd": "0.00",
        "target_executions": 0,
    }
    if actions != expected_actions or any(
        type(value) is not int
        for key, value in actions.items()
        if key != "spend_usd"
    ):
        raise ValidationError("materialization receipt overstates or mistypes zero actions")
    if receipt.get("result_status") != {
        "cohort_acquisition": "not_authorized",
        "design_preflight": "supported",
        "independent_ground_truth": "blocked",
        "retained_evidence_recovery": "blocked",
    }:
        raise ValidationError("materialization result statuses are wrong")


def validate_selection_freeze(
    census: dict[str, Any],
    selection_receipt: dict[str, Any],
) -> None:
    if census.get("schema_version") != "telos.iter240.selection_census.v1":
        raise ValidationError("selection census schema is wrong")
    if (
        selection_receipt.get("schema_version")
        != "telos.iter240.selection_freeze_receipt.v1"
    ):
        raise ValidationError("selection freeze receipt schema is wrong")
    validate_source_ledger(selection_receipt)
    sources = selection_receipt.get("source_inputs")
    expected_sources = sorted(
        (
            Path("experiments") / run / "proof/iter200_per_candidate.json"
        ).as_posix()
        for run in FRESH_RUNS
    )
    if [row.get("path") for row in sources] != expected_sources:
        raise ValidationError("selection freeze read a diagnostic or unregistered source")
    census_bytes = (ROOT / SELECTION_CENSUS).read_bytes()
    if selection_receipt.get("selection_census") != {
        "byte_count": len(census_bytes),
        "path": SELECTION_CENSUS.as_posix(),
        "sha256_file_bytes": _sha(census_bytes),
    }:
        raise ValidationError("selection freeze does not bind the census bytes")
    builder_bytes = (ROOT / BUILDER).read_bytes()
    if (
        selection_receipt.get("builder_path") != BUILDER.as_posix()
        or selection_receipt.get("builder_sha256") != _sha(builder_bytes)
    ):
        raise ValidationError("selection freeze does not bind the active selector instrument")
    if selection_receipt.get("external_actions") != {
        "gpu_allocations": 0,
        "model_or_provider_calls": 0,
        "scientific_containers": 0,
        "spend_usd": "0.00",
        "target_executions": 0,
    }:
        raise ValidationError("selection freeze overstates or mistypes the zero-action boundary")
    for path in (SELECTION_CENSUS, SELECTION_RECEIPT):
        listing = _git("ls-tree", "HEAD", "--", path.as_posix()).decode("utf-8")
        lines = [line for line in listing.splitlines() if line]
        if len(lines) != 1:
            raise ValidationError(f"{path}: selection freeze is not committed")
        prefix, exact_path = lines[0].split("\t", 1)
        mode, kind, oid = prefix.split(" ")
        if exact_path != path.as_posix() or mode != "100644" or kind != "blob":
            raise ValidationError(f"{path}: committed selection freeze is not regular")
        if (ROOT / path).read_bytes() != _git("cat-file", "blob", oid):
            raise ValidationError(f"{path}: worktree differs from committed selection freeze")


def validate_missingness(
    census: dict[str, Any],
    manifest: dict[str, Any],
    taxonomy: dict[str, Any],
) -> list[tuple[str, str]]:
    independently_selected: list[tuple[str, int, dict]] = []
    documents: dict[str, dict[str, Any]] = {}
    for run in FRESH_RUNS:
        path = Path("experiments") / run / "proof/iter200_per_candidate.json"
        document = _object(load_json(path), path.as_posix())
        documents[run] = document
        for index, row in select_independently(
            document.get("candidates"), source=f"{path}#/candidates"
        ):
            independently_selected.append((run, index, row))
    keys = [(run, row.get("instance_id")) for run, _, row in independently_selected]
    if len(keys) != 13 or len(set(keys)) != 13 or len({iid for _, iid in keys}) != 13:
        raise ValidationError("independent strict selector does not yield 13 unique tasks")

    manifest_rows = manifest.get("selected_rows")
    if (
        not isinstance(manifest_rows, list)
        or manifest.get("selected_count") != 13
        or manifest.get("unique_task_count") != 13
        or type(manifest.get("selected_count")) is not int
        or type(manifest.get("unique_task_count")) is not int
    ):
        raise ValidationError("missingness manifest count accounting is wrong")
    projected = [
        (
            row.get("source_run"),
            row.get("instance_id"),
            row.get("pointers", {}).get("candidate", {}).get("json_pointer"),
        )
        for row in manifest_rows
    ]
    expected_projection = [
        (run, row["instance_id"], f"/candidates/{index}")
        for run, index, row in independently_selected
    ]
    census_rows = census.get("selected_rows")
    census_projection = [
        (
            row.get("source_run"),
            row.get("instance_id"),
            row.get("candidate_pointer", {}).get("json_pointer"),
        )
        for row in census_rows
    ] if isinstance(census_rows, list) else []
    if (
        census.get("selected_count") != 13
        or census.get("unique_task_count") != 13
        or type(census.get("selected_count")) is not int
        or type(census.get("unique_task_count")) is not int
        or census_projection != expected_projection
    ):
        raise ValidationError("committed selection census differs from independent selector")
    if projected != expected_projection:
        raise ValidationError("missingness manifest differs from independent selector")
    if manifest.get("selection_contract", {}).get("typed_boolean_identity_required") is not True:
        raise ValidationError("missingness manifest weakens exact boolean selection")

    taxonomy_rows = taxonomy.get("rows")
    if not isinstance(taxonomy_rows, list) or len(taxonomy_rows) != 13:
        raise ValidationError("availability taxonomy row count is wrong")
    taxonomy_by_key = {
        (row.get("source_run"), row.get("instance_id")): row
        for row in taxonomy_rows
        if isinstance(row, dict)
    }
    if len(taxonomy_by_key) != 13:
        raise ValidationError("availability taxonomy duplicates or loses a row")

    derived_states: dict[tuple[str, str], str] = {}
    for run, _, selected in independently_selected:
        instance_id = selected["instance_id"]
        root = Path("experiments") / run / "proof"
        summary_path = root / "raw/scenarios/scenarios_summary.json"
        blind_path = root / "blind_judge_verdicts.json"
        summary = _object(load_json(summary_path), summary_path.as_posix())
        blind = _object(load_json(blind_path), blind_path.as_posix())
        _, scenario = _unique_by_id(
            _rows(summary, "manifest", summary_path.as_posix()),
            instance_id,
            summary_path.as_posix(),
        )
        blind_matches = [
            row
            for row in _rows(blind, "verdicts", blind_path.as_posix())
            if row.get("instance_id") == instance_id
        ]
        status = scenario.get("status")
        if status in {"excluded_unsafe", "no_scenario"}:
            state = status
        elif status == "scenario":
            candidate_path = root / f"raw/execution/{instance_id}.variant.log"
            accepted_path = root / f"raw/execution/{instance_id}.gold.log"
            candidate = classify_arm(
                (ROOT / candidate_path).read_text(encoding="utf-8"),
                "variant",
                candidate_path.as_posix(),
            )
            accepted = classify_arm(
                (ROOT / accepted_path).read_text(encoding="utf-8"),
                "gold",
                accepted_path.as_posix(),
            )
            if candidate["valid"] and accepted["valid"]:
                state = "paired_valid_judged" if blind_matches else "paired_valid_unjudged"
            elif not candidate["valid"] and not accepted["valid"]:
                state = "paired_invalid_both_arms"
            elif not candidate["valid"] and accepted["valid"]:
                state = "paired_invalid_candidate_only"
            else:
                state = "source_inconsistent"
            retained = taxonomy_by_key[(run, instance_id)].get("arm_summaries")
            if retained != {"accepted": accepted, "candidate": candidate}:
                raise ValidationError(f"{run}/{instance_id}: retained arm summary mismatch")
        else:
            state = "source_inconsistent"
        derived_states[(run, instance_id)] = state
        row = taxonomy_by_key[(run, instance_id)]
        if (
            row.get("availability_state") != state
            or row.get("retained_blind_verdict_count") != len(blind_matches)
            or row.get("historical_outcome_exposed") is not True
        ):
            raise ValidationError(f"{run}/{instance_id}: taxonomy projection mismatch")

    counts = dict(sorted(Counter(derived_states.values()).items()))
    if counts != {
        "excluded_unsafe": 7,
        "no_scenario": 1,
        "paired_invalid_both_arms": 3,
        "paired_invalid_candidate_only": 2,
    }:
        raise ValidationError(f"availability taxonomy changed: {counts}")
    if (
        taxonomy.get("availability_counts") != counts
        or taxonomy.get("paired_valid_rows") != 0
        or taxonomy.get("future_primary_endpoint_rows") != 0
        or taxonomy.get("retained_evidence_recovery") != "blocked"
    ):
        raise ValidationError("availability result boundary is wrong")
    return keys


def validate_frame(frame: dict[str, Any], missing_keys: list[tuple[str, str]]) -> None:
    original: set[tuple[str, str]] = set()
    for run in NATURAL_RUNS:
        path = Path("experiments") / run / "proof/blind_judge_verdicts.json"
        document = _object(load_json(path), path.as_posix())
        for index, row in enumerate(_rows(document, "verdicts", path.as_posix())):
            value = row.get("both_judges_flag_only_model")
            if type(value) is not bool:
                raise ValidationError(f"{path}#/verdicts/{index}: nonboolean label")
            if value is True:
                key = (run, row.get("instance_id"))
                if key in original:
                    raise ValidationError(f"duplicate original positive {key}")
                original.add(key)
    judges = _object(load_json(
        Path("experiments/iter235_witness_recovery/proof/raw/judge/judge_summary.json")
    ), "iter235 judge")
    recovered = set()
    for index, row in enumerate(_rows(judges, "verdicts", "iter235 judge")):
        value = row.get("confirmed")
        if type(value) is not bool:
            raise ValidationError(f"iter235 judge row {index}: nonboolean")
        if value is True:
            recovered.add((row.get("run"), row.get("instance_id")))
    if len(original) != 13 or len(recovered) != 4 or original & recovered:
        raise ValidationError("independent positive-frame reconstruction changed")

    eval_path = Path(
        "experiments/iter230_gold_free_detector_natural/proof/raw/eval_set.json"
    )
    eval_set = _object(load_json(eval_path), eval_path.as_posix())
    hard = {
        (row.get("run"), row.get("instance_id"))
        for row in _rows(eval_set, "negatives", eval_path.as_posix())
        if row.get("reason") == "certified_no_observed_divergence"
        and row.get("label") == "certified_correct"
    }
    if len(hard) != 25:
        raise ValidationError("independent hard-control reconstruction changed")

    rows = frame.get("rows")
    if not isinstance(rows, list):
        raise ValidationError("frame rows are missing")
    keyed: dict[str, set[tuple[str, str]]] = {
        "operational_positive": set(),
        "hard_control": set(),
        "fresh_missing": set(),
    }
    task_strata: dict[str, set[str]] = {}
    row_ids: set[str] = set()
    for row in rows:
        if not isinstance(row, dict):
            raise ValidationError("frame row is not an object")
        stratum = row.get("operational_stratum")
        if stratum not in keyed:
            raise ValidationError("frame row has unknown stratum")
        key = (row.get("source_run"), row.get("instance_id"))
        keyed[stratum].add(key)
        task = row.get("task_id")
        if task != row.get("instance_id"):
            raise ValidationError("frame task identity differs from source instance")
        task_strata.setdefault(task, set()).add(stratum)
        row_id = row.get("candidate_row_id")
        if (
            not isinstance(row_id, str)
            or HEX64.fullmatch(row_id) is None
            or row_id in row_ids
        ):
            raise ValidationError("frame candidate-row identity is malformed or duplicate")
        row_ids.add(row_id)
        if row.get("independent_semantic_label") is not None:
            raise ValidationError("frame invents an independent semantic label")
        patch = row.get("patch")
        if not isinstance(patch, dict):
            raise ValidationError("frame patch receipt is missing")
        patch_path = Path(patch.get("path", ""))
        data = (ROOT / patch_path).read_bytes()
        if (
            patch.get("sha256_file_bytes") != _sha(data)
            or not data.endswith(b"\n")
            or patch.get("legacy_sha256_one_terminal_lf_removed")
            != _sha(data[:-1])
        ):
            raise ValidationError(f"{patch_path}: frame patch digest mismatch")

    if keyed["operational_positive"] != original | recovered:
        raise ValidationError("frame operational positives differ from independent sources")
    if keyed["hard_control"] != hard:
        raise ValidationError("frame hard controls differ from independent sources")
    if keyed["fresh_missing"] != set(missing_keys):
        raise ValidationError("frame fresh rows differ from strict selector")
    overlaps = sorted(task for task, strata in task_strata.items() if len(strata) > 1)
    if (
        len(rows) != 55
        or len(task_strata) != 37
        or overlaps != ["django__django-11964", "pydata__xarray-7233"]
        or frame.get("candidate_row_count") != 55
        or frame.get("unique_task_count") != 37
        or frame.get("independent_semantic_label_count") != 0
        or frame.get("inferential_unit") != "unique_task_identity"
    ):
        raise ValidationError("frame cluster accounting is wrong")
    for row in rows:
        strata = sorted(
            task_strata[row["task_id"]],
            key={"operational_positive": 0, "hard_control": 1, "fresh_missing": 2}.get,
        )
        if (
            row.get("task_strata") != strata
            or row.get("cross_stratum_overlap") is not (len(strata) > 1)
        ):
            raise ValidationError("frame row overlap projection is wrong")


def validate_curves(curves: dict[str, Any]) -> None:
    branches = curves.get("missingness_branches")
    if not isinstance(branches, list) or len(branches) != 14:
        raise ValidationError("missingness branch grid is incomplete")
    for x, row in enumerate(branches):
        if (
            type(row.get("fresh_operational_positive_count")) is not int
            or row.get("fresh_operational_positive_count") != x
        ):
            raise ValidationError("missingness branch is selected, missing, or reordered")
        fisher = row.get("exploratory_fisher")
        expected = _fisher(x)
        if (
            not isinstance(fisher, dict)
            or fisher.get("table") != [[x, 37 - x], [5, 24]]
            or fisher.get("alternative") != "fresh_less_than_reused"
            or fisher.get("numerator") != expected.numerator
            or fisher.get("denominator") != expected.denominator
            or type(fisher.get("numerator")) is not int
            or type(fisher.get("denominator")) is not int
            or row.get("registered_strict_concentration_holds") is not (29 * x < 185)
            or row.get("fresh_rate") != {"denominator": 37, "numerator": x}
        ):
            raise ValidationError(f"missingness branch x={x} is wrong")

    zero = curves.get("zero_event_upper_bounds")
    grid = zero.get("grid") if isinstance(zero, dict) else None
    if not isinstance(grid, list) or len(grid) != 500:
        raise ValidationError("zero-event grid does not cover n=1..500")
    for expected_n, row in enumerate(grid, start=1):
        if (
            type(row.get("n_unique_tasks")) is not int
            or row.get("n_unique_tasks") != expected_n
        ):
            raise ValidationError("zero-event grid is missing or reordered")
        _assert_close(
            row.get("one_sided_95_percent_upper_bound"),
            _zero(expected_n),
            f"zero-event n={expected_n}",
        )
    expected_crossings = {"0.10": 29, "0.05": 59, "0.02": 149, "0.01": 299}
    crossings = zero.get("threshold_crossings")
    if not isinstance(crossings, list) or len(crossings) != 4:
        raise ValidationError("zero-event threshold grid is incomplete")
    for row in crossings:
        threshold_text = row.get("threshold")
        n = expected_crossings.get(threshold_text)
        if (
            n is None
            or type(row.get("first_n_at_or_below")) is not int
            or row.get("first_n_at_or_below") != n
        ):
            raise ValidationError("zero-event first-crossing result is wrong")
        threshold = Decimal(threshold_text)
        with localcontext() as context:
            context.prec = 80
            if not (
                (Decimal(1) - threshold) ** (n - 1) > Decimal("0.05")
                and (Decimal(1) - threshold) ** n <= Decimal("0.05")
            ):
                raise ValidationError("zero-event crossing fails exact rational inequality")
        _assert_close(row.get("upper_bound_at_n"), _zero(n), "threshold n")
        _assert_close(
            row.get("upper_bound_at_n_minus_one"), _zero(n - 1), "threshold n-1"
        )
    numeric_contract = zero.get("numeric_contract", "")
    if "never binary-float identity" not in numeric_contract:
        raise ValidationError("zero-event artifact does not forbid bit-exact libm comparison")

    acquisition = curves.get("acquisition_sensitivity")
    if not isinstance(acquisition, dict):
        raise ValidationError("acquisition sensitivity is missing")
    historical = acquisition.get("historical_certification_yield")
    conditional = acquisition.get("conditional_solution_patch_diagnostic")
    if (
        not isinstance(historical, dict)
        or historical.get("certified") != 37
        or historical.get("denominator") != 64
        or not isinstance(conditional, dict)
        or conditional.get("certified") != 37
        or conditional.get("denominator") != 62
        or conditional.get("forbidden_as_acquisition_input") is not True
    ):
        raise ValidationError("37/64 acquisition yield is confused with conditional 37/62")
    yield_grid = [(2, 5), (1, 2), (37, 64), (3, 5), (2, 3), (3, 4), (4, 5)]
    targets = [29, 59, 149, 299]
    rows = acquisition.get("rows")
    if not isinstance(rows, list) or len(rows) != len(yield_grid):
        raise ValidationError("acquisition yield grid is incomplete")
    for row, (numerator, denominator) in zip(rows, yield_grid, strict=True):
        if row.get("certification_yield") != {
            "numerator": numerator,
            "denominator": denominator,
        }:
            raise ValidationError("acquisition yield row is wrong")
        target_rows = row.get("targets")
        if not isinstance(target_rows, list) or len(target_rows) != len(targets):
            raise ValidationError("acquisition target row is incomplete")
        for item, target in zip(target_rows, targets, strict=True):
            required = (target * denominator + numerator - 1) // numerator
            if item != {
                "required_solve_attempts": required,
                "target_unique_certified_tasks": target,
            }:
                raise ValidationError("acquisition uses floor/round or wrong denominator")
    readiness = curves.get("assurance_delta_readiness")
    if (
        not isinstance(readiness, dict)
        or readiness.get("paired_detector_power") != "blocked"
        or readiness.get("selected_or_optimized_branch") is not None
        or readiness.get("missing_measured_inputs")
        != [
            "supported_label_yield",
            "consequence_validity",
            "adjudication_completion",
            "within_task_discordance",
            "control_false_rejection_behavior",
        ]
    ):
        raise ValidationError("assurance-delta power is not honestly blocked")


def validate_result_boundary() -> None:
    path = ROOT / RESULT
    if not path.exists():
        return
    text = path.read_text(encoding="utf-8")
    required = (
        "design_preflight: **supported**",
        "retained_evidence_recovery: **blocked**",
        "independent_ground_truth: **blocked**",
        "cohort_acquisition: **not_authorized**",
        "`k=0,N=37,u=13`",
    )
    missing = [item for item in required if item not in text]
    if missing:
        raise ValidationError("RESULT.md lacks exact status boundary: " + ", ".join(missing))
    forbidden = (
        "independent ground truth is supported",
        "detector efficacy is supported",
        "cohort acquisition is authorized",
        "state of the art",
        "production-ready",
    )
    lowered = text.casefold()
    if any(item in lowered for item in forbidden):
        raise ValidationError("RESULT.md contains a forbidden overclaim")


def validate() -> None:
    if _git("rev-parse", f"{AUTHORIZATION}^").decode().strip() != PREDECESSOR:
        raise ValidationError("authorization parent is not merged iter239")
    if _git("rev-parse", f"{ACTIVATION}^").decode().strip() != AUTHORIZATION:
        raise ValidationError("activation parent is not authorization")
    if subprocess.run(
        ["git", "merge-base", "--is-ancestor", ACTIVATION, "HEAD"],
        cwd=ROOT,
        capture_output=True,
        check=False,
    ).returncode != 0:
        raise ValidationError("HEAD does not descend from iter240 activation")

    selector_problems = validate_selector_source(
        (ROOT / BUILDER).read_text(encoding="utf-8")
    )
    if selector_problems:
        raise ValidationError("; ".join(selector_problems))

    census = _object(
        load_json(SELECTION_CENSUS, canonical=True), SELECTION_CENSUS.as_posix()
    )
    selection_receipt = _object(
        load_json(SELECTION_RECEIPT, canonical=True), SELECTION_RECEIPT.as_posix()
    )
    manifest = _object(load_json(MANIFEST, canonical=True), MANIFEST.as_posix())
    taxonomy = _object(load_json(TAXONOMY, canonical=True), TAXONOMY.as_posix())
    frame = _object(load_json(FRAME, canonical=True), FRAME.as_posix())
    curves = _object(load_json(CURVES, canonical=True), CURVES.as_posix())
    _object(load_json(ROLE_POLICY, canonical=True), ROLE_POLICY.as_posix())
    receipt = _object(load_json(RECEIPT, canonical=True), RECEIPT.as_posix())

    schemas = {
        MANIFEST: "telos.iter240.missingness_manifest.v1",
        TAXONOMY: "telos.iter240.availability_taxonomy.v1",
        FRAME: "telos.iter240.ground_truth_frame.v1",
        CURVES: "telos.iter240.decision_curves.v1",
        RECEIPT: "telos.iter240.materialization_receipt.v1",
    }
    documents = {
        MANIFEST: manifest,
        TAXONOMY: taxonomy,
        FRAME: frame,
        CURVES: curves,
        RECEIPT: receipt,
    }
    for path, schema in schemas.items():
        if documents[path].get("schema_version") != schema:
            raise ValidationError(f"{path}: wrong schema version")

    validate_selection_freeze(census, selection_receipt)
    validate_source_ledger(receipt)
    validate_output_receipt(receipt)
    missing_keys = validate_missingness(census, manifest, taxonomy)
    validate_frame(frame, missing_keys)
    validate_curves(curves)
    validate_result_boundary()


def main() -> int:
    try:
        validate()
    except (ValidationError, OSError, UnicodeError, KeyError, TypeError) as exc:
        print(f"iter240 ground-truth admission validation: FAIL: {exc}")
        return 1
    print(
        "iter240 ground-truth admission validation: PASS "
        "(13 missing; 55 rows/37 tasks; retained recovery and ground truth blocked)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
