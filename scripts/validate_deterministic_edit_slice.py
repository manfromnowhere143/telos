#!/usr/bin/env python3
"""Validate the iter06 deterministic edit slice selection."""

from __future__ import annotations

import json
from pathlib import Path
import re
import sys
from typing import Any


ROOT = Path.cwd()
SLICE = ROOT / "experiments" / "iter06_deterministic_edit_slice" / "proof" / "slice.json"
HEX40 = re.compile(r"^[a-f0-9]{40}$")
REQUIRED_ARTIFACT_KINDS = {
    "agent_stats",
    "artifact",
    "diff_scope",
    "test",
    "trajectory",
}


def fail(message: str) -> int:
    print(f"deterministic edit slice invalid: {message}")
    return 1


def require_mapping(data: dict[str, Any], key: str) -> dict[str, Any]:
    value = data.get(key)
    if not isinstance(value, dict):
        raise ValueError(f"{key} must be an object")
    return value


def main() -> int:
    if not SLICE.exists():
        return fail(f"missing {SLICE}")
    data = json.loads(SLICE.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        return fail("slice root must be an object")

    try:
        if data.get("schema_version") != "telos.deterministic_edit_slice.v1":
            raise ValueError("unexpected schema_version")
        if data.get("status") != "selected":
            raise ValueError("status must be selected")
        if data.get("selected_candidate") != "codeclash_overlay_workspace_python_marker_edit":
            raise ValueError("unexpected selected candidate")

        source = require_mapping(data, "source")
        if not HEX40.match(str(source.get("commit_sha", ""))):
            raise ValueError("source.commit_sha must be a 40-character git SHA")
        if not str(source.get("url", "")).startswith(("https://", "http://")):
            raise ValueError("source.url must be HTTP(S)")

        overlay = require_mapping(data, "overlay")
        overlay_paths = [
            ROOT / str(overlay.get("model_config", "")),
            ROOT / str(overlay.get("run_config", "")),
        ]
        for path in overlay_paths:
            if not path.exists():
                raise ValueError(f"missing overlay file: {path.relative_to(ROOT)}")
        model_text = overlay_paths[0].read_text(encoding="utf-8")
        run_text = overlay_paths[1].read_text(encoding="utf-8")
        for required in [
            "minisweagent.models.test_models.DeterministicModel",
            "telos_marker.py",
            "COMPLETE_TASK_AND_SUBMIT_FINAL_OUTPUT",
        ]:
            if required not in model_text:
                raise ValueError(f"model overlay missing {required}")
        if "telos_edit_battlesnake_marker.yaml" not in run_text:
            raise ValueError("run overlay does not include telos_edit_battlesnake_marker model")

        config = require_mapping(data, "config")
        if config.get("path") != "configs/test/telos_battlesnake_edit_test.yaml":
            raise ValueError("unexpected config path")
        if config.get("game") != "BattleSnake":
            raise ValueError("config.game must be BattleSnake")
        if int(config.get("tournament_rounds", -1)) != 1:
            raise ValueError("config.tournament_rounds must be 1")
        if int(config.get("sims_per_round", -1)) != 1:
            raise ValueError("config.sims_per_round must be 1")
        agents = config.get("agents")
        if not isinstance(agents, list) or len(agents) < 2:
            raise ValueError("config.agents must include mini and dummy")
        mini = next(
            (agent for agent in agents if isinstance(agent, dict) and agent.get("type") == "mini"),
            None,
        )
        if not mini:
            raise ValueError("missing mini agent")
        if mini.get("model_name") != "telos_edit_workspace_marker":
            raise ValueError("mini model must be telos_edit_workspace_marker")
        if mini.get("provider_backed") is not False:
            raise ValueError("mini provider_backed must be false")
        if mini.get("expected_provider_cost") not in (0, 0.0):
            raise ValueError("expected provider cost must be zero")
        if int(mini.get("expected_model_calls_min", 0)) < 2:
            raise ValueError("expected model calls must be at least two")
        expected_files = ["telos_marker.py"]
        if mini.get("expected_modified_files") != expected_files:
            raise ValueError("expected modified files must be the BattleSnake Python file")

        artifact_kinds = {
            artifact.get("kind")
            for artifact in data.get("expected_artifacts", [])
            if isinstance(artifact, dict)
        }
        missing = REQUIRED_ARTIFACT_KINDS - artifact_kinds
        if missing:
            raise ValueError("expected artifacts missing kinds: " + ", ".join(sorted(missing)))

        spend = require_mapping(data, "spend")
        if spend.get("api_calls") is not False:
            raise ValueError("spend.api_calls must be false")
        if spend.get("cloud") is not False:
            raise ValueError("spend.cloud must be false")
        if spend.get("gpu") is not False:
            raise ValueError("spend.gpu must be false")
        if spend.get("local_or_github_runner") is not True:
            raise ValueError("spend.local_or_github_runner must be true")
    except (TypeError, ValueError) as exc:
        return fail(str(exc))

    print("deterministic edit slice valid: selected=codeclash_overlay_workspace_python_marker_edit")
    return 0


if __name__ == "__main__":
    sys.exit(main())
