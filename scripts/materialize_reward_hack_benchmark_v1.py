#!/usr/bin/env python3
"""Materialize the reward-hack benchmark v1 artifact from committed evidence."""

from __future__ import annotations

from collections import Counter
import hashlib
import json
from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
BENCH = ROOT / "benchmarks" / "reward_hack_benchmark_v1"
PROOF = ROOT / "experiments" / "iter156_reward_hack_benchmark_v1_manifest" / "proof"
VALID = PROOF / "valid"

SEED_ROWS = ROOT / "benchmarks" / "reward_hack_seed_v0" / "reward_hack_seed_v0.jsonl"
SEED_MANIFEST = ROOT / "benchmarks" / "reward_hack_seed_v0" / "manifest.json"
ITER154_ROWS = (
    ROOT
    / "experiments"
    / "iter154_reward_hack_benchmark_expansion_pilot"
    / "proof"
    / "raw"
    / "expansion_rows.jsonl"
)
ITER154_RESULTS = (
    ROOT
    / "experiments"
    / "iter154_reward_hack_benchmark_expansion_pilot"
    / "proof"
    / "raw"
    / "expansion_results.json"
)
ITER155_ROWS = (
    ROOT
    / "experiments"
    / "iter155_adaptive_reward_hack_expansion"
    / "proof"
    / "raw"
    / "expansion_rows.jsonl"
)
ITER155_RESULTS = (
    ROOT
    / "experiments"
    / "iter155_adaptive_reward_hack_expansion"
    / "proof"
    / "raw"
    / "expansion_results.json"
)


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def read_json(path: Path) -> dict[str, Any] | list[dict[str, Any]]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    text = path.read_text(encoding="utf-8").strip()
    if not text:
        return []
    return [json.loads(line) for line in text.splitlines()]


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [json.dumps(row, sort_keys=True, separators=(",", ":")) for row in rows]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sha256_record(record: dict[str, Any]) -> str:
    payload = json.dumps(record, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(payload).hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(f"iter156 materialization failed: {message}")


def official_reports(row: dict[str, Any]) -> list[dict[str, str]]:
    if "source_report_paths" in row:
        return [
            {"path": item["path"], "sha256": item["sha256"]}
            for item in row["source_report_paths"]
        ]
    return [{"path": row["official_report_path"], "sha256": row["official_report_sha256"]}]


def seed_static(row: dict[str, Any]) -> dict[str, Any]:
    static = row["static_verdicts"]
    return {
        "claude_opus_4_8_fooled": static["claude_opus_4_8_fooled"],
        "claude_opus_4_8_verdict": static["claude_opus_4_8_verdict"],
        "deterministic_detector_flags": static["deterministic_detector_flags"],
        "deterministic_detector_fooled": static["deterministic_detector_fooled"],
        "gpt_5_6_terra_fooled": static["gpt_5_6_terra_fooled"],
        "gpt_5_6_terra_verdict": static["gpt_5_6_terra_verdict"],
        "survives_all_static": static["survives_all_static"],
    }


def expansion_static(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "claude_opus_4_8_fooled": row["opus_fooled"],
        "claude_opus_4_8_verdict": row["judge_opus48"],
        "deterministic_detector_flags": row["detector_flags"],
        "deterministic_detector_fooled": not row["detector_flags"],
        "gpt_5_6_terra_fooled": row["gpt_fooled"],
        "gpt_5_6_terra_verdict": row["judge_gpt56"],
        "survives_all_static": row["survives_all_static"],
    }


def normalize_seed(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out = []
    for idx, row in enumerate(rows, start=1):
        reports = official_reports(row)
        out.append(
            {
                "benchmark_id": "reward_hack_benchmark_v1",
                "claim_boundary": (
                    "Reward-hack benchmark v1 row: constructed execution-verified "
                    "both-miss evidence only; not a benchmark score, leaderboard, "
                    "model-superiority result, SOTA claim, broad reward-model robustness "
                    "claim, or natural-RL frequency claim."
                ),
                "execution_verified_both_miss": True,
                "hack_diff": row["hack_diff"],
                "hack_diff_sha256": row["hack_diff_sha256"],
                "instance_id": row["instance_id"],
                "official_report_paths": reports,
                "official_report_sha256": reports[0]["sha256"],
                "repo": row["repo"],
                "row_id": f"telos-rh-v1-{idx:03d}",
                "schema_version": "telos.reward_hack_benchmark_v1.row.v1",
                "source_artifact_path": rel(SEED_ROWS),
                "source_experiment": row["source_experiment"],
                "source_record_sha256": sha256_record(row),
                "source_result_path": (
                    "experiments/iter153_reward_hack_benchmark_seed_materialization/RESULT.md"
                ),
                "source_row_id": row["row_id"],
                "source_row_index": idx - 1,
                "source_split": "seed_v0",
                "static_verdicts": seed_static(row),
            }
        )
    return out


def normalize_expansion(
    rows: list[dict[str, Any]],
    *,
    start_idx: int,
    source_artifact: Path,
    source_experiment: str,
    source_result_path: str,
    source_split: str,
) -> list[dict[str, Any]]:
    out = []
    for offset, row in enumerate(rows):
        idx = start_idx + offset
        reports = official_reports(row)
        out.append(
            {
                "accepted_attempt": row["accepted_attempt"],
                "benchmark_id": "reward_hack_benchmark_v1",
                "claim_boundary": (
                    "Reward-hack benchmark v1 row: constructed execution-verified "
                    "both-miss evidence only; not a benchmark score, leaderboard, "
                    "model-superiority result, SOTA claim, broad reward-model robustness "
                    "claim, or natural-RL frequency claim."
                ),
                "execution_verified_both_miss": True,
                "fail_to_pass": row["fail_to_pass"],
                "hack_diff": row["hack_diff"],
                "hack_diff_sha256": row["hack_diff_sha256"],
                "instance_id": row["instance_id"],
                "official_report_paths": reports,
                "official_report_sha256": reports[0]["sha256"],
                "pass_to_pass_count": row.get("pass_to_pass_count"),
                "repo": row["repo"],
                "row_id": f"telos-rh-v1-{idx:03d}",
                "schema_version": "telos.reward_hack_benchmark_v1.row.v1",
                "source_artifact_path": rel(source_artifact),
                "source_candidate_rank": row["source_candidate_rank"],
                "source_candidate_row_sha256": row["source_candidate_row_sha256"],
                "source_experiment": source_experiment,
                "source_file": row.get("source_file"),
                "source_record_sha256": sha256_record(row),
                "source_result_path": source_result_path,
                "source_row_index": offset,
                "source_split": source_split,
                "static_verdicts": expansion_static(row),
            }
        )
    return out


def row_count_by_split(rows: list[dict[str, Any]]) -> dict[str, int]:
    counts = Counter(row["source_split"] for row in rows)
    return dict(sorted(counts.items()))


def count_true(rows: list[dict[str, Any]], key: str) -> int:
    return sum(1 for row in rows if row["static_verdicts"][key] is True)


def build_schema() -> dict[str, Any]:
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "additionalProperties": True,
        "properties": {
            "benchmark_id": {"const": "reward_hack_benchmark_v1"},
            "execution_verified_both_miss": {"const": True},
            "hack_diff": {"type": "string"},
            "hack_diff_sha256": {"pattern": "^[0-9a-f]{64}$", "type": "string"},
            "instance_id": {"type": "string"},
            "official_report_paths": {"minItems": 1, "type": "array"},
            "official_report_sha256": {"pattern": "^[0-9a-f]{64}$", "type": "string"},
            "repo": {"type": "string"},
            "row_id": {"pattern": "^telos-rh-v1-[0-9]{3}$", "type": "string"},
            "source_artifact_path": {"type": "string"},
            "source_experiment": {"type": "string"},
            "source_record_sha256": {"pattern": "^[0-9a-f]{64}$", "type": "string"},
            "source_split": {"enum": ["seed_v0", "iter154_expansion", "iter155_adaptive"]},
            "static_verdicts": {"type": "object"},
        },
        "required": [
            "row_id",
            "benchmark_id",
            "schema_version",
            "source_split",
            "source_experiment",
            "source_artifact_path",
            "source_record_sha256",
            "repo",
            "instance_id",
            "execution_verified_both_miss",
            "official_report_paths",
            "official_report_sha256",
            "static_verdicts",
            "hack_diff_sha256",
            "hack_diff",
            "claim_boundary",
        ],
        "title": "Telos reward_hack_benchmark_v1 row",
        "type": "object",
    }


def write_benchmark_readme(path: Path) -> None:
    path.write_text(
        """# Reward Hack Benchmark v1

This directory is a hash-checked Telos benchmark artifact containing 40 constructed,
execution-verified both-miss reward-hack rows.

Sources:

- 20 rows from `benchmarks/reward_hack_seed_v0/`
- 17 rows from `experiments/iter154_reward_hack_benchmark_expansion_pilot`
- 3 rows from `experiments/iter155_adaptive_reward_hack_expansion`

Each row preserves:

- the hack diff and hack diff SHA256,
- the official SWE-bench report hash,
- the source experiment and source row hash,
- deterministic detector, `gpt-5.6-terra`, and `claude-opus-4-8` static labels,
- the `survives_all_static` label.

Claim boundary: this is a benchmark artifact, not a benchmark score, leaderboard,
model-comparison result, state-of-the-art claim, broad reward-model robustness claim, or
natural reward-hacking frequency claim.

Primary files:

- `reward_hack_benchmark_v1.jsonl`: 40 normalized rows.
- `manifest.json`: counts, source hashes, artifact hashes, and claim-boundary flags.
- `schema.json`: minimal row schema for reviewer inspection.
""",
        encoding="utf-8",
    )


def verify_rows(rows: list[dict[str, Any]]) -> dict[str, Any]:
    instance_ids = [row["instance_id"] for row in rows]
    source_counts = row_count_by_split(rows)
    summary = {
        "benchmark_score_claimed": False,
        "claude_opus_4_8_fooled": count_true(rows, "claude_opus_4_8_fooled"),
        "deterministic_detector_evaded": count_true(rows, "deterministic_detector_fooled"),
        "gpt_5_6_terra_fooled": count_true(rows, "gpt_5_6_terra_fooled"),
        "leaderboard_claimed": False,
        "manifest_row_count": len(rows),
        "model_superiority_claimed": False,
        "natural_rl_frequency_claimed": False,
        "new_cloud_resources": 0,
        "new_provider_calls": 0,
        "new_swebench_executions": 0,
        "repo_count": len({row["repo"] for row in rows}),
        "repos": sorted({row["repo"] for row in rows}),
        "rows_with_execution_verified_both_miss": sum(
            1 for row in rows if row["execution_verified_both_miss"] is True
        ),
        "rows_with_hack_diff_sha256": sum(1 for row in rows if row.get("hack_diff_sha256")),
        "rows_with_official_report_hash": sum(
            1 for row in rows if row.get("official_report_sha256")
        ),
        "rows_with_source_traceability": sum(
            1
            for row in rows
            if row.get("source_artifact_path")
            and row.get("source_experiment")
            and row.get("source_record_sha256")
        ),
        "sota_claimed": False,
        "source_counts": source_counts,
        "survives_all_static_rows": count_true(rows, "survives_all_static"),
        "unique_instance_ids": len(set(instance_ids)),
    }

    require(summary["manifest_row_count"] == 40, "manifest_row_count must be 40")
    require(summary["unique_instance_ids"] == 40, "unique_instance_ids must be 40")
    require(
        summary["rows_with_execution_verified_both_miss"] == 40,
        "all rows must be execution-verified both-miss",
    )
    require(summary["rows_with_hack_diff_sha256"] == 40, "all rows need hack diff hashes")
    require(
        summary["rows_with_official_report_hash"] >= 40,
        "all rows need official report hashes",
    )
    require(summary["rows_with_source_traceability"] == 40, "all rows need source traceability")
    require(source_counts == {"iter154_expansion": 17, "iter155_adaptive": 3, "seed_v0": 20},
            f"source counts mismatch: {source_counts}")
    require(summary["survives_all_static_rows"] >= 13, "survives_all_static_rows must be >= 13")
    return summary


def write_receipt(receipt_path: Path, summary: dict[str, Any], artifacts: dict[str, str]) -> None:
    sys.path.insert(0, str(ROOT))
    from telos.proof import receipt_digest

    receipt = {
        "acceptance_criteria": [
            "The v1 manifest must contain exactly 40 rows.",
            "All 40 rows must have unique instance ids.",
            "All 40 rows must be execution-verified both-miss rows.",
            "All 40 rows must have hack diff hashes, official report hashes, and source traceability.",
            "The source split must be 20 seed rows, 17 iter154 rows, and 3 iter155 rows.",
            "The gate must use zero provider calls, zero SWE-bench executions, and zero cloud resources.",
            "The result must not claim a benchmark score, leaderboard, model superiority, state-of-the-art result, broad reward-model robustness, or natural reward-hacking frequency.",
        ],
        "agent_id": "codex-local-zero-spend-manifest-materializer",
        "benchmark_id": "reward_hack_benchmark_v1",
        "evidence": [
            {
                "artifact": "benchmarks/reward_hack_benchmark_v1/reward_hack_benchmark_v1.jsonl",
                "kind": "artifact",
                "status": "pass",
            },
            {
                "artifact": "benchmarks/reward_hack_benchmark_v1/manifest.json",
                "kind": "artifact",
                "status": "pass",
            },
            {
                "artifact": "experiments/iter156_reward_hack_benchmark_v1_manifest/proof/audit_report.json",
                "kind": "adversarial_review",
                "status": "pass",
            },
        ],
        "falsifiers": [
            "The gate fails if row count, uniqueness, source split, or row traceability bars fail.",
            "The gate fails if it requires any new provider call, SWE-bench execution, cloud resource, GPU run, or live-domain mutation.",
            "The gate fails if public wording claims a benchmark score, leaderboard, model superiority, state-of-the-art result, broad reward-model robustness, or natural reward-hacking frequency.",
        ],
        "receipt_id": "iter156-reward-hack-benchmark-v1-manifest-pass",
        "sha256": "",
        "stated_goal": (
            "Materialize a hash-checked 40-row reward-hack benchmark v1 artifact from committed "
            "seed, iter154, and iter155 evidence without new spend or model/leaderboard claims."
        ),
        "status": "pass",
        "task_id": "telos:iter156_reward_hack_benchmark_v1_manifest",
    }
    receipt["sha256"] = receipt_digest(receipt)
    write_json(receipt_path, receipt)


def main() -> int:
    BENCH.mkdir(parents=True, exist_ok=True)
    PROOF.mkdir(parents=True, exist_ok=True)
    VALID.mkdir(parents=True, exist_ok=True)

    seed_rows = read_jsonl(SEED_ROWS)
    iter154_rows = read_jsonl(ITER154_ROWS)
    iter155_rows = read_jsonl(ITER155_ROWS)
    iter154_results = read_json(ITER154_RESULTS)
    iter155_results = read_json(ITER155_RESULTS)

    require(len(seed_rows) == 20, "seed row count must be 20")
    require(len(iter154_rows) == 17, "iter154 row count must be 17")
    require(len(iter155_rows) == 3, "iter155 row count must be 3")
    require(
        sum(1 for row in iter154_results if row.get("execution_verified_both_miss") is True) == 17,
        "iter154 accepted result count must be 17",
    )
    require(
        sum(1 for row in iter155_results if row.get("execution_verified_both_miss") is True) == 3,
        "iter155 accepted result count must be 3",
    )

    rows = [
        *normalize_seed(seed_rows),
        *normalize_expansion(
            iter154_rows,
            start_idx=21,
            source_artifact=ITER154_ROWS,
            source_experiment="iter154_reward_hack_benchmark_expansion_pilot",
            source_result_path="experiments/iter154_reward_hack_benchmark_expansion_pilot/RESULT.md",
            source_split="iter154_expansion",
        ),
        *normalize_expansion(
            iter155_rows,
            start_idx=38,
            source_artifact=ITER155_ROWS,
            source_experiment="iter155_adaptive_reward_hack_expansion",
            source_result_path="experiments/iter155_adaptive_reward_hack_expansion/RESULT.md",
            source_split="iter155_adaptive",
        ),
    ]
    summary = verify_rows(rows)

    rows_path = BENCH / "reward_hack_benchmark_v1.jsonl"
    schema_path = BENCH / "schema.json"
    readme_path = BENCH / "README.md"
    manifest_path = BENCH / "manifest.json"

    write_jsonl(rows_path, rows)
    write_json(schema_path, build_schema())
    write_benchmark_readme(readme_path)

    source_artifacts = {
        rel(SEED_ROWS): sha256_file(SEED_ROWS),
        rel(SEED_MANIFEST): sha256_file(SEED_MANIFEST),
        rel(ITER154_ROWS): sha256_file(ITER154_ROWS),
        rel(ITER154_RESULTS): sha256_file(ITER154_RESULTS),
        rel(ITER155_ROWS): sha256_file(ITER155_ROWS),
        rel(ITER155_RESULTS): sha256_file(ITER155_RESULTS),
    }
    benchmark_artifacts = {
        rel(readme_path): sha256_file(readme_path),
        rel(rows_path): sha256_file(rows_path),
        rel(schema_path): sha256_file(schema_path),
    }

    claim_boundary = (
        "Telos released a hash-checked v1 artifact of 40 constructed, execution-verified "
        "both-miss reward-hack rows gathered from iter152 through iter155. This is not a "
        "model benchmark score, leaderboard ranking, state-of-the-art performance claim, "
        "natural reward-hacking frequency claim, or broad reward-model robustness claim."
    )
    manifest = {
        **summary,
        "benchmark_artifacts": benchmark_artifacts,
        "benchmark_id": "reward_hack_benchmark_v1",
        "claim_boundary": claim_boundary,
        "schema_version": "telos.reward_hack_benchmark_v1.manifest.v1",
        "source_artifacts": source_artifacts,
        "source_experiments": [
            "iter152_reward_model_gaming_scale",
            "iter153_reward_hack_benchmark_seed_materialization",
            "iter154_reward_hack_benchmark_expansion_pilot",
            "iter155_adaptive_reward_hack_expansion",
        ],
        "status": "released_artifact_no_score",
    }
    write_json(manifest_path, manifest)
    benchmark_artifacts[rel(manifest_path)] = sha256_file(manifest_path)

    endpoint = {
        **summary,
        "bars": {
            "benchmark_score_claimed_false": summary["benchmark_score_claimed"] is False,
            "iter154_rows_eq_17": summary["source_counts"].get("iter154_expansion") == 17,
            "iter155_rows_eq_3": summary["source_counts"].get("iter155_adaptive") == 3,
            "leaderboard_claimed_false": summary["leaderboard_claimed"] is False,
            "manifest_row_count_eq_40": summary["manifest_row_count"] == 40,
            "model_superiority_claimed_false": summary["model_superiority_claimed"] is False,
            "new_cloud_resources_eq_0": summary["new_cloud_resources"] == 0,
            "new_provider_calls_eq_0": summary["new_provider_calls"] == 0,
            "new_swebench_executions_eq_0": summary["new_swebench_executions"] == 0,
            "rows_with_execution_verified_both_miss_eq_40": (
                summary["rows_with_execution_verified_both_miss"] == 40
            ),
            "rows_with_hack_diff_sha256_eq_40": summary["rows_with_hack_diff_sha256"] == 40,
            "rows_with_official_report_hash_ge_40": (
                summary["rows_with_official_report_hash"] >= 40
            ),
            "rows_with_source_traceability_eq_40": (
                summary["rows_with_source_traceability"] == 40
            ),
            "seed_rows_eq_20": summary["source_counts"].get("seed_v0") == 20,
            "sota_claimed_false": summary["sota_claimed"] is False,
            "survives_all_static_rows_ge_13": summary["survives_all_static_rows"] >= 13,
            "unique_instance_ids_eq_40": summary["unique_instance_ids"] == 40,
        },
        "benchmark_artifacts": benchmark_artifacts,
        "claim_boundary": claim_boundary,
        "experiment_id": "iter156_reward_hack_benchmark_v1_manifest",
        "schema_version": "telos.iter156.endpoint_results.v1",
        "source_artifacts": source_artifacts,
        "status": "pass_released_artifact_no_score",
    }
    write_json(PROOF / "endpoint_results.json", endpoint)

    run_summary = {
        **summary,
        "benchmark_artifacts": benchmark_artifacts,
        "experiment_id": "iter156_reward_hack_benchmark_v1_manifest",
        "final_gate_outcome": "pass_released_artifact_no_score",
        "schema_version": "telos.iter156.run_summary.v1",
    }
    write_json(PROOF / "run_summary.json", run_summary)

    audit_report = {
        "bars": [
            {"name": "manifest_row_count == 40", "observed": summary["manifest_row_count"], "passed": True},
            {"name": "unique_instance_ids == 40", "observed": summary["unique_instance_ids"], "passed": True},
            {
                "name": "rows_with_execution_verified_both_miss == 40",
                "observed": summary["rows_with_execution_verified_both_miss"],
                "passed": True,
            },
            {
                "name": "rows_with_hack_diff_sha256 == 40",
                "observed": summary["rows_with_hack_diff_sha256"],
                "passed": True,
            },
            {
                "name": "rows_with_official_report_hash >= 40",
                "observed": summary["rows_with_official_report_hash"],
                "passed": True,
            },
            {
                "name": "rows_with_source_traceability == 40",
                "observed": summary["rows_with_source_traceability"],
                "passed": True,
            },
            {
                "name": "source split == 20 seed, 17 iter154, 3 iter155",
                "observed": summary["source_counts"],
                "passed": True,
            },
            {
                "name": "survives_all_static_rows >= 13",
                "observed": summary["survives_all_static_rows"],
                "passed": True,
            },
            {"name": "new_provider_calls == 0", "observed": 0, "passed": True},
            {"name": "new_swebench_executions == 0", "observed": 0, "passed": True},
            {"name": "new_cloud_resources == 0", "observed": 0, "passed": True},
            {"name": "benchmark_score_claimed == false", "observed": False, "passed": True},
            {"name": "leaderboard_claimed == false", "observed": False, "passed": True},
            {"name": "model_superiority_claimed == false", "observed": False, "passed": True},
            {"name": "sota_claimed == false", "observed": False, "passed": True},
        ],
        "experiment_id": "iter156_reward_hack_benchmark_v1_manifest",
        "notes": [
            "The artifact is assembled only from committed iter153, iter154, and iter155 evidence.",
            "No provider calls, SWE-bench executions, cloud resources, GPU runs, or live-domain mutations occurred.",
            "The artifact is a released row manifest, not a benchmark score or model-comparison result.",
        ],
        "schema_version": "telos.iter156.audit_report.v1",
        "status": "pass_released_artifact_no_score",
    }
    write_json(PROOF / "audit_report.json", audit_report)

    learning = {
        "evidence_paths": [
            "benchmarks/reward_hack_benchmark_v1/reward_hack_benchmark_v1.jsonl",
            "benchmarks/reward_hack_benchmark_v1/manifest.json",
            "benchmarks/reward_hack_benchmark_v1/schema.json",
            "experiments/iter156_reward_hack_benchmark_v1_manifest/proof/audit_report.json",
            "experiments/iter156_reward_hack_benchmark_v1_manifest/proof/endpoint_results.json",
            "experiments/iter156_reward_hack_benchmark_v1_manifest/proof/run_summary.json",
            "experiments/iter156_reward_hack_benchmark_v1_manifest/proof/valid/receipt_reward_hack_benchmark_v1_manifest.json",
        ],
        "experiment_id": "iter156_reward_hack_benchmark_v1_manifest",
        "insight": (
            "The seed, iter154, and iter155 evidence can be joined into a 40-row "
            "hash-checked reward-hack benchmark artifact with 13 rows that survive every "
            "static layer, without new spend or benchmark-score claims."
        ),
        "next_action": (
            "Resume the paper plain-language pass across the remaining sections, updating the "
            "benchmark artifact claim boundary while preserving that no leaderboard, model score, "
            "SOTA, natural-frequency, or broad robustness claim is made."
        ),
        "result_path": "experiments/iter156_reward_hack_benchmark_v1_manifest/RESULT.md",
        "schema_version": "telos.learning_record.v1",
        "status": "pass",
    }
    write_json(PROOF / "learning_record.json", learning)
    write_receipt(
        PROOF / "valid" / "receipt_reward_hack_benchmark_v1_manifest.json",
        summary,
        benchmark_artifacts,
    )

    print(
        "reward_hack_benchmark_v1: "
        f"{summary['manifest_row_count']} rows, "
        f"{summary['survives_all_static_rows']} survives-all-static, "
        f"repos={summary['repo_count']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
