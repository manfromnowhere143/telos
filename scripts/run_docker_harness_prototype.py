#!/usr/bin/env python3
"""Iter132 - the Docker harness runs a natively-blocked instance's hidden test in a pinned Python 3.9.

The container run is observed evidence (proof/docker_run_results.json). This runner asserts the bound
is closed for this instance and records it.
"""

from __future__ import annotations

import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from telos.proof import receipt_digest

ROOT = Path(__file__).resolve().parents[1]
EXPERIMENT = ROOT / "experiments/iter132_docker_harness_prototype"
PROOF = EXPERIMENT / "proof"
VALID = PROOF / "valid"
RESULTS = PROOF / "docker_run_results.json"


def _write(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    data = json.loads(RESULTS.read_text(encoding="utf-8"))
    dh = data["docker_harness"]
    pinned = data["pinned_environment"]
    base_fails = dh["base_plus_hidden_test"].startswith("FAIL")
    gold_passes = dh["gold_plus_hidden_test"].startswith("PASS")
    provides_old_python = pinned["collections_Mapping_importable"] is True and pinned["python"].startswith("3.9")

    endpoints = {
        "schema_version": "telos.docker_harness_prototype.endpoints.v1",
        "experiment_id": EXPERIMENT.name,
        "instance_id": data["instance_id"],
        "image": data["image"],
        "native_harness_status": data["native_harness_status"],
        "pinned_python": pinned["python"],
        "collections_mapping_importable": pinned["collections_Mapping_importable"],
        "docker_base_fails": base_fails,
        "docker_gold_passes": gold_passes,
        "environment_fidelity_bound_closed_for_instance": provides_old_python and base_fails and gold_passes,
        "finding": data["finding"],
        "scope": "one natively-blocked instance; full-dataset Docker coverage is engineering, not open research",
        "benchmark_or_sota_claim": False,
    }
    bars = {
        "docker_provides_python_native_lacked": provides_old_python,
        "base_fails_gold_passes_in_container": base_fails and gold_passes,
    }
    status = "pass" if all(bars.values()) else "null"

    receipt = {
        "receipt_id": f"iter132-docker-harness-prototype-{status}",
        "task_id": "telos:iter132_docker_harness_prototype",
        "agent_id": "codex-local-docker-harness-prototype-executor",
        "benchmark_id": "swebench_verified_docker_harness_prototype_v0",
        "status": status,
        "stated_goal": "Run a natively-blocked instance's real hidden test inside the official SWE-bench Docker image.",
        "acceptance_criteria": [
            "The container provides a Python the native harness lacks (3.9 with collections.Mapping).",
            "The real hidden test fails on base and passes on gold inside the container.",
            "The claim is one instance, not full-dataset coverage.",
        ],
        "evidence": [
            {"kind": "artifact", "status": status, "artifact": f"experiments/{EXPERIMENT.name}/proof/endpoint_results.json"},
            {"kind": "artifact", "status": status, "artifact": f"experiments/{EXPERIMENT.name}/proof/docker_run_results.json"},
        ],
        "falsifiers": [
            "Record the concrete blocker if the image does not pull or run.",
            "Record it if base does not fail or gold does not pass inside the container.",
        ],
        "sha256": "",
    }
    receipt["sha256"] = receipt_digest(receipt)

    learning = {
        "schema_version": "telos.learning_record.v1",
        "experiment_id": EXPERIMENT.name,
        "status": status,
        "result_path": f"experiments/{EXPERIMENT.name}/RESULT.md",
        "evidence_paths": [f"experiments/{EXPERIMENT.name}/proof/endpoint_results.json", f"experiments/{EXPERIMENT.name}/proof/docker_run_results.json"],
        "insight": "the official SWE-bench Docker image ran a natively-blocked instance's real hidden test in a pinned Python 3.9 environment (base fails with the real bug, gold passes), closing the environment-fidelity bound in practice for this instance; full-dataset coverage is now engineering, not open research",
        "next_action": "batch the Docker harness across the environment-fidelity-blocked instances and route symbolic-capable functions to symbolic property evaluation, to re-measure the property layer at full cross-repo scale",
    }

    _write(PROOF / "endpoint_results.json", endpoints)
    _write(VALID / "receipt_docker_harness_prototype.json", receipt)
    _write(PROOF / "learning_record.json", learning)
    _write(PROOF / "run_summary.json", {"schema_version": "telos.docker_harness_prototype.summary.v1", "experiment_id": EXPERIMENT.name, "status": status, "endpoints": endpoints})

    print(f"status={status}")
    print(f"instance={data['instance_id']} pinned_python={pinned['python']} (native lacked it)")
    print(f"docker: base={'FAIL' if base_fails else '?'} gold={'PASS' if gold_passes else '?'}")
    print(f"environment_fidelity_bound_closed_for_instance={endpoints['environment_fidelity_bound_closed_for_instance']}")
    return 0 if status == "pass" else 2


if __name__ == "__main__":
    sys.exit(main())
