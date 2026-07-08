#!/usr/bin/env python3
"""Validate the iter08 provider-model pilot selection."""

from __future__ import annotations

import json
from pathlib import Path
import re
import sys
from typing import Any


ROOT = Path.cwd()
PROOF = ROOT / "experiments" / "iter08_provider_model_pilot_slice" / "proof"
SELECTED = PROOF / "selected_pilot.json"
SCORECARD = PROOF / "scorecard.json"
PREFLIGHT = PROOF / "preflight.json"
SOURCES = PROOF / "sources.md"
HEX40 = re.compile(r"^[a-f0-9]{40}$")
EXPECTED_PILOT = "vertex_gemini_3_1_pro_customtools_codeclash_micro_edit"


def fail(message: str) -> int:
    print(f"provider model pilot slice invalid: {message}")
    return 1


def load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path.relative_to(ROOT)} root must be an object")
    return data


def require_mapping(data: dict[str, Any], key: str) -> dict[str, Any]:
    value = data.get(key)
    if not isinstance(value, dict):
        raise ValueError(f"{key} must be an object")
    return value


def validate_selected(data: dict[str, Any]) -> None:
    if data.get("schema_version") != "telos.provider_model_pilot_slice.v1":
        raise ValueError("unexpected selected_pilot schema_version")
    if data.get("status") != "selected":
        raise ValueError("selected pilot status must be selected")
    if data.get("pilot_id") != EXPECTED_PILOT:
        raise ValueError("unexpected pilot_id")

    provider = require_mapping(data, "provider")
    if provider.get("name") != "Google Vertex AI":
        raise ValueError("provider must be Google Vertex AI")
    if provider.get("model_id") != "gemini-3.1-pro-preview-customtools":
        raise ValueError("unexpected provider model id")
    if provider.get("base_model_id") != "gemini-3.1-pro-preview":
        raise ValueError("unexpected base model id")
    if provider.get("launch_stage") != "Public preview":
        raise ValueError("launch stage must be Public preview")
    if not str(provider.get("official_model_doc", "")).startswith("https://docs.cloud.google.com/"):
        raise ValueError("official model doc must be a Google Cloud docs URL")

    credential = require_mapping(data, "credential_surface")
    if credential.get("gcloud_project_configured") is not True:
        raise ValueError("gcloud project must be configured")
    if credential.get("project_identifier_logged") is not False:
        raise ValueError("project identifier must not be logged")
    if credential.get("required_repo_secrets") != []:
        raise ValueError("selected local-first pilot must not require repo secrets")

    codeclash = require_mapping(data, "codeclash")
    if not HEX40.match(str(codeclash.get("commit_sha", ""))):
        raise ValueError("CodeClash commit must be a 40-character SHA")

    task = require_mapping(data, "task")
    if task.get("game") != "BattleSnake":
        raise ValueError("task.game must be BattleSnake")
    if task.get("pilot_config_path") != "configs/test/telos_battlesnake_vertex_gemini_pilot.yaml":
        raise ValueError("unexpected pilot config path")
    if int(task.get("rounds", -1)) != 1:
        raise ValueError("pilot rounds must be 1")
    if int(task.get("sims_per_round", -1)) != 1:
        raise ValueError("pilot sims_per_round must be 1")
    players = task.get("players")
    if not isinstance(players, list) or len(players) != 2:
        raise ValueError("pilot must define p1 and p2 players")
    p1 = next((player for player in players if player.get("name") == "p1"), None)
    if not p1 or p1.get("provider_backed") is not True:
        raise ValueError("p1 must be provider-backed")

    budget = require_mapping(data, "budget")
    if budget.get("dollar_ceiling_usd") != 25:
        raise ValueError("dollar ceiling must be 25")
    if budget.get("max_model_invocations") != 8:
        raise ValueError("max_model_invocations must be 8")
    if budget.get("stop_if_cost_missing") is not True:
        raise ValueError("pilot must stop if cost is missing")


def validate_scorecard(data: dict[str, Any]) -> None:
    if data.get("schema_version") != "telos.provider_model_pilot_scorecard.v1":
        raise ValueError("unexpected scorecard schema_version")
    if data.get("selected") != EXPECTED_PILOT:
        raise ValueError("scorecard selected candidate mismatch")
    candidates = data.get("candidates")
    if not isinstance(candidates, list) or len(candidates) < 3:
        raise ValueError("scorecard must include at least three candidates")
    selected = [item for item in candidates if item.get("decision") == "selected"]
    if len(selected) != 1 or selected[0].get("candidate_id") != EXPECTED_PILOT:
        raise ValueError("scorecard must select exactly the expected pilot")


def validate_preflight(data: dict[str, Any]) -> None:
    if data.get("schema_version") != "telos.provider_model_preflight.v1":
        raise ValueError("unexpected preflight schema_version")

    env = require_mapping(data, "local_environment")
    for name in [
        "OPENAI_API_KEY_present",
        "ANTHROPIC_API_KEY_present",
        "GEMINI_API_KEY_present",
        "PORTKEY_API_KEY_present",
    ]:
        if env.get(name) is not False:
            raise ValueError(f"{name} must be false for this selection")

    github = require_mapping(data, "github_actions")
    if github.get("secret_values_inspected") is not False:
        raise ValueError("GitHub secret values must not be inspected")

    google = require_mapping(data, "google_cloud")
    if google.get("gcloud_present") is not True:
        raise ValueError("gcloud must be present")
    if google.get("active_account_present") is not True:
        raise ValueError("active gcloud account must be present")
    if google.get("project_configured") is not True:
        raise ValueError("gcloud project must be configured")
    if google.get("project_identifier_logged") is not False:
        raise ValueError("gcloud project identifier must not be logged")
    if google.get("tokens_or_secret_values_logged") is not False:
        raise ValueError("tokens or secret values must not be logged")

    services = set(google.get("enabled_services", []))
    required = {"aiplatform.googleapis.com", "generativelanguage.googleapis.com"}
    if not required.issubset(services):
        raise ValueError("required Google services are not both enabled")


def main() -> int:
    try:
        for path in [SELECTED, SCORECARD, PREFLIGHT, SOURCES]:
            if not path.exists():
                raise ValueError(f"missing {path.relative_to(ROOT)}")
        validate_selected(load_json(SELECTED))
        validate_scorecard(load_json(SCORECARD))
        validate_preflight(load_json(PREFLIGHT))

        sources = SOURCES.read_text(encoding="utf-8")
        for required in [
            "https://developers.openai.com/api/docs/guides/latest-model.md",
            "https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/gemini/3-1-pro",
            "381cdfa05a35e8acd35853b9fc7e13005121b127",
            "No token, API key, credential JSON, or Google Cloud project identifier is committed",
        ]:
            if required not in sources:
                raise ValueError(f"sources missing required evidence: {required}")
    except (OSError, TypeError, ValueError, json.JSONDecodeError) as exc:
        return fail(str(exc))

    print(f"provider model pilot slice valid: selected={EXPECTED_PILOT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
