"""Agent-behavior slice validation."""

from __future__ import annotations

from dataclasses import dataclass
import json
import re
from pathlib import Path
from typing import Any


class AgentBehaviorSliceValidationError(ValueError):
    """Raised when an agent-behavior slice is malformed."""


HEX40 = re.compile(r"^[a-f0-9]{40}$")
REQUIRED_ARTIFACT_KINDS = {
    "agent_stats",
    "artifact",
    "diff_scope",
    "test",
    "trajectory",
}


@dataclass(frozen=True)
class AgentBehaviorSlice:
    """Frozen first agent-behavior slice."""

    slice_id: str
    selected_candidate: str
    config_path: str
    first_run_command: str


def _require_mapping(data: dict[str, Any], key: str) -> dict[str, Any]:
    value = data.get(key)
    if not isinstance(value, dict):
        raise AgentBehaviorSliceValidationError(f"{key} must be an object")
    return value


def _require_nonempty_string(data: dict[str, Any], key: str) -> str:
    value = data.get(key)
    if not isinstance(value, str) or not value.strip():
        raise AgentBehaviorSliceValidationError(f"{key} must be a non-empty string")
    return value


def validate_agent_behavior_slice(data: dict[str, Any]) -> AgentBehaviorSlice:
    """Validate an agent-behavior slice selection."""

    for key in [
        "schema_version",
        "slice_id",
        "status",
        "selected_candidate",
        "source",
        "config",
        "expected_artifacts",
        "first_run_command",
        "first_run_falsifier",
        "spend",
    ]:
        if key not in data:
            raise AgentBehaviorSliceValidationError(f"missing field: {key}")

    if data["schema_version"] != "telos.agent_behavior_slice.v1":
        raise AgentBehaviorSliceValidationError(
            "schema_version must be telos.agent_behavior_slice.v1"
        )
    if data["status"] != "selected":
        raise AgentBehaviorSliceValidationError("status must be selected")

    slice_id = _require_nonempty_string(data, "slice_id")
    selected_candidate = _require_nonempty_string(data, "selected_candidate")
    first_run_command = _require_nonempty_string(data, "first_run_command")
    _require_nonempty_string(data, "first_run_falsifier")

    source = _require_mapping(data, "source")
    _require_nonempty_string(source, "name")
    commit_sha = _require_nonempty_string(source, "commit_sha")
    if not HEX40.match(commit_sha):
        raise AgentBehaviorSliceValidationError("source.commit_sha must be a 40-character git SHA")
    source_url = _require_nonempty_string(source, "url")
    if not source_url.startswith(("https://", "http://")):
        raise AgentBehaviorSliceValidationError("source.url must be HTTP(S)")
    _require_nonempty_string(source, "license_note")

    config = _require_mapping(data, "config")
    config_path = _require_nonempty_string(config, "path")
    if not config_path.startswith("configs/test/"):
        raise AgentBehaviorSliceValidationError("config.path must use CodeClash configs/test")
    if int(config.get("tournament_rounds", -1)) != 1:
        raise AgentBehaviorSliceValidationError("config.tournament_rounds must be 1")
    if int(config.get("sims_per_round", -1)) > 10:
        raise AgentBehaviorSliceValidationError("config.sims_per_round must stay <= 10")
    if config.get("game") != "BattleSnake":
        raise AgentBehaviorSliceValidationError("config.game must be BattleSnake")

    agents = config.get("agents")
    if not isinstance(agents, list) or len(agents) < 2:
        raise AgentBehaviorSliceValidationError("config.agents must contain at least two agents")
    agent_types = {agent.get("type") for agent in agents if isinstance(agent, dict)}
    if "mini" not in agent_types or "dummy" not in agent_types:
        raise AgentBehaviorSliceValidationError("config.agents must include mini and dummy")
    mini_agents = [agent for agent in agents if isinstance(agent, dict) and agent.get("type") == "mini"]
    if not mini_agents:
        raise AgentBehaviorSliceValidationError("missing mini agent")
    mini = mini_agents[0]
    if mini.get("model_name") != "instant_submit":
        raise AgentBehaviorSliceValidationError("mini agent must use instant_submit")
    if mini.get("model_class") != "minisweagent.models.test_models.DeterministicModel":
        raise AgentBehaviorSliceValidationError("mini agent must use deterministic model class")
    if mini.get("provider_backed") is not False:
        raise AgentBehaviorSliceValidationError("mini agent provider_backed must be false")
    if mini.get("expected_provider_cost") not in (0, 0.0):
        raise AgentBehaviorSliceValidationError("mini agent expected_provider_cost must be 0")
    if int(mini.get("expected_model_calls_min", 0)) < 1:
        raise AgentBehaviorSliceValidationError(
            "mini agent expected_model_calls_min must be at least 1"
        )

    expected_artifacts = data["expected_artifacts"]
    if not isinstance(expected_artifacts, list) or not expected_artifacts:
        raise AgentBehaviorSliceValidationError("expected_artifacts must be a non-empty list")
    kinds = set()
    for idx, artifact in enumerate(expected_artifacts):
        if not isinstance(artifact, dict):
            raise AgentBehaviorSliceValidationError(f"expected_artifacts[{idx}] must be an object")
        kind = _require_nonempty_string(artifact, "kind")
        _require_nonempty_string(artifact, "name")
        _require_nonempty_string(artifact, "purpose")
        kinds.add(kind)
    missing = REQUIRED_ARTIFACT_KINDS - kinds
    if missing:
        raise AgentBehaviorSliceValidationError(
            "expected_artifacts missing kinds: " + ", ".join(sorted(missing))
        )

    spend = _require_mapping(data, "spend")
    if spend.get("api_calls") is not False:
        raise AgentBehaviorSliceValidationError("spend.api_calls must be false")
    if spend.get("cloud") is not False:
        raise AgentBehaviorSliceValidationError("spend.cloud must be false")
    if spend.get("gpu") is not False:
        raise AgentBehaviorSliceValidationError("spend.gpu must be false")
    if spend.get("local_or_github_runner") is not True:
        raise AgentBehaviorSliceValidationError("spend.local_or_github_runner must be true")

    return AgentBehaviorSlice(
        slice_id=slice_id,
        selected_candidate=selected_candidate,
        config_path=config_path,
        first_run_command=first_run_command,
    )


def load_agent_behavior_slice(path: str | Path) -> AgentBehaviorSlice:
    """Load and validate an agent-behavior slice selection."""

    raw = Path(path).read_text(encoding="utf-8")
    data = json.loads(raw)
    if not isinstance(data, dict):
        raise AgentBehaviorSliceValidationError("agent-behavior slice root must be an object")
    return validate_agent_behavior_slice(data)
