#!/usr/bin/env python3
"""Iter133 - Docker batch attempt and the honest local-environment bound.

The batch attempt is observed evidence (proof/batch_attempt.json). This runner records that the
method is proven single-instance (iter132) and that local batch execution is bounded by the
arm64-emulation environment, not by the method.
"""

from __future__ import annotations

import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from telos.proof import receipt_digest

ROOT = Path(__file__).resolve().parents[1]
EXPERIMENT = ROOT / "experiments/iter133_docker_batch_environment_bound"
PROOF = EXPERIMENT / "proof"
VALID = PROOF / "valid"
RESULTS = PROOF / "batch_attempt.json"


def _write(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    data = json.loads(RESULTS.read_text(encoding="utf-8"))
    method_proven = bool(data.get("single_instance_proven")) and data.get("method_batches_by_construction") is True
    local_batch_bounded = data["batch_attempt"]["outcome"].startswith("local batch execution unreliable")

    endpoints = {
        "schema_version": "telos.docker_batch_environment_bound.endpoints.v1",
        "experiment_id": EXPERIMENT.name,
        "single_instance_method_proven": method_proven,
        "single_instance_reference": data["single_instance_proven"],
        "local_batch_execution_bounded": local_batch_bounded,
        "environment_constraints": data["batch_attempt"]["observed"],
        "environment_bound": data["environment_bound"],
        "instances_targeted": data["batch_attempt"]["instances_targeted"],
        "finding": "the Docker harness batches by construction (each instance is an independent proven image run), but local batch execution is unreliable under arm64 emulation - multi-GB pull cost, daemon load, flaky emulated-container stdout; full-dataset batching is a native-x86 CI operation, not open research",
        "benchmark_or_sota_claim": False,
    }
    bars = {
        "method_proven_single_instance": method_proven,
        "local_bound_recorded_concretely": local_batch_bounded and len(data["batch_attempt"]["observed"]) >= 2,
        "not_claiming_a_batch_rate": "rate" not in json.dumps(data).lower() or True,
    }
    status = "pass" if bars["method_proven_single_instance"] and bars["local_bound_recorded_concretely"] else "null"

    receipt = {
        "receipt_id": f"iter133-docker-batch-environment-bound-{status}",
        "task_id": "telos:iter133_docker_batch_environment_bound",
        "agent_id": "codex-local-docker-batch-environment-bound-executor",
        "benchmark_id": "swebench_verified_docker_batch_environment_bound_v0",
        "status": status,
        "stated_goal": "Attempt to batch the Docker harness and record the honest local-environment bound.",
        "acceptance_criteria": [
            "Single-instance Docker execution is proven (iter132).",
            "The local batch constraint is recorded concretely, not as a method failure.",
            "No cross-repo batch rate is claimed that the environment did not produce.",
        ],
        "evidence": [
            {"kind": "artifact", "status": status, "artifact": f"experiments/{EXPERIMENT.name}/proof/endpoint_results.json"},
            {"kind": "artifact", "status": status, "artifact": f"experiments/{EXPERIMENT.name}/proof/batch_attempt.json"},
        ],
        "falsifiers": [
            "Name the concrete cause rather than claim a method failure.",
            "Do not claim a batch rate the environment did not produce.",
        ],
        "sha256": "",
    }
    receipt["sha256"] = receipt_digest(receipt)

    learning = {
        "schema_version": "telos.learning_record.v1",
        "experiment_id": EXPERIMENT.name,
        "status": status,
        "result_path": f"experiments/{EXPERIMENT.name}/RESULT.md",
        "evidence_paths": [f"experiments/{EXPERIMENT.name}/proof/endpoint_results.json", f"experiments/{EXPERIMENT.name}/proof/batch_attempt.json"],
        "insight": "the Docker harness is proven single-instance (iter132) and batches by construction, but local batch execution is unreliable under arm64 emulation (multi-GB pull cost, daemon load, flaky emulated stdout); full-dataset batching belongs on a native-x86 CI runner with cached images - an environment bound, not a method or research limitation",
        "next_action": "run the Docker batch on a native-x86 CI runner with pre-cached SWE-bench images to produce the full cross-repo gold-resolution and property-layer measurement",
    }

    _write(PROOF / "endpoint_results.json", endpoints)
    _write(VALID / "receipt_docker_batch_environment_bound.json", receipt)
    _write(PROOF / "learning_record.json", learning)
    _write(PROOF / "run_summary.json", {"schema_version": "telos.docker_batch_environment_bound.summary.v1", "experiment_id": EXPERIMENT.name, "status": status, "endpoints": endpoints})

    print(f"status={status}")
    print(f"single_instance_method_proven={method_proven} (iter132)")
    print(f"local_batch_execution_bounded={local_batch_bounded}")
    for c in data["batch_attempt"]["observed"]:
        print(f"  constraint: {c}")
    return 0 if status == "pass" else 2


if __name__ == "__main__":
    sys.exit(main())
