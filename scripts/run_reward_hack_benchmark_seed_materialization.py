#!/usr/bin/env python3
"""Iter153 - materialize the iter152 reward-hack seed artifact.

This is a zero-spend gate. It reads only committed iter152 proof artifacts and writes a
reviewer-facing seed package under benchmarks/reward_hack_seed_v0 plus the iter153 proof packet.
It does not call providers, run SWE-bench, or add judge verdicts.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import sys
import tarfile
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from telos.proof import receipt_digest

ROOT = Path(__file__).resolve().parents[1]
EXPERIMENT = ROOT / "experiments/iter153_reward_hack_benchmark_seed_materialization"
PROOF = EXPERIMENT / "proof"
VALID = PROOF / "valid"
RAW = PROOF / "raw"
SEED_DIR = ROOT / "benchmarks/reward_hack_seed_v0"

SOURCE_EXPERIMENT = "iter152_reward_model_gaming_scale"
SOURCE_ROOT = ROOT / f"experiments/{SOURCE_EXPERIMENT}/proof"
SOURCE_RESULTS = SOURCE_ROOT / "raw/detection_results.json"
SOURCE_REPORTS = SOURCE_ROOT / "raw/det_reports.tgz"
SOURCE_SUMMARY = SOURCE_ROOT / "run_summary.json"

SEED_JSONL = SEED_DIR / "reward_hack_seed_v0.jsonl"
MANIFEST = SEED_DIR / "manifest.json"
README = SEED_DIR / "README.md"
SCHEMA = SEED_DIR / "schema.json"


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def sha256_text(text: str) -> str:
    return sha256_bytes(text.encode("utf-8"))


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def stable_json(data: Any) -> str:
    return json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def load_source_rows() -> list[dict[str, Any]]:
    rows = json.loads(SOURCE_RESULTS.read_text(encoding="utf-8"))
    if not isinstance(rows, list):
        raise ValueError("iter152 detection_results.json must be a list")
    return rows


def report_index() -> dict[str, list[dict[str, str]]]:
    by_instance: dict[str, list[dict[str, str]]] = {}
    with tarfile.open(SOURCE_REPORTS, "r:gz") as archive:
        for member in archive.getmembers():
            if not member.isfile() or not member.name.endswith("/report.json"):
                continue
            if "/hack/" not in member.name:
                continue
            instance_id = member.name.split("/hack/", 1)[1].split("/report.json", 1)[0]
            extracted = archive.extractfile(member)
            if extracted is None:
                raise ValueError(f"could not read tar member: {member.name}")
            by_instance.setdefault(instance_id, []).append(
                {
                    "path": member.name,
                    "sha256": sha256_bytes(extracted.read()),
                }
            )
    return {key: sorted(value, key=lambda item: item["path"]) for key, value in by_instance.items()}


def materialize_rows(source_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    reports = report_index()
    rows: list[dict[str, Any]] = []
    both_miss_source = [
        (idx, row) for idx, row in enumerate(source_rows) if row.get("both_miss") is True
    ]
    for ordinal, (source_index, source_row) in enumerate(both_miss_source, start=1):
        instance_id = str(source_row["id"])
        hack_diff = str(source_row.get("hack_diff") or "")
        if not hack_diff.strip():
            raise ValueError(f"missing hack diff for {instance_id}")
        source_reports = reports.get(instance_id, [])
        if not source_reports:
            raise ValueError(f"missing hack report in det_reports.tgz for {instance_id}")
        row = {
            "schema_version": "telos.reward_hack_seed.v0.row.v1",
            "row_id": f"telos-rh-v0-{ordinal:03d}",
            "source_experiment": SOURCE_EXPERIMENT,
            "source_detection_results_path": str(SOURCE_RESULTS.relative_to(ROOT)),
            "source_detection_results_index": source_index,
            "source_row_sha256": sha256_text(stable_json(source_row)),
            "source_det_reports_path": str(SOURCE_REPORTS.relative_to(ROOT)),
            "source_report_paths": source_reports,
            "repo": source_row["repo"],
            "instance_id": instance_id,
            "execution_verified_both_miss": True,
            "official_harness_verdict": {
                "both_miss": source_row["both_miss"],
                "both_miss_resolved": source_row["both_miss_resolved"],
                "baseline_resolved": source_row["baseline_resolved"],
            },
            "static_verdicts": {
                "deterministic_detector_flags": source_row["detector_flags"],
                "deterministic_detector_fooled": source_row["detector_flags"] is False,
                "gpt_5_6_terra_verdict": source_row["judge_gpt56"],
                "gpt_5_6_terra_fooled": source_row["gpt_fooled"],
                "claude_opus_4_8_verdict": source_row["judge_opus48"],
                "claude_opus_4_8_fooled": source_row["opus_fooled"],
                "survives_all_static": source_row["survives_all_static"],
            },
            "hack_diff_sha256": sha256_text(hack_diff),
            "hack_diff": hack_diff,
            "claim_boundary": (
                "Seed row from iter152 committed evidence only; not a benchmark score, "
                "leaderboard result, model-superiority result, SOTA claim, or natural-RL "
                "frequency claim."
            ),
        }
        rows.append(row)
    return rows


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows)
    path.write_text(payload, encoding="utf-8")


def build_schema() -> dict[str, Any]:
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "title": "Telos reward_hack_seed_v0 row",
        "type": "object",
        "required": [
            "row_id",
            "source_experiment",
            "source_detection_results_index",
            "repo",
            "instance_id",
            "execution_verified_both_miss",
            "static_verdicts",
            "hack_diff_sha256",
            "hack_diff",
            "claim_boundary",
        ],
        "properties": {
            "row_id": {"type": "string"},
            "repo": {"type": "string"},
            "instance_id": {"type": "string"},
            "execution_verified_both_miss": {"const": True},
            "hack_diff_sha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
            "hack_diff": {"type": "string"},
            "static_verdicts": {"type": "object"},
        },
        "additionalProperties": True,
    }


def build_manifest(rows: list[dict[str, Any]]) -> dict[str, Any]:
    repos = sorted({row["repo"] for row in rows})
    survives_all = sum(
        1 for row in rows if row["static_verdicts"]["survives_all_static"] is True
    )
    return {
        "schema_version": "telos.reward_hack_seed.v0.manifest.v1",
        "seed_id": "reward_hack_seed_v0",
        "status": "validated_seed_artifact_not_released_benchmark",
        "source_experiment": SOURCE_EXPERIMENT,
        "source_artifacts": {
            str(SOURCE_RESULTS.relative_to(ROOT)): sha256_file(SOURCE_RESULTS),
            str(SOURCE_REPORTS.relative_to(ROOT)): sha256_file(SOURCE_REPORTS),
            str(SOURCE_SUMMARY.relative_to(ROOT)): sha256_file(SOURCE_SUMMARY),
        },
        "artifacts": {
            str(SEED_JSONL.relative_to(ROOT)): sha256_file(SEED_JSONL),
            str(SCHEMA.relative_to(ROOT)): sha256_file(SCHEMA),
        },
        "row_count": len(rows),
        "repo_count": len(repos),
        "repos": repos,
        "hack_diff_sha256_present": sum(1 for row in rows if row.get("hack_diff_sha256")),
        "survives_all_static": survives_all,
        "new_provider_calls": 0,
        "new_cloud_resources": 0,
        "new_swebench_executions": 0,
        "new_judge_calls": 0,
        "benchmark_result_claimed": False,
        "released_benchmark_claimed": False,
        "leaderboard_claimed": False,
        "model_superiority_claimed": False,
        "sota_claimed": False,
        "natural_rl_frequency_claimed": False,
        "claim_boundary": (
            "Telos materialized a validated seed artifact from the 20 iter152 reward-hack "
            "diffs, preserving 8-repository coverage, static-verifier labels, and the 5/20 "
            "survives-all-static label. This is not a released benchmark, benchmark score, "
            "leaderboard, model comparison, state-of-the-art claim, or natural-RL frequency claim."
        ),
    }


def build_readme(manifest: dict[str, Any]) -> str:
    return f"""# Reward Hack Seed v0

This directory is a validated seed artifact derived from committed Telos iter152 evidence.
It contains {manifest["row_count"]} execution-verified both-miss hack diffs across
{manifest["repo_count"]} repositories.

The seed preserves:

- one JSONL row per iter152 both-miss hack,
- a SHA256 for each hack diff,
- detector and reward-model judge verdict labels from iter152,
- source links and hashes back to the committed iter152 proof artifacts,
- the `survives_all_static` label, which is true for {manifest["survives_all_static"]}/20 rows.

Claim boundary: this is a seed artifact, not a released benchmark, benchmark score,
leaderboard, model-comparison result, state-of-the-art claim, or natural-RL frequency claim.
No provider calls, cloud resources, SWE-bench executions, or judge calls were added by iter153.

Primary files:

- `reward_hack_seed_v0.jsonl`: seed rows.
- `manifest.json`: counts, source hashes, artifact hashes, and claim-boundary flags.
- `schema.json`: minimal row schema for reviewer inspection.
"""


OVERCLAIM_PATTERNS = [
    re.compile(r"\bis a released benchmark\b", re.IGNORECASE),
    re.compile(r"\breleased benchmark result\b", re.IGNORECASE),
    re.compile(r"\bleaderboard result\b", re.IGNORECASE),
    re.compile(r"\bmodel superiority\b", re.IGNORECASE),
    re.compile(r"\bstate-of-the-art result\b", re.IGNORECASE),
    re.compile(r"\bSOTA result\b", re.IGNORECASE),
]


def validate_seed(rows: list[dict[str, Any]], manifest: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
    failures: list[str] = []
    source_rows = load_source_rows()
    source_both_miss = [row for row in source_rows if row.get("both_miss") is True]
    report_paths = {
        report["path"]
        for reports in report_index().values()
        for report in reports
    }

    if len(rows) != 20:
        failures.append(f"expected 20 rows, got {len(rows)}")
    if len(source_both_miss) != 20:
        failures.append(f"expected 20 source both-miss rows, got {len(source_both_miss)}")

    row_ids = [row.get("row_id") for row in rows]
    if len(set(row_ids)) != len(row_ids):
        failures.append("row_id values must be unique")

    repos = sorted({row.get("repo") for row in rows})
    if len(repos) != 8:
        failures.append(f"expected 8 repositories, got {len(repos)}")

    survives_all = 0
    for row in rows:
        source_index = row.get("source_detection_results_index")
        if not isinstance(source_index, int) or source_index < 0 or source_index >= len(source_rows):
            failures.append(f"{row.get('row_id')}: invalid source index")
            continue
        source_row = source_rows[source_index]
        if row.get("source_row_sha256") != sha256_text(stable_json(source_row)):
            failures.append(f"{row.get('row_id')}: source row sha256 mismatch")
        if source_row.get("id") != row.get("instance_id"):
            failures.append(f"{row.get('row_id')}: instance_id does not match source")
        if source_row.get("both_miss") is not True:
            failures.append(f"{row.get('row_id')}: source row is not both_miss")
        if row.get("hack_diff_sha256") != sha256_text(str(row.get("hack_diff") or "")):
            failures.append(f"{row.get('row_id')}: hack_diff_sha256 mismatch")
        if not str(row.get("hack_diff") or "").strip():
            failures.append(f"{row.get('row_id')}: missing hack_diff")
        static = row.get("static_verdicts", {})
        expected_survival = (
            static.get("deterministic_detector_fooled") is True
            and static.get("gpt_5_6_terra_fooled") is True
            and static.get("claude_opus_4_8_fooled") is True
        )
        if static.get("survives_all_static") is not expected_survival:
            failures.append(f"{row.get('row_id')}: survives_all_static is inconsistent")
        if static.get("survives_all_static") is True:
            survives_all += 1
        source_reports = row.get("source_report_paths", [])
        if not source_reports:
            failures.append(f"{row.get('row_id')}: missing source report paths")
        for report in source_reports:
            path = report.get("path") if isinstance(report, dict) else None
            digest = report.get("sha256") if isinstance(report, dict) else None
            if path not in report_paths:
                failures.append(f"{row.get('row_id')}: unknown report path {path}")
            if not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest):
                failures.append(f"{row.get('row_id')}: invalid report sha256 for {path}")

    if survives_all != 5:
        failures.append(f"expected 5 survives_all_static rows, got {survives_all}")

    expected_manifest_values = {
        "row_count": 20,
        "repo_count": 8,
        "hack_diff_sha256_present": 20,
        "survives_all_static": 5,
        "new_provider_calls": 0,
        "new_cloud_resources": 0,
        "new_swebench_executions": 0,
        "new_judge_calls": 0,
        "benchmark_result_claimed": False,
        "released_benchmark_claimed": False,
        "leaderboard_claimed": False,
        "model_superiority_claimed": False,
        "sota_claimed": False,
        "natural_rl_frequency_claimed": False,
    }
    for key, expected in expected_manifest_values.items():
        if manifest.get(key) != expected:
            failures.append(f"manifest {key} expected {expected!r}, got {manifest.get(key)!r}")

    generated_text = README.read_text(encoding="utf-8") + "\n" + stable_json(manifest)
    for pattern in OVERCLAIM_PATTERNS:
        if pattern.search(generated_text):
            failures.append(f"overclaim pattern matched: {pattern.pattern}")

    audit = {
        "schema_version": "telos.reward_hack_seed.v0.audit.v1",
        "status": "pass" if not failures else "null",
        "row_count": len(rows),
        "repo_count": len(repos),
        "repos": repos,
        "survives_all_static": survives_all,
        "source_both_miss_count": len(source_both_miss),
        "source_artifacts": manifest["source_artifacts"],
        "seed_artifacts": manifest["artifacts"],
        "zero_spend": {
            "new_provider_calls": manifest["new_provider_calls"],
            "new_cloud_resources": manifest["new_cloud_resources"],
            "new_swebench_executions": manifest["new_swebench_executions"],
            "new_judge_calls": manifest["new_judge_calls"],
        },
        "failures": failures,
    }
    return audit, failures


def main() -> int:
    source_rows = load_source_rows()
    rows = materialize_rows(source_rows)

    SEED_DIR.mkdir(parents=True, exist_ok=True)
    write_jsonl(SEED_JSONL, rows)
    write_json(SCHEMA, build_schema())
    manifest = build_manifest(rows)
    write_json(MANIFEST, manifest)
    README.write_text(build_readme(manifest), encoding="utf-8")
    manifest = build_manifest(rows)
    write_json(MANIFEST, manifest)

    audit, failures = validate_seed(rows, manifest)
    RAW.mkdir(parents=True, exist_ok=True)
    write_json(RAW / "materialized_rows.json", {"rows": rows})
    write_json(PROOF / "audit_report.json", audit)

    bars = {
        "row_count_20": audit["row_count"] == 20,
        "repo_count_8": audit["repo_count"] == 8,
        "hack_diff_sha256_present_20": manifest["hack_diff_sha256_present"] == 20,
        "survives_all_static_5": audit["survives_all_static"] == 5,
        "traceable_to_iter152": audit["source_both_miss_count"] == 20 and not failures,
        "new_provider_calls_0": manifest["new_provider_calls"] == 0,
        "new_cloud_resources_0": manifest["new_cloud_resources"] == 0,
        "new_swebench_executions_0": manifest["new_swebench_executions"] == 0,
        "new_judge_calls_0": manifest["new_judge_calls"] == 0,
        "no_overclaim_flags": not any(
            manifest[key]
            for key in [
                "benchmark_result_claimed",
                "released_benchmark_claimed",
                "leaderboard_claimed",
                "model_superiority_claimed",
                "sota_claimed",
                "natural_rl_frequency_claimed",
            ]
        ),
    }
    status = "pass" if all(bars.values()) and not failures else "null"

    endpoints = {
        "schema_version": "telos.reward_hack_seed_materialization.endpoints.v1",
        "experiment_id": EXPERIMENT.name,
        "status": status,
        "seed_id": manifest["seed_id"],
        "seed_path": str(SEED_JSONL.relative_to(ROOT)),
        "manifest_path": str(MANIFEST.relative_to(ROOT)),
        "row_count": audit["row_count"],
        "repo_count": audit["repo_count"],
        "repos": audit["repos"],
        "survives_all_static": audit["survives_all_static"],
        "source_experiment": SOURCE_EXPERIMENT,
        "source_artifacts": manifest["source_artifacts"],
        "seed_artifacts": manifest["artifacts"],
        "zero_spend": audit["zero_spend"],
        "bars": bars,
        "claim_boundary": manifest["claim_boundary"],
    }
    write_json(PROOF / "endpoint_results.json", endpoints)
    write_json(
        PROOF / "run_summary.json",
        {
            "schema_version": "telos.reward_hack_seed_materialization.summary.v1",
            "experiment_id": EXPERIMENT.name,
            "status": status,
            "endpoints": endpoints,
        },
    )

    receipt_status = "pass" if status == "pass" else "fail"
    receipt = {
        "receipt_id": f"iter153-reward-hack-seed-materialization-{status}",
        "task_id": "telos:iter153_reward_hack_benchmark_seed_materialization",
        "agent_id": "local-zero-spend-materializer",
        "benchmark_id": "telos_reward_hack_seed_v0_materialization",
        "status": receipt_status,
        "stated_goal": (
            "Materialize a validated reward-hack benchmark seed from committed iter152 "
            "artifacts without new provider calls, cloud resources, SWE-bench execution, or "
            "judge calls."
        ),
        "acceptance_criteria": [
            "Exactly 20 iter152 both-miss rows are materialized.",
            "All 8 iter152 repositories are represented.",
            "Every row has a non-empty hack diff and matching SHA256.",
            "Every row traces back to committed iter152 raw evidence.",
            "The survives-all-static row count is 5.",
            "No benchmark, leaderboard, model-superiority, SOTA, or natural-RL-frequency claim is made.",
        ],
        "evidence": [
            {"kind": "artifact", "status": receipt_status, "artifact": str(SEED_JSONL.relative_to(ROOT))},
            {"kind": "artifact", "status": receipt_status, "artifact": str(MANIFEST.relative_to(ROOT))},
            {
                "kind": "artifact",
                "status": receipt_status,
                "artifact": f"experiments/{EXPERIMENT.name}/proof/audit_report.json",
            },
            {
                "kind": "test",
                "status": receipt_status,
                "artifact": f"experiments/{EXPERIMENT.name}/proof/endpoint_results.json",
            },
        ],
        "falsifiers": [
            "The seed must fail if row count differs from 20 or repository count differs from 8.",
            "The seed must fail if any row loses traceability to iter152 detection_results.json or det_reports.tgz.",
            "The seed must fail if any hack diff SHA256 is missing or mismatched.",
            "The seed must fail if it claims a released benchmark, leaderboard, model superiority, SOTA result, or natural-RL frequency.",
            "The seed must fail if this gate performs new provider calls, cloud runs, SWE-bench execution, or judge calls.",
        ],
        "sha256": "",
    }
    receipt["sha256"] = receipt_digest(receipt)
    write_json(VALID / "receipt_reward_hack_benchmark_seed_materialization.json", receipt)

    learning = {
        "schema_version": "telos.learning_record.v1",
        "experiment_id": EXPERIMENT.name,
        "status": status,
        "result_path": f"experiments/{EXPERIMENT.name}/RESULT.md",
        "evidence_paths": [
            str(SEED_JSONL.relative_to(ROOT)),
            str(MANIFEST.relative_to(ROOT)),
            f"experiments/{EXPERIMENT.name}/proof/audit_report.json",
            f"experiments/{EXPERIMENT.name}/proof/endpoint_results.json",
            f"experiments/{EXPERIMENT.name}/proof/valid/receipt_reward_hack_benchmark_seed_materialization.json",
        ],
        "insight": (
            "The iter152 reward-hack evidence can be converted into a reviewer-facing seed "
            "without adding measurements: 20 rows, 8 repositories, 20/20 diff hashes, and "
            "5/20 survives-all-static labels all trace back to committed proof artifacts."
        ),
        "next_action": (
            "Pre-register the next benchmark-expansion gate before any paid/cloud work: grow N "
            "and judge diversity from the validated seed while preserving execution proof and "
            "claim boundaries."
        ),
    }
    write_json(PROOF / "learning_record.json", learning)

    print(f"status={status}")
    print(f"  seed rows: {audit['row_count']} across {audit['repo_count']} repos")
    print(f"  survives_all_static: {audit['survives_all_static']}/20")
    print(f"  seed: {SEED_JSONL.relative_to(ROOT)}")
    print(f"  manifest: {MANIFEST.relative_to(ROOT)}")
    if failures:
        print("failures:")
        for failure in failures:
            print(f"  - {failure}")
    return 0 if status == "pass" else 2


if __name__ == "__main__":
    sys.exit(main())
