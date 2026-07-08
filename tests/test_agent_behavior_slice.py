from __future__ import annotations

import pytest

from telos.agent_behavior_slice import (
    AgentBehaviorSliceValidationError,
    validate_agent_behavior_slice,
)


def valid_slice() -> dict:
    return {
        "schema_version": "telos.agent_behavior_slice.v1",
        "slice_id": "codeclash_battlesnake_instant_submit_pvp_slice",
        "status": "selected",
        "selected_candidate": "codeclash_battlesnake_pvp_test_instant_submit",
        "source": {
            "name": "CodeClash",
            "url": "https://github.com/codeclash-ai/codeclash",
            "commit_sha": "381cdfa05a35e8acd35853b9fc7e13005121b127",
            "license_note": "MIT licensed public repository.",
        },
        "config": {
            "path": "configs/test/battlesnake_pvp_test.yaml",
            "game": "BattleSnake",
            "tournament_rounds": 1,
            "sims_per_round": 1,
            "agents": [
                {
                    "name": "p1",
                    "type": "mini",
                    "model_name": "instant_submit",
                    "model_class": "minisweagent.models.test_models.DeterministicModel",
                    "provider_backed": False,
                    "expected_provider_cost": 0,
                    "expected_model_calls_min": 1,
                },
                {"name": "p2", "type": "dummy"},
            ],
        },
        "expected_artifacts": [
            {"kind": "artifact", "name": "codeclash_logs", "purpose": "Preserve run logs."},
            {"kind": "test", "name": "round_result", "purpose": "Parse one game result."},
            {"kind": "diff_scope", "name": "change_records", "purpose": "Record changed files."},
            {"kind": "trajectory", "name": "mini_traj", "purpose": "Capture agent loop."},
            {"kind": "agent_stats", "name": "agent_stats", "purpose": "Verify zero API calls."},
        ],
        "first_run_command": "uv run codeclash run configs/test/battlesnake_pvp_test.yaml -o /tmp/telos-codeclash-agent-behavior-smoke",
        "first_run_falsifier": "The run fails if p1 lacks trajectory or agent_stats evidence.",
        "spend": {"api_calls": False, "cloud": False, "gpu": False, "local_or_github_runner": True},
    }


def test_agent_behavior_slice_validates() -> None:
    selected = validate_agent_behavior_slice(valid_slice())

    assert selected.config_path == "configs/test/battlesnake_pvp_test.yaml"


def test_agent_behavior_slice_requires_deterministic_mini_agent() -> None:
    data = valid_slice()
    data["config"]["agents"][0]["model_class"] = "provider.Model"

    with pytest.raises(AgentBehaviorSliceValidationError, match="deterministic"):
        validate_agent_behavior_slice(data)


def test_agent_behavior_slice_forbids_provider_backed_model() -> None:
    data = valid_slice()
    data["config"]["agents"][0]["provider_backed"] = True

    with pytest.raises(AgentBehaviorSliceValidationError, match="provider_backed"):
        validate_agent_behavior_slice(data)


def test_agent_behavior_slice_forbids_api_spend() -> None:
    data = valid_slice()
    data["spend"]["api_calls"] = True

    with pytest.raises(AgentBehaviorSliceValidationError, match="api_calls"):
        validate_agent_behavior_slice(data)
