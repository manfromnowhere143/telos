#!/usr/bin/env python3
"""Redacted iter154 cloud/provider preflight.

The report intentionally records only readiness booleans and error classes/status codes. It never writes
provider keys, account IDs, project IDs, raw model text, or bearer tokens.
"""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import time
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
PROOF = ROOT / "experiments/iter154_reward_hack_benchmark_expansion_pilot/proof"


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


def call_preflight(req: Request, started: float) -> dict[str, Any]:
    try:
        with urlopen(req, timeout=60) as response:
            response.read()
            return {
                "ok": 200 <= response.status < 300,
                "status_code": response.status,
                "error_class": None,
                "latency_sec": round(time.time() - started, 3),
            }
    except HTTPError as exc:
        exc.read()
        return {
            "ok": False,
            "status_code": exc.code,
            "error_class": "HTTPError",
            "latency_sec": round(time.time() - started, 3),
        }
    except URLError:
        return {
            "ok": False,
            "status_code": None,
            "error_class": "URLError",
            "latency_sec": round(time.time() - started, 3),
        }
    except Exception as exc:  # pragma: no cover - defensive redaction branch.
        return {
            "ok": False,
            "status_code": None,
            "error_class": type(exc).__name__,
            "latency_sec": round(time.time() - started, 3),
        }


def main() -> int:
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
        else {"ok": False, "status_code": None, "error_class": "MissingSecret", "latency_sec": 0}
    )
    anthropic = (
        anthropic_preflight(anthropic_key)
        if anthropic_key
        else {"ok": False, "status_code": None, "error_class": "MissingSecret", "latency_sec": 0}
    )

    report = {
        "schema_version": "telos.iter154.preflight.v1",
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
            "reason": "iter154 optional third judge not selected before base expansion preflight",
        },
        "redaction": {
            "secrets_written": False,
            "account_ids_written": False,
            "project_ids_written": False,
            "raw_model_text_written": False,
        },
    }
    report["ready_for_cloud_execution"] = all(
        [
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
    return 0 if report["ready_for_cloud_execution"] else 2


if __name__ == "__main__":
    sys.exit(main())
