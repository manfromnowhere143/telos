from __future__ import annotations

import pytest

from telos.public_slice import PublicSliceValidationError, validate_public_slice


def valid_slice() -> dict:
    return {
        "schema_version": "telos.public_slice.v1",
        "slice_id": "codeclash_dummy_swebench_receipt_slice",
        "status": "selected",
        "target_family": "telos_codeclash_swebench_overlay",
        "selected_candidate": "codeclash_dummy_tournament_plus_swebench_receipt_fields",
        "sources": [
            {
                "name": "CodeClash",
                "url": "https://github.com/codeclash-ai/codeclash",
                "commit_sha": "381cdfa05a35e8acd35853b9fc7e13005121b127",
                "license_note": "MIT licensed public repository.",
            },
            {
                "name": "SWE-bench Verified",
                "url": "https://huggingface.co/datasets/SWE-bench/SWE-bench_Verified",
                "commit_sha": "91aa3ed51b709be6457e12d00300a6a596d4c6a3",
                "license_note": "Public and ungated dataset; source repository licenses remain separate.",
            },
        ],
        "task": {
            "task_id": "codeclash:configs/test/dummy.yaml",
            "kind": "codeclash_tournament_smoke",
            "primary_commit_sha": "381cdfa05a35e8acd35853b9fc7e13005121b127",
            "public_config": "configs/test/dummy.yaml",
            "receipt_substrate": "swebench_verified_fields",
            "supporting_task": {
                "repo": "astropy/astropy",
                "instance_id": "astropy__astropy-12907",
                "row_idx": 0,
                "base_commit": "d16bfe05a744909de4b27f5875fe0d4ed41ce607",
                "environment_setup_commit": "298ccb478e6bf092953bca67a3d29dc6c35f6752",
                "difficulty": "15 min - 1 hour",
                "fail_to_pass": [
                    "astropy/modeling/tests/test_separable.py::test_separable[compound_model6-result6]"
                ],
                "pass_to_pass_count": 13,
                "patch_sha256": "0f3e44432ed8540e9526edff4f83793948a2f139fc3971b67c30043c1eb7964a",
                "test_patch_sha256": "5ef90b640ffce4590bb61ef2ea0e3256416dddf41b45bf4f2c3610a6e8c53718",
                "problem_statement_sha256": "c01334ec1b21a089c650cf2e7b96ab974469076bf1260d23885799e1f0a7551f",
            },
        },
        "expected_artifacts": [
            {"kind": "artifact", "name": "codeclash_logs", "purpose": "Preserve tournament logs."},
            {"kind": "test", "name": "arena_result", "purpose": "Parse round scores and winner."},
            {"kind": "diff_scope", "name": "agent_workspace", "purpose": "Record changed files."},
        ],
        "first_run_command": "uv run codeclash run configs/test/dummy.yaml -o /tmp/telos-codeclash-dummy-smoke",
        "first_run_falsifier": "The slice fails if the CodeClash dummy tournament cannot produce logs and parsed round results under a responsive Docker engine.",
        "spend": {"api_calls": False, "cloud": False, "gpu": False, "local_only": True},
    }


def test_public_slice_validates() -> None:
    public_slice = validate_public_slice(valid_slice())

    assert public_slice.task_id == "codeclash:configs/test/dummy.yaml"


def test_public_slice_requires_test_artifact() -> None:
    data = valid_slice()
    data["expected_artifacts"] = [
        artifact for artifact in data["expected_artifacts"] if artifact["kind"] != "test"
    ]

    with pytest.raises(PublicSliceValidationError, match="test"):
        validate_public_slice(data)


def test_public_slice_forbids_cloud_spend() -> None:
    data = valid_slice()
    data["spend"]["cloud"] = True

    with pytest.raises(PublicSliceValidationError, match="cloud"):
        validate_public_slice(data)
