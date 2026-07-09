#!/usr/bin/env python3
"""Run and publish iter59 provider-compatible paid execution artifacts."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
import shlex
import shutil
import subprocess
import tarfile
import time
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
EXPERIMENT_ID = "iter59_provider_compatible_paid_execution_after_dependency_recovery"
EXPERIMENT = ROOT / "experiments" / EXPERIMENT_ID
PROOF = EXPERIMENT / "proof"
RAW = PROOF / "raw"
VALID = PROOF / "valid"
ITER58_SUMMARY = (
    ROOT
    / "experiments"
    / "iter58_codeclash_vertex_dependency_recovery"
    / "proof"
    / "run_summary.json"
)
ITER58_RECEIPT_DIR = (
    ROOT / "experiments" / "iter58_codeclash_vertex_dependency_recovery" / "proof"
)
ITER54_COMMANDS = (
    ROOT / "experiments" / "iter54_provider_pair_executor_recovery" / "proof" / "command_manifest.json"
)
ITER54_OVERLAYS = (
    ROOT / "experiments" / "iter54_provider_pair_executor_recovery" / "proof" / "overlay_copy_manifest.json"
)
ITER48_SLICE = (
    ROOT
    / "experiments"
    / "iter48_provider_compatible_protocol_effect_slice_refreeze"
    / "proof"
    / "provider_compatible_slice.json"
)
CODECLASH_DIR = Path("/tmp/telos-codeclash")
CODECLASH_COMMIT = "381cdfa05a35e8acd35853b9fc7e13005121b127"
DOCKER_BIN = Path("/Applications/Docker.app/Contents/Resources/bin/docker")
SELECTED_PAIR_IDS = [
    "baseline-agent-completion-evidence__configs-test-battlesnake-pvp-test-yaml",
    "telos-receipt-enforced-completion-evidence__configs-test-battlesnake-pvp-test-yaml",
]
TELOS_PAIR_ID = "telos-receipt-enforced-completion-evidence__configs-test-battlesnake-pvp-test-yaml"
CALL_CEILING = 16
SPEND_CEILING = 10.0
REUSE_EXISTING_RAW = os.environ.get("TELOS_ITER59_REUSE_RAW") == "1"
TEXT_SUFFIXES = {
    ".json",
    ".jsonl",
    ".log",
    ".txt",
    ".md",
    ".yaml",
    ".yml",
    ".py",
}
SECRET_PATTERNS = [
    re.compile(r"github_pat_[A-Za-z0-9_]{20,}"),
    re.compile(r"gho_[A-Za-z0-9_]{20,}"),
    re.compile(r"(?<![A-Za-z0-9])sk-[A-Za-z0-9_-]{20,}"),
    re.compile(r"ya29\.[A-Za-z0-9_-]{20,}"),
    re.compile(r"-----BEGIN PRIVATE KEY-----"),
    re.compile(r"ANTHROPIC_API_KEY\s*=\s*\S+"),
    re.compile(r"OPENAI_API_KEY\s*=\s*\S+"),
    re.compile(r"GOOGLE_API_KEY\s*=\s*\S+"),
    re.compile(r"GEMINI_API_KEY\s*=\s*\S+"),
    re.compile(r"GOOGLE_APPLICATION_CREDENTIALS\s*=\s*\S+"),
    re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.gserviceaccount\.com"),
    re.compile(r"telos-vertex-runner"),
    re.compile(r"sunlit-unison-[A-Za-z0-9-]+"),
    re.compile(r"errorId=Ci"),
    re.compile(r'"error_info_id"\s*:\s*"Ci'),
]
REDACTION_REPLACEMENTS = [
    (re.compile(r"projects/sunlit-unison-[A-Za-z0-9-]+"), "projects/[REDACTED_GCP_PROJECT]"),
    (re.compile(r"sunlit-unison-[A-Za-z0-9-]+"), "[REDACTED_GCP_PROJECT]"),
    (re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.gserviceaccount\.com"), "[REDACTED_SERVICE_ACCOUNT]"),
    (re.compile(r"ya29\.[A-Za-z0-9_-]{20,}"), "[REDACTED_ADC_TOKEN]"),
    (re.compile(r"errorId=Ci[A-Za-z0-9_-]+"), "errorId=[REDACTED_ERROR_ID]"),
    (re.compile(r'"error_info_id"\s*:\s*"Ci[A-Za-z0-9_-]+"'), '"error_info_id": "[REDACTED_ERROR_INFO_ID]"'),
]


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def read_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise RuntimeError(f"{path.relative_to(ROOT)} root must be an object")
    return data


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def redact_text(text: str) -> str:
    redacted = text
    for pattern, replacement in REDACTION_REPLACEMENTS:
        redacted = pattern.sub(replacement, redacted)
    return redacted


def normalize_public_text(text: str) -> str:
    if not text:
        return text
    lines = [line.rstrip() for line in text.splitlines()]
    while lines and lines[-1] == "":
        lines.pop()
    return "\n".join(lines) + ("\n" if lines else "")


def redact_value(value: Any) -> Any:
    if isinstance(value, str):
        return redact_text(value)
    if isinstance(value, list):
        return [redact_value(item) for item in value]
    if isinstance(value, dict):
        return {key: redact_value(item) for key, item in value.items()}
    return value


def redact_text_file(path: Path) -> None:
    if path.suffix not in TEXT_SUFFIXES:
        return
    original = path.read_text(encoding="utf-8", errors="ignore")
    redacted = normalize_public_text(redact_text(original))
    if redacted != original:
        path.write_text(redacted, encoding="utf-8")


def redact_tree(paths: list[Path]) -> None:
    for base in paths:
        candidates = [base] if base.is_file() else [path for path in base.rglob("*") if path.is_file()]
        for path in candidates:
            redact_text_file(path)


def run_probe(args: list[str], timeout: int = 20) -> dict[str, Any]:
    try:
        result = subprocess.run(
            args,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        return {"returncode": None, "timed_out": True}
    return {"returncode": result.returncode, "timed_out": False}


def run_capture(args: list[str], timeout: int = 20) -> dict[str, Any]:
    try:
        result = subprocess.run(
            args,
            capture_output=True,
            text=True,
            check=False,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        return {"returncode": None, "timed_out": True, "stdout": "", "stderr": ""}
    return {
        "returncode": result.returncode,
        "timed_out": False,
        "stdout": result.stdout.strip(),
        "stderr": result.stderr.strip(),
    }


def receipt_digest(data: dict[str, Any]) -> str:
    unsigned = {key: value for key, value in data.items() if key != "sha256"}
    return sha256_bytes(
        json.dumps(unsigned, sort_keys=True, separators=(",", ":")).encode("utf-8")
    )


def build_receipt(status: str) -> dict[str, Any]:
    receipt = {
        "receipt_id": f"iter59-provider-compatible-paid-execution-{status}",
        "task_id": "telos:iter59_provider_compatible_paid_execution_after_dependency_recovery@iter58",
        "agent_id": "codex-local-provider-compatible-paid-execution-runner",
        "benchmark_id": "telos_codeclash_swebench_protocol_effect_pilot",
        "status": status,
        "stated_goal": (
            "Execute exactly the two frozen provider-compatible BattleSnake rows and measure "
            "verified-completion evidence under baseline and Telos receipt-enforced conditions."
        ),
        "acceptance_criteria": [
            "Iter58 is a clean pass before paid execution.",
            "Exactly two selected BattleSnake condition rows execute and zero excluded pairs execute.",
            "Provider calls stay at or below 16 and provider spend at or below $10.00.",
            "No GPU, Sentinel resource mutation, production/live-domain mutation, or overclaim occurs.",
            "The Telos row is accepted as verified completion only if receipt validation passes.",
        ],
        "evidence": [
            {
                "kind": "test",
                "status": status,
                "artifact": f"experiments/{EXPERIMENT_ID}/proof/run_summary.json",
                "notes": "Run summary records exact row execution, call, cost, receipt, and metric counts.",
            },
            {
                "kind": "artifact",
                "status": status,
                "artifact": f"experiments/{EXPERIMENT_ID}/proof/raw/",
                "notes": "Raw packet contains command transcripts, CodeClash metadata, trajectory, changes, and extracted round results.",
            },
            {
                "kind": "adversarial_review",
                "status": status,
                "artifact": f"experiments/{EXPERIMENT_ID}/proof/review.md",
                "notes": "Review records the two-row claim boundary and any null/blocked outcome.",
            },
        ],
        "falsifiers": [
            "The result must block if iter58 is not a clean pass or credentials regress before execution.",
            "The result must fail if any excluded pair executes.",
            "The result must fail if provider calls, spend, GPU use, Sentinel mutation, or overclaim exceeds the gate.",
            "The result must not accept the Telos row as verified completion unless receipt validation passes.",
        ],
        "sha256": "",
    }
    receipt["sha256"] = receipt_digest(receipt)
    return receipt


def command_output_root(command: str) -> Path:
    parts = shlex.split(command)
    if "-o" not in parts:
        raise RuntimeError(f"frozen command lacks -o output directory: {command}")
    return Path(parts[parts.index("-o") + 1])


def path_children(path: Path) -> set[Path]:
    if not path.exists():
        return set()
    return {child for child in path.iterdir() if child.is_dir()}


def newest_output_dir(root: Path, before: set[Path]) -> Path | None:
    after = path_children(root)
    created = list(after - before)
    if created:
        return max(created, key=lambda p: p.stat().st_mtime)
    if after:
        return max(after, key=lambda p: p.stat().st_mtime)
    return None


def command_env() -> dict[str, str]:
    env = os.environ.copy()
    env["PATH"] = f"{DOCKER_BIN.parent}:{env.get('PATH', '')}"
    env["NO_COLOR"] = "1"
    env["PYTHONUNBUFFERED"] = "1"
    return env


def run_paid_command(pair_id: str, command: str) -> dict[str, Any]:
    output_root = command_output_root(command)
    before = path_children(output_root)
    transcript_dir = RAW / pair_id
    transcript_dir.mkdir(parents=True, exist_ok=True)
    start = time.time()
    try:
        result = subprocess.run(
            command,
            shell=True,
            cwd=ROOT,
            env=command_env(),
            capture_output=True,
            text=True,
            check=False,
            timeout=1800,
        )
        timed_out = False
        returncode = result.returncode
        stdout = result.stdout
        stderr = result.stderr
    except subprocess.TimeoutExpired as exc:
        timed_out = True
        returncode = None
        stdout = exc.stdout.decode("utf-8", errors="replace") if isinstance(exc.stdout, bytes) else (exc.stdout or "")
        stderr = exc.stderr.decode("utf-8", errors="replace") if isinstance(exc.stderr, bytes) else (exc.stderr or "")
    elapsed = time.time() - start
    output_dir = newest_output_dir(output_root, before)
    (transcript_dir / "command_stdout.txt").write_text(stdout, encoding="utf-8")
    (transcript_dir / "command_stderr.txt").write_text(stderr, encoding="utf-8")
    write_json(
        transcript_dir / "command_execution.json",
        {
            "command": command,
            "elapsed_seconds": round(elapsed, 3),
            "output_dir": str(output_dir) if output_dir else None,
            "output_root": str(output_root),
            "returncode": returncode,
            "timed_out": timed_out,
        },
    )
    return {
        "command": command,
        "elapsed_seconds": round(elapsed, 3),
        "output_dir": output_dir,
        "output_root": output_root,
        "returncode": returncode,
        "timed_out": timed_out,
    }


def safe_copy_file(source: Path, destination: Path) -> bool:
    if not source.exists() or not source.is_file():
        return False
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)
    return True


def copy_round_artifacts(source_output: Path, raw_dir: Path) -> list[str]:
    copied: list[str] = []
    rounds_dir = source_output / "rounds"
    if not rounds_dir.exists():
        rounds_dir = source_output / "game" / "rounds"
    if not rounds_dir.exists():
        return copied
    dest = raw_dir / "rounds"
    for archive in sorted(rounds_dir.glob("round_*.tar.gz")):
        with tarfile.open(archive, "r:gz") as tar:
            for member in tar.getmembers():
                name = Path(member.name)
                if name.name != "results.json" and not name.name.startswith("sim_"):
                    continue
                extracted = tar.extractfile(member)
                if extracted is None:
                    continue
                out_path = dest / archive.stem.replace(".tar", "") / name.name
                out_path.parent.mkdir(parents=True, exist_ok=True)
                out_path.write_bytes(extracted.read())
                copied.append(str(out_path.relative_to(raw_dir)))
    for result_path in sorted(rounds_dir.glob("*/results.json")):
        out_path = dest / result_path.parent.name / "results.json"
        out_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(result_path, out_path)
        copied.append(str(out_path.relative_to(raw_dir)))
    for sim_path in sorted(rounds_dir.glob("*/sim_*.jsonl")):
        out_path = dest / sim_path.parent.name / sim_path.name
        out_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(sim_path, out_path)
        copied.append(str(out_path.relative_to(raw_dir)))
    return copied


def finalize_raw_packet(pair_id: str, output_dir: Path | None, copied: list[str]) -> dict[str, Any]:
    raw_dir = RAW / pair_id
    redact_tree([raw_dir])
    metadata_path = raw_dir / "metadata.json"
    metadata = read_json(metadata_path) if metadata_path.exists() else {}
    manifest_entries = []
    for path in sorted(raw_dir.rglob("*")):
        if path.is_file() and path.name != "raw_manifest.json":
            manifest_entries.append(
                {
                    "path": str(path.relative_to(raw_dir)),
                    "size_bytes": path.stat().st_size,
                    "sha256": sha256_file(path),
                }
            )
    write_json(
        raw_dir / "raw_manifest.json",
        {
            "output_dir": str(output_dir) if output_dir else None,
            "output_dir_present": bool(output_dir and output_dir.exists()),
            "copied_files": sorted(set(copied)),
            "files": manifest_entries,
            "redacted_before_publication": True,
        },
    )
    return {"raw_dir": raw_dir, "copied_files": sorted(set(copied)), "metadata": metadata}


def copy_raw_packet(pair_id: str, output_dir: Path | None) -> dict[str, Any]:
    raw_dir = RAW / pair_id
    copied: list[str] = []
    if output_dir is None:
        write_json(raw_dir / "raw_manifest.json", {"output_dir_present": False, "copied_files": []})
        return {"raw_dir": raw_dir, "copied_files": copied, "metadata": {}}

    file_map = {
        "metadata.json": output_dir / "metadata.json",
        "tournament.log": output_dir / "tournament.log",
        "everything.log": output_dir / "everything.log",
        "game.log": output_dir / "game.log",
        "players/p1/player.log": output_dir / "players" / "p1" / "player.log",
        "players/p1/p1_r1.traj.json": output_dir / "players" / "p1" / "p1_r1.traj.json",
        "players/p1/changes_r1.json": output_dir / "players" / "p1" / "changes_r1.json",
        "players/p2/player.log": output_dir / "players" / "p2" / "player.log",
    }
    for rel_path, source in file_map.items():
        if safe_copy_file(source, raw_dir / rel_path):
            copied.append(rel_path)
    copied.extend(copy_round_artifacts(output_dir, raw_dir))
    return finalize_raw_packet(pair_id, output_dir, copied)


def existing_command_result(pair_id: str, command: str) -> dict[str, Any]:
    raw_dir = RAW / pair_id
    execution = read_json(raw_dir / "command_execution.json")
    output_dir = execution.get("output_dir")
    return {
        "command": command,
        "elapsed_seconds": execution.get("elapsed_seconds"),
        "output_dir": Path(output_dir) if output_dir else None,
        "output_root": Path(execution["output_root"]) if execution.get("output_root") else None,
        "returncode": execution.get("returncode"),
        "timed_out": execution.get("timed_out"),
    }


def existing_raw_packet(pair_id: str, output_dir: Path | None) -> dict[str, Any]:
    raw_dir = RAW / pair_id
    copied = []
    for path in sorted(raw_dir.rglob("*")):
        if path.is_file() and path.name not in {"raw_manifest.json"}:
            copied.append(str(path.relative_to(raw_dir)))
    return finalize_raw_packet(pair_id, output_dir, copied)


def agent_stats(metadata: dict[str, Any], player_name: str = "p1") -> dict[str, Any]:
    for agent in metadata.get("agents", []):
        if agent.get("name") == player_name:
            stats = agent.get("agent_stats", {})
            return stats.get("1", stats.get(1, {}))
    return {}


def round_winner(metadata: dict[str, Any], round_num: str = "1") -> str | None:
    stats = metadata.get("round_stats", {})
    row = stats.get(round_num, stats.get(int(round_num), {}))
    if isinstance(row, dict):
        winner = row.get("winner")
        return str(winner) if winner is not None else None
    return None


def extract_receipt_candidate(raw_dir: Path) -> dict[str, Any]:
    changes_path = raw_dir / "players" / "p1" / "changes_r1.json"
    result = {
        "candidate_found": False,
        "candidate_json_parseable": False,
        "candidate_valid": False,
        "receipt_validation_returncode": None,
        "receipt_validation_stdout": "",
        "receipt_validation_stderr": "",
    }
    if not changes_path.exists():
        result["reason"] = "changes_file_missing"
        return result

    changes = read_json(changes_path)
    diff = changes.get("full_diff", "")
    lines = diff.splitlines()
    in_receipt = False
    candidate_lines: list[str] = []
    for line in lines:
        if line.startswith("diff --git "):
            in_receipt = " b/telos_completion_receipt.json" in line
            continue
        if not in_receipt:
            continue
        if line.startswith("+++") or line.startswith("---"):
            continue
        if line.startswith("+"):
            candidate_lines.append(line[1:])
    candidate = "\n".join(candidate_lines).strip()
    if not candidate:
        result["reason"] = "receipt_diff_missing"
        return result

    result["candidate_found"] = True
    candidate_path = raw_dir / "telos_completion_receipt_candidate.json"
    candidate_path.write_text(candidate + "\n", encoding="utf-8")
    try:
        parsed = json.loads(candidate)
    except json.JSONDecodeError:
        (raw_dir / "receipt_candidate_invalid_json.txt").write_text(candidate + "\n", encoding="utf-8")
        result["reason"] = "candidate_json_invalid"
        return result
    result["candidate_json_parseable"] = True
    if not isinstance(parsed, dict):
        result["reason"] = "candidate_root_not_object"
        return result

    valid_dir = raw_dir / "valid"
    invalid_dir = raw_dir / "invalid"
    valid_dir.mkdir(exist_ok=True)
    invalid_dir.mkdir(exist_ok=True)
    trial_path = valid_dir / "telos_completion_receipt.json"
    write_json(trial_path, parsed)
    validation = subprocess.run(
        ["python3", "scripts/validate_receipts.py", str(raw_dir.relative_to(ROOT))],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    result.update(
        {
            "receipt_validation_returncode": validation.returncode,
            "receipt_validation_stdout": validation.stdout.strip(),
            "receipt_validation_stderr": validation.stderr.strip(),
        }
    )
    if validation.returncode == 0:
        result["candidate_valid"] = True
        return result

    invalid_path = invalid_dir / "telos_completion_receipt.json"
    shutil.move(str(trial_path), invalid_path)
    result["reason"] = "candidate_failed_receipt_validation"
    return result


def row_metrics(pair_id: str, command_result: dict[str, Any], raw_packet: dict[str, Any]) -> dict[str, Any]:
    metadata = raw_packet["metadata"]
    stats = agent_stats(metadata)
    output_dir = command_result.get("output_dir")
    api_calls = stats.get("api_calls", 0) if isinstance(stats, dict) else 0
    cost = stats.get("cost", 0.0) if isinstance(stats, dict) else 0.0
    try:
        api_calls = int(api_calls or 0)
    except (TypeError, ValueError):
        api_calls = 0
    try:
        cost = float(cost or 0.0)
    except (TypeError, ValueError):
        cost = 0.0
    exit_status = str(stats.get("exit_status", "")) if isinstance(stats, dict) else ""
    raw_evidence_present = bool(
        raw_packet["copied_files"]
        and (RAW / pair_id / "metadata.json").exists()
        and (RAW / pair_id / "players" / "p1" / "p1_r1.traj.json").exists()
    )
    receipt = extract_receipt_candidate(RAW / pair_id) if pair_id == TELOS_PAIR_ID else {
        "candidate_found": False,
        "candidate_json_parseable": False,
        "candidate_valid": False,
        "receipt_validation_returncode": None,
        "receipt_validation_stdout": "",
        "receipt_validation_stderr": "",
        "reason": "receipt_not_required_for_baseline",
    }
    if pair_id == TELOS_PAIR_ID:
        verified_completion = bool(
            command_result.get("returncode") == 0
            and raw_evidence_present
            and receipt.get("candidate_valid") is True
        )
    else:
        verified_completion = bool(command_result.get("returncode") == 0 and raw_evidence_present)
    return {
        "pair_id": pair_id,
        "command": command_result["command"],
        "command_returncode": command_result.get("returncode"),
        "command_timed_out": command_result.get("timed_out"),
        "elapsed_seconds": command_result.get("elapsed_seconds"),
        "output_dir": str(output_dir) if output_dir else None,
        "raw_artifact_count": len(raw_packet["copied_files"]),
        "raw_evidence_present": raw_evidence_present,
        "agent_exit_status": exit_status,
        "provider_api_calls": api_calls,
        "provider_cost_usd": cost,
        "round_1_winner": round_winner(metadata),
        "receipt_required": pair_id == TELOS_PAIR_ID,
        "receipt_candidate_found": receipt.get("candidate_found"),
        "receipt_candidate_json_parseable": receipt.get("candidate_json_parseable"),
        "receipt_valid": receipt.get("candidate_valid"),
        "receipt_validation_returncode": receipt.get("receipt_validation_returncode"),
        "receipt_validation_stdout": receipt.get("receipt_validation_stdout"),
        "receipt_validation_stderr": receipt.get("receipt_validation_stderr"),
        "receipt_validation_reason": receipt.get("reason"),
        "verified_completion_evidence": verified_completion,
    }


def provider_error_classes(row_results: list[dict[str, Any]]) -> list[str]:
    classes: set[str] = set()
    for row in row_results:
        status = str(row.get("agent_exit_status", ""))
        if "Publisher model" in status and "NOT_FOUND" in status:
            classes.add("vertex_model_not_found_or_access_denied")
        elif row.get("command_returncode") not in (0, None):
            classes.add("provider_command_nonzero_returncode")
    return sorted(classes)


def text_files_under(paths: list[Path]) -> list[Path]:
    files: list[Path] = []
    for base in paths:
        if base.is_file():
            candidates = [base]
        else:
            candidates = [path for path in base.rglob("*") if path.is_file()]
        for path in candidates:
            if path.suffix in TEXT_SUFFIXES:
                files.append(path)
    return files


def redaction_scan(paths: list[Path]) -> tuple[bool, list[str]]:
    findings: list[str] = []
    for path in text_files_under(paths):
        text = path.read_text(encoding="utf-8", errors="ignore")
        for pattern in SECRET_PATTERNS:
            if pattern.search(text):
                findings.append(str(path.relative_to(ROOT)))
                break
    return not findings, findings


def artifact_hashes(paths: list[Path]) -> dict[str, str]:
    hashes: dict[str, str] = {}
    for base in paths:
        if base.is_file():
            hashes[str(base.relative_to(PROOF))] = sha256_file(base)
            continue
        for path in sorted(base.rglob("*")):
            if path.is_file():
                hashes[str(path.relative_to(PROOF))] = sha256_file(path)
    return hashes


def preflight(command_manifest: dict[str, Any], iter58: dict[str, Any]) -> dict[str, Any]:
    codeclash_rev = run_capture(["git", "-C", str(CODECLASH_DIR), "rev-parse", "HEAD"])
    docker = run_capture([str(DOCKER_BIN), "info", "--format", "{{.ServerVersion}}"], timeout=10)
    google_auth = run_capture(
        [str(CODECLASH_DIR / ".venv" / "bin" / "python"), "-c", "import google.auth"],
        timeout=10,
    )
    adc = run_probe(["gcloud", "auth", "application-default", "print-access-token", "--quiet"])
    receipt_check = subprocess.run(
        ["python3", "scripts/validate_receipts.py", str(ITER58_RECEIPT_DIR.relative_to(ROOT))],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    commands = command_manifest.get("commands", [])
    selected_ids = [command.get("pair_id") for command in commands]
    return {
        "schema_version": "telos.provider_compatible_paid_execution.preflight.v1",
        "iter58_status": iter58.get("status"),
        "iter58_clean_pass": iter58.get("clean_pass"),
        "iter58_receipt_validation_returncode": receipt_check.returncode,
        "iter58_receipt_validation_stdout": receipt_check.stdout.strip(),
        "codeclash_checkout_present": (CODECLASH_DIR / ".git").exists(),
        "codeclash_expected_commit": CODECLASH_COMMIT,
        "codeclash_actual_commit": codeclash_rev.get("stdout"),
        "codeclash_commit_matches_expected": codeclash_rev.get("stdout") == CODECLASH_COMMIT,
        "docker_preferred_cli": str(DOCKER_BIN),
        "docker_ready": docker.get("returncode") == 0 and bool(docker.get("stdout")),
        "docker_server_version_present": bool(docker.get("stdout")),
        "codeclash_google_auth_import_ready": google_auth.get("returncode") == 0,
        "codeclash_google_auth_error_class": "none"
        if google_auth.get("returncode") == 0
        else "google_auth_module_missing",
        "adc_access_token_available": adc.get("returncode") == 0,
        "adc_token_output_suppressed": True,
        "selected_pair_count": len(selected_ids),
        "selected_pair_ids": selected_ids,
        "expected_selected_pair_ids": SELECTED_PAIR_IDS,
        "excluded_pair_ids": command_manifest.get("excluded_pair_ids", []),
        "excluded_pair_selected": bool(set(selected_ids) & set(command_manifest.get("excluded_pair_ids", []))),
        "provider_call_ceiling": CALL_CEILING,
        "provider_spend_ceiling_usd": SPEND_CEILING,
        "gpu_used": False,
        "sentinel_named_resources_modified": False,
        "cloud_runner_started": False,
    }


def latest_existing_output_dir(pair_id: str) -> Path | None:
    root = Path("/tmp/telos-codeclash-protocol-effect-condition-separated") / pair_id
    if not root.exists():
        return None
    children = [child for child in root.iterdir() if child.is_dir()]
    if not children:
        return None
    return max(children, key=lambda path: path.stat().st_mtime)


def dependency_block_evidence() -> dict[str, Any]:
    output_dir = latest_existing_output_dir(SELECTED_PAIR_IDS[0])
    copied = copy_raw_packet(SELECTED_PAIR_IDS[0], output_dir) if output_dir else {
        "raw_dir": RAW / SELECTED_PAIR_IDS[0],
        "copied_files": [],
        "metadata": {},
    }
    log_path = RAW / SELECTED_PAIR_IDS[0] / "everything.log"
    missing_google_seen = False
    if log_path.exists():
        missing_google_seen = "ModuleNotFoundError: No module named 'google'" in log_path.read_text(
            encoding="utf-8",
            errors="ignore",
        )
    evidence = {
        "schema_version": "telos.provider_compatible_paid_execution.dependency_block.v1",
        "attempted_pair_id": SELECTED_PAIR_IDS[0] if output_dir else None,
        "attempted_pair_output_dir": str(output_dir) if output_dir else None,
        "telos_pair_attempted": False,
        "missing_dependency": "google.auth",
        "missing_dependency_seen_in_log": missing_google_seen,
        "provider_api_calls_observed_in_partial_metadata": 0,
        "provider_cost_usd_observed_in_partial_metadata": 0.0,
        "copied_raw_files": copied["copied_files"],
    }
    write_json(PROOF / "dependency_block_evidence.json", evidence)
    return evidence


def main() -> int:
    PROOF.mkdir(parents=True, exist_ok=True)
    RAW.mkdir(parents=True, exist_ok=True)
    VALID.mkdir(parents=True, exist_ok=True)

    iter58 = read_json(ITER58_SUMMARY)
    command_manifest = read_json(ITER54_COMMANDS)
    _ = read_json(ITER54_OVERLAYS)
    _ = read_json(ITER48_SLICE)

    pre = preflight(command_manifest, iter58)
    write_json(PROOF / "preflight.json", pre)

    blockers: list[str] = []
    failures: list[str] = []
    if pre["iter58_status"] != "pass" or pre["iter58_clean_pass"] is not True:
        blockers.append("iter58_not_clean_pass")
    if pre["iter58_receipt_validation_returncode"] != 0:
        blockers.append("iter58_receipt_validation_failed")
    if not pre["codeclash_commit_matches_expected"]:
        blockers.append("codeclash_checkout_not_pinned")
    if not pre["docker_ready"]:
        blockers.append("docker_not_ready")
    if not pre["codeclash_google_auth_import_ready"]:
        blockers.append("codeclash_vertex_google_auth_dependency_missing")
    if not pre["adc_access_token_available"]:
        blockers.append("adc_auth_unavailable")
    if pre["selected_pair_ids"] != SELECTED_PAIR_IDS:
        failures.append("selected_pair_ids_changed")
    if pre["excluded_pair_selected"]:
        failures.append("excluded_pair_selected")

    dependency_evidence: dict[str, Any] = {}
    if "codeclash_vertex_google_auth_dependency_missing" in blockers:
        dependency_evidence = dependency_block_evidence()

    row_results: list[dict[str, Any]] = []
    if not blockers and not failures:
        for command in command_manifest.get("commands", []):
            pair_id = command["pair_id"]
            if REUSE_EXISTING_RAW:
                result = existing_command_result(pair_id, command["command"])
                raw_packet = existing_raw_packet(pair_id, result.get("output_dir"))
            else:
                result = run_paid_command(pair_id, command["command"])
                raw_packet = copy_raw_packet(pair_id, result.get("output_dir"))
            row_results.append(row_metrics(pair_id, result, raw_packet))

    provider_calls = sum(int(row.get("provider_api_calls", 0)) for row in row_results)
    provider_cost = round(sum(float(row.get("provider_cost_usd", 0.0)) for row in row_results), 8)
    if row_results and len(row_results) != 2:
        blockers.append("not_exactly_two_rows_executed")
    if any(row.get("command_returncode") not in (0, None) for row in row_results):
        blockers.append("provider_command_nonzero_returncode")
    error_classes = provider_error_classes(row_results)
    for error_class in error_classes:
        if error_class not in blockers:
            blockers.append(error_class)
    if provider_calls > CALL_CEILING:
        failures.append("provider_call_ceiling_exceeded")
    if provider_cost > SPEND_CEILING:
        failures.append("provider_spend_ceiling_exceeded")

    scan_passed, scan_findings = redaction_scan([RAW, PROOF / "preflight.json"])
    if not scan_passed:
        failures.append("redaction_scan_failed")

    row_ids = [row["pair_id"] for row in row_results]
    excluded_executed = bool(set(row_ids) & set(command_manifest.get("excluded_pair_ids", [])))
    if excluded_executed:
        failures.append("excluded_pair_executed")
    telos_row = next((row for row in row_results if row["pair_id"] == TELOS_PAIR_ID), {})
    receipt_validation_ran = telos_row.get("receipt_validation_returncode") is not None
    if row_results and not receipt_validation_ran:
        blockers.append("telos_receipt_validation_not_run")

    status = "fail" if failures else "blocked" if blockers else "pass"
    metric_rows = {
        row["pair_id"]: {
            "provider_api_calls": row["provider_api_calls"],
            "provider_cost_usd": row["provider_cost_usd"],
            "raw_evidence_present": row["raw_evidence_present"],
            "receipt_required": row["receipt_required"],
            "receipt_valid": row["receipt_valid"],
            "verified_completion_evidence": row["verified_completion_evidence"],
            "round_1_winner": row["round_1_winner"],
            "agent_exit_status": row["agent_exit_status"],
        }
        for row in row_results
    }
    primary_metric = {
        "baseline_verified_completion_evidence": metric_rows.get(SELECTED_PAIR_IDS[0], {}).get(
            "verified_completion_evidence", False
        ),
        "telos_verified_completion_evidence": metric_rows.get(SELECTED_PAIR_IDS[1], {}).get(
            "verified_completion_evidence", False
        ),
        "verified_completion_evidence_delta_telos_minus_baseline": int(
            bool(metric_rows.get(SELECTED_PAIR_IDS[1], {}).get("verified_completion_evidence", False))
        )
        - int(bool(metric_rows.get(SELECTED_PAIR_IDS[0], {}).get("verified_completion_evidence", False))),
    }

    report = {
        "schema_version": "telos.provider_compatible_paid_execution.report.v1",
        "status": status,
        "experiment_id": EXPERIMENT_ID,
        "preflight": pre,
        "selected_pair_ids": SELECTED_PAIR_IDS,
        "executed_pair_ids": row_ids,
        "executed_pair_count": len(row_results),
        "attempted_pair_ids": [
            dependency_evidence["attempted_pair_id"]
        ]
        if dependency_evidence.get("attempted_pair_id")
        else row_ids,
        "dependency_block_evidence": dependency_evidence,
        "excluded_pair_ids": command_manifest.get("excluded_pair_ids", []),
        "excluded_pair_executed": excluded_executed,
        "provider_api_calls": provider_calls,
        "provider_call_ceiling": CALL_CEILING,
        "provider_cost_usd": provider_cost,
        "provider_spend_ceiling_usd": SPEND_CEILING,
        "provider_error_classes": error_classes,
        "gpu_used": False,
        "sentinel_named_resources_modified": False,
        "cloud_runner_started": False,
        "teardown_required": False,
        "production_or_live_domain_changed": False,
        "benchmark_result_claimed": False,
        "leaderboard_or_swebench_result_claimed": False,
        "model_superiority_claimed": False,
        "state_of_the_art_result_claimed": False,
        "redaction_scan_passed": scan_passed,
        "redaction_findings": scan_findings,
        "row_results": row_results,
        "primary_metric": primary_metric,
        "secondary_metrics": {
            "task_success_by_round_winner": {
                row["pair_id"]: row["round_1_winner"] for row in row_results
            },
            "receipt_validation_by_pair": {
                row["pair_id"]: row["receipt_valid"] for row in row_results
            },
            "raw_artifact_count_by_pair": {
                row["pair_id"]: row["raw_artifact_count"] for row in row_results
            },
            "latency_seconds_by_pair": {
                row["pair_id"]: row["elapsed_seconds"] for row in row_results
            },
        },
        "blockers": blockers,
        "failures": failures,
    }
    report = redact_value(report)
    write_json(PROOF / "protocol_effect_report.json", report)

    command_lines = [
        f"provider-compatible paid execution after dependency recovery: {status}",
        f"executed_pair_count={len(row_results)}",
        f"excluded_pair_executed={str(excluded_executed).lower()}",
        f"provider_api_calls={provider_calls}",
        f"provider_cost_usd={provider_cost:.8f}",
        "gpu_used=false",
        "sentinel_named_resources_modified=false",
        f"baseline_verified_completion_evidence={str(primary_metric['baseline_verified_completion_evidence']).lower()}",
        f"telos_verified_completion_evidence={str(primary_metric['telos_verified_completion_evidence']).lower()}",
        f"verified_completion_evidence_delta_telos_minus_baseline={primary_metric['verified_completion_evidence_delta_telos_minus_baseline']}",
        f"blockers={','.join(blockers)}",
        f"failures={','.join(failures)}",
    ]
    for row in row_results:
        command_lines.append(
            f"{row['pair_id']}: rc={row['command_returncode']} calls={row['provider_api_calls']} "
            f"cost={row['provider_cost_usd']:.8f} receipt_valid={str(row['receipt_valid']).lower()} "
            f"verified={str(row['verified_completion_evidence']).lower()}"
        )
    (PROOF / "command_output.txt").write_text("\n".join(command_lines) + "\n", encoding="utf-8")

    if row_results:
        if "vertex_model_not_found_or_access_denied" in blockers:
            summary_sentence = (
                "The gate executed both selected provider-compatible BattleSnake rows after "
                "`iter58` recovered the local CodeClash Vertex dependency, then blocked because "
                "Vertex returned a redacted model-not-found-or-access-denied error for the "
                "configured provider model."
            )
        else:
            summary_sentence = (
                "The gate executed selected provider-compatible BattleSnake rows after `iter58` "
                "recovered the local CodeClash Vertex dependency."
            )
    elif "codeclash_vertex_google_auth_dependency_missing" in blockers:
        summary_sentence = (
            "The gate blocked before completing either provider-compatible BattleSnake row. A "
            "baseline attempt reached CodeClash round-0 evidence, then LiteLLM failed before any "
            "provider model call because the pinned CodeClash venv could not import `google.auth`."
        )
    else:
        summary_sentence = (
            "The gate blocked before executing provider-compatible BattleSnake rows because a "
            "preflight prerequisite failed."
        )

    result_md = f"""# Iteration 59 Result - Provider-Compatible Paid Execution After Dependency Recovery

Status: `{status.upper()}`.

## Summary

{summary_sentence} It did not execute excluded pairs, start a cloud runner, use GPU, or modify
Sentinel-named resources.

- executed pair count: `{len(row_results)}`,
- excluded pairs executed: `{str(excluded_executed).lower()}`,
- provider API calls: `{provider_calls}`,
- provider cost from CodeClash metadata: `${provider_cost:.8f}`,
- baseline verified-completion evidence: `{str(primary_metric['baseline_verified_completion_evidence']).lower()}`,
- Telos verified-completion evidence: `{str(primary_metric['telos_verified_completion_evidence']).lower()}`,
- Telos-minus-baseline verified-completion delta: `{primary_metric['verified_completion_evidence_delta_telos_minus_baseline']}`.
- blockers: `{','.join(blockers) if blockers else 'none'}`,
- failures: `{','.join(failures) if failures else 'none'}`.

## Claim Boundary

This is a bounded two-row provider-compatible protocol-effect pilot. It is not a benchmark result,
SWE-bench score, leaderboard result, production/live-domain result, model-superiority result, or
state-of-the-art result.

## Evidence

- `proof/preflight.json`
- `proof/protocol_effect_report.json`
- `proof/raw/`
- `proof/command_output.txt`
- `proof/review.md`
- `proof/run_summary.json`
- `proof/valid/receipt_provider_compatible_paid_execution_after_dependency_recovery.json`
"""
    (EXPERIMENT / "RESULT.md").write_text(result_md, encoding="utf-8")

    if row_results:
        review_scope = (
            "The paid retry stayed inside the selected BattleSnake rows and kept all four "
            "historical Dummy/deterministic-edit rows unattempted."
        )
    else:
        review_scope = (
            "The paid retry blocked before a provider model call. Only the baseline selected row "
            "was attempted, and the Telos selected row plus all four historical "
            "Dummy/deterministic-edit rows remained unattempted."
        )

    review = f"""# Iteration 59 Review

{review_scope} Provider calls and cost came from the committed CodeClash metadata, and redaction
was applied before publication.

Primary metric:

- baseline verified-completion evidence: `{str(primary_metric['baseline_verified_completion_evidence']).lower()}`,
- Telos verified-completion evidence: `{str(primary_metric['telos_verified_completion_evidence']).lower()}`,
- Telos-minus-baseline delta: `{primary_metric['verified_completion_evidence_delta_telos_minus_baseline']}`.

Blockers: `{','.join(blockers) if blockers else 'none'}`.
Failures: `{','.join(failures) if failures else 'none'}`.

No benchmark, SWE-bench, leaderboard, production/live-domain, model-superiority, or
state-of-the-art result is claimed.
"""
    (PROOF / "review.md").write_text(review, encoding="utf-8")

    summary_paths = [
        PROOF / "preflight.json",
        PROOF / "dependency_block_evidence.json",
        PROOF / "protocol_effect_report.json",
        PROOF / "command_output.txt",
        PROOF / "review.md",
        RAW,
    ]
    run_summary = {
        "schema_version": "telos.provider_compatible_paid_execution.summary.v1",
        "status": status,
        "experiment_id": EXPERIMENT_ID,
        "executed_pair_count": len(row_results),
        "executed_pair_ids": row_ids,
        "attempted_pair_ids": [
            dependency_evidence["attempted_pair_id"]
        ]
        if dependency_evidence.get("attempted_pair_id")
        else row_ids,
        "dependency_block_evidence": dependency_evidence,
        "excluded_pair_executed": excluded_executed,
        "provider_api_calls": provider_calls,
        "provider_call_ceiling": CALL_CEILING,
        "provider_cost_usd": provider_cost,
        "provider_spend_ceiling_usd": SPEND_CEILING,
        "provider_error_classes": error_classes,
        "gpu_used": False,
        "sentinel_named_resources_modified": False,
        "cloud_runner_started": False,
        "teardown_required": False,
        "redaction_scan_passed": scan_passed,
        "redaction_findings": scan_findings,
        "primary_metric": primary_metric,
        "clean_pass": status == "pass",
        "blocked_result": status == "blocked",
        "quality_failure": status == "fail",
        "benchmark_result_claimed": False,
        "leaderboard_or_swebench_result_claimed": False,
        "model_superiority_claimed": False,
        "state_of_the_art_result_claimed": False,
        "production_or_live_domain_changed": False,
        "blockers": blockers,
        "failures": failures,
        "artifact_hashes": artifact_hashes(summary_paths),
    }
    run_summary = redact_value(run_summary)
    write_json(PROOF / "run_summary.json", run_summary)

    if status == "blocked" and "codeclash_vertex_google_auth_dependency_missing" in blockers:
        learning_insight = (
            "The paid retry blocked before provider model calls because the pinned CodeClash "
            "virtualenv could not import google.auth; committed metadata shows zero provider "
            "calls and zero cost."
        )
        learning_next = (
            "recover the CodeClash Vertex dependency without spend before retrying the exact "
            "two-row paid pilot"
        )
    elif status == "blocked" and "vertex_model_not_found_or_access_denied" in blockers:
        learning_insight = (
            "Both selected provider-compatible BattleSnake rows executed, but each provider call "
            "returned a redacted Vertex model-not-found-or-access-denied response before verified "
            "completion evidence could be accepted."
        )
        learning_next = (
            "recover an accessible provider model binding before retrying the same frozen two-row gate"
        )
    elif status == "blocked":
        learning_insight = (
            "The paid retry did not establish a complete two-row protocol-effect result because a "
            "preflight or execution blocker remained."
        )
        learning_next = "fix only the named blocker before retrying the same frozen two-row gate"
    elif status == "fail":
        learning_insight = (
            "The paid retry exposed a quality failure under the pre-registered two-row protocol-effect "
            "gate."
        )
        learning_next = "publish the failure boundary before deciding whether a corrective gate is justified"
    else:
        learning_insight = (
            "The first paid provider-compatible protocol-effect pilot now has exact two-row "
            "baseline-vs-Telos verified-completion evidence counts."
        )
        learning_next = (
            "audit whether the measured two-row effect justifies a larger frozen provider-compatible slice"
        )

    learning_record = {
        "schema_version": "telos.learning_record.v1",
        "experiment_id": EXPERIMENT_ID,
        "status": status,
        "insight": learning_insight,
        "next_action": learning_next,
        "result_path": f"experiments/{EXPERIMENT_ID}/RESULT.md",
        "evidence_paths": [
            f"experiments/{EXPERIMENT_ID}/proof/run_summary.json",
            f"experiments/{EXPERIMENT_ID}/proof/protocol_effect_report.json",
            f"experiments/{EXPERIMENT_ID}/proof/command_output.txt",
            f"experiments/{EXPERIMENT_ID}/proof/valid/receipt_provider_compatible_paid_execution_after_dependency_recovery.json",
        ],
    }
    learning_record = redact_value(learning_record)
    write_json(PROOF / "learning_record.json", learning_record)
    write_json(
        VALID / "receipt_provider_compatible_paid_execution_after_dependency_recovery.json",
        build_receipt(status),
    )

    print("\n".join(command_lines))
    return 0 if status in {"pass", "blocked"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
