#!/usr/bin/env python3
"""Redacted iter155 cloud/provider preflight.

The report intentionally records only readiness booleans, status codes, error classes, artifact hashes,
and latency. It never writes provider keys, account IDs, project IDs, raw model text, or bearer tokens.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
EXPERIMENT = ROOT / "experiments/iter155_adaptive_reward_hack_expansion"
PROOF = EXPERIMENT / "proof"
POOL = PROOF / "raw/adaptive_candidate_pool.json"
SUMMARY = PROOF / "adaptive_pool_summary.json"


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def run_bool(cmd: list[str]) -> bool:
    return subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode == 0


def secret_names() -> list[str]:
    proc = subprocess.run(
        ["gcloud", "secrets", "list", "--format=value(name)"],
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        return []
    return [line.strip() for line in proc.stdout.splitlines() if line.strip()]


def access_secret(containing: str) -> tuple[str | None, bool]:
    matches = [name for name in secret_names() if containing in name.lower()]
    if not matches:
        return None, False
    proc = subprocess.run(
        ["gcloud", "secrets", "versions", "access", "latest", "--secret", matches[0]],
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=False,
        check=False,
    )
    if proc.returncode != 0 or len(proc.stdout.strip()) <= 8:
        return None, False
    return proc.stdout.decode("utf-8", errors="ignore").strip(), True


def call_preflight(req: Request, started: float) -> dict[str, Any]:
    try:
        with urlopen(req, timeout=60) as response:
            response.read()
            return {
                "ok": 200 <= response.status < 300,
                "status_code": response.status,
                "error_class": None,
                "latency_sec": round(time.time() - started, 3),
                "raw_model_text_written": False,
            }
    except HTTPError as exc:
        exc.read()
        return {
            "ok": False,
            "status_code": exc.code,
            "error_class": "HTTPError",
            "latency_sec": round(time.time() - started, 3),
            "raw_model_text_written": False,
        }
    except URLError:
        return {
            "ok": False,
            "status_code": None,
            "error_class": "URLError",
            "latency_sec": round(time.time() - started, 3),
            "raw_model_text_written": False,
        }
    except Exception as exc:  # pragma: no cover - defensive redaction branch.
        return {
            "ok": False,
            "status_code": None,
            "error_class": type(exc).__name__,
            "latency_sec": round(time.time() - started, 3),
            "raw_model_text_written": False,
        }


def openai_preflight(api_key: str) -> dict[str, Any]:
    started = time.time()
    body = json.dumps(
        {
            "model": "gpt-5.6-terra",
            "messages": [{"role": "user", "content": "Return compact JSON: {\"ok\":true}"}],
            "max_completion_tokens": 64,
        }
    ).encode("utf-8")
    req = Request(
        "https://api.openai.com/v1/chat/completions",
        data=body,
        headers={"Authorization": "Bearer " + api_key, "content-type": "application/json"},
        method="POST",
    )
    return call_preflight(req, started)


def anthropic_preflight(api_key: str) -> dict[str, Any]:
    started = time.time()
    body = json.dumps(
        {
            "model": "claude-opus-4-8",
            "max_tokens": 64,
            "messages": [{"role": "user", "content": "Return compact JSON: {\"ok\":true}"}],
        }
    ).encode("utf-8")
    req = Request(
        "https://api.anthropic.com/v1/messages",
        data=body,
        headers={
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
        method="POST",
    )
    return call_preflight(req, started)


def missing_artifact_report(missing: list[Path]) -> dict[str, Any]:
    return {
        "schema_version": "telos.iter155.preflight.v1",
        "ready_for_cloud_execution": False,
        "execution_blockers": [f"missing artifact: {path.relative_to(ROOT)}" for path in missing],
        "redaction": {
            "secrets_written": False,
            "account_ids_written": False,
            "project_ids_written": False,
            "raw_model_text_written": False,
            "bearer_tokens_written": False,
        },
    }


def main() -> int:
    missing = [path for path in (POOL, SUMMARY) if not path.exists()]
    if missing:
        report = missing_artifact_report(missing)
        write_json(PROOF / "preflight_report.json", report)
        print("preflight_ready=false")
        print("blocker=missing_iter155_pool_artifact")
        return 2

    pool = json.loads(POOL.read_text(encoding="utf-8"))
    summary = json.loads(SUMMARY.read_text(encoding="utf-8"))

    gcloud_present = run_bool(["gcloud", "--version"])
    docker_present = run_bool(["docker", "--version"])
    active_auth = run_bool(["gcloud", "auth", "list", "--filter=status:ACTIVE", "--format=value(account)"])
    project_configured = run_bool(["gcloud", "config", "get-value", "project"])
    compute_access = run_bool(["gcloud", "compute", "zones", "list", "--limit=1"])
    secretmanager_access = run_bool(["gcloud", "secrets", "list", "--limit=1"])

    openai_key, openai_secret_access = access_secret("openai")
    anthropic_key, anthropic_secret_access = access_secret("anthropic")

    openai = (
        openai_preflight(openai_key)
        if openai_key
        else {
            "ok": False,
            "status_code": None,
            "error_class": "MissingSecret",
            "latency_sec": 0,
            "raw_model_text_written": False,
        }
    )
    anthropic = (
        anthropic_preflight(anthropic_key)
        if anthropic_key
        else {
            "ok": False,
            "status_code": None,
            "error_class": "MissingSecret",
            "latency_sec": 0,
            "raw_model_text_written": False,
        }
    )

    selected_candidates = len(pool.get("rows", []))
    blockers: list[str] = []
    if selected_candidates != summary.get("selected_candidates"):
        blockers.append("pool_summary_selected_candidate_mismatch")
    if selected_candidates <= 0:
        blockers.append("empty_adaptive_candidate_pool")
    if summary.get("provider_calls") != 0:
        blockers.append("adaptive_pool_not_provider_outcome_free")
    if summary.get("cloud_resources_created") != 0:
        blockers.append("adaptive_pool_created_cloud_resources")

    report = {
        "schema_version": "telos.iter155.preflight.v1",
        "adaptive_pool": {
            "path": str(POOL.relative_to(ROOT)),
            "sha256": sha256_file(POOL),
            "selected_candidates": selected_candidates,
            "selected_repositories": summary.get("selected_repositories", []),
        },
        "adaptive_pool_summary": {
            "path": str(SUMMARY.relative_to(ROOT)),
            "sha256": sha256_file(SUMMARY),
            "status": summary.get("status"),
        },
        "budget": {
            "provider_plus_cloud_spend_usd_ceiling": 250,
            "preflight_provider_calls": 2,
        },
        "gcloud_present": gcloud_present,
        "docker_present": docker_present,
        "active_gcloud_auth_present": active_auth,
        "gcloud_project_configured": project_configured,
        "gcloud_compute_access": compute_access,
        "secretmanager_access": secretmanager_access,
        "openai_secret_access": openai_secret_access,
        "anthropic_secret_access": anthropic_secret_access,
        "models": {
            "gpt_5_6_terra": openai,
            "claude_opus_4_8": anthropic,
        },
        "third_judge_preflight": {
            "attempted": False,
            "ok": False,
            "reason": "iter155 hypothesis does not add a third judge without a separate preflight",
        },
        "redaction": {
            "secrets_written": False,
            "account_ids_written": False,
            "project_ids_written": False,
            "raw_model_text_written": False,
            "bearer_tokens_written": False,
        },
        "execution_blockers": blockers,
    }
    report["ready_for_cloud_execution"] = all(
        [
            not blockers,
            report["gcloud_present"],
            report["active_gcloud_auth_present"],
            report["gcloud_project_configured"],
            report["gcloud_compute_access"],
            report["secretmanager_access"],
            report["openai_secret_access"],
            report["anthropic_secret_access"],
            openai["ok"],
            anthropic["ok"],
        ]
    )
    write_json(PROOF / "preflight_report.json", report)
    print("preflight_ready=" + str(report["ready_for_cloud_execution"]).lower())
    print("openai_model_ok=" + str(openai["ok"]).lower())
    print("anthropic_model_ok=" + str(anthropic["ok"]).lower())
    print("execution_blockers=" + str(len(blockers)))
    return 0 if report["ready_for_cloud_execution"] else 2


if __name__ == "__main__":
    sys.exit(main())
