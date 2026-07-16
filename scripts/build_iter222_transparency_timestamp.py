#!/usr/bin/env python3
"""Obtain a real RFC 3161 transparency timestamp over the frozen iter222 commitment.

The commitment binds the model-binding digest, the isolation-rehearsal digest, and the
sealed hypothesis digest.  A public timestamp authority signs a token over the commitment's
SHA-256; the token verifies only against that authority's certificate chain, so this
repository cannot mint it and a fabricated token fails verification (Standard 9).

A Git commit is not this.  The token is an external attestation that the commitment existed
at the authority's stated time, independent of this repository's own history.

If no authority is reachable, this writes a blocked record and returns nonzero.  It never
fabricates a token or substitutes a Git commit for one.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import urllib.request
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
EXPERIMENT = ROOT / "experiments/iter222_tcp1_agent_solvable_admission_evidence"
PROOF = EXPERIMENT / "proof"
COMMITMENT = PROOF / "timestamp_commitment.json"
TOKEN = PROOF / "timestamp_token.tsr"
CACERT = PROOF / "timestamp_cacert.pem"
TSACERT = PROOF / "timestamp_tsa.crt"
RECORD = PROOF / "transparency_timestamp.json"

HYPOTHESIS = EXPERIMENT / "HYPOTHESIS.md"
MODEL_BINDING = PROOF / "model_binding.json"
ISOLATION = PROOF / "isolation_rehearsal.json"

TSA_URL = "https://freetsa.org/tsr"
CACERT_URL = "https://freetsa.org/files/cacert.pem"
TSACERT_URL = "https://freetsa.org/files/tsa.crt"


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def digest_of(record_path: Path, field: str) -> str:
    return json.loads(record_path.read_text(encoding="utf-8"))[field]


def freeze_commitment() -> dict[str, Any]:
    commitment = {
        "schema_version": "telos.iter222.timestamp_commitment.v1",
        "hypothesis_sha256": sha256_file(HYPOTHESIS),
        "model_binding_sha256": digest_of(MODEL_BINDING, "binding_sha256"),
        "isolation_rehearsal_sha256": sha256_file(ISOLATION),
    }
    COMMITMENT.write_text(
        json.dumps(commitment, indent=1, sort_keys=True) + "\n", encoding="utf-8"
    )
    return commitment


def fetch(url: str, dest: Path) -> None:
    with urllib.request.urlopen(url, timeout=45) as response:
        dest.write_bytes(response.read())


def request_token() -> None:
    query = PROOF / "_timestamp_request.tsq"
    subprocess.run(
        ["openssl", "ts", "-query", "-data", str(COMMITMENT), "-sha256", "-cert", "-out", str(query)],
        check=True,
        capture_output=True,
    )
    request = urllib.request.Request(
        TSA_URL,
        data=query.read_bytes(),
        headers={"Content-Type": "application/timestamp-query"},
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        TOKEN.write_bytes(response.read())
    query.unlink(missing_ok=True)


def verify_token() -> tuple[bool, str]:
    result = subprocess.run(
        [
            "openssl", "ts", "-verify",
            "-data", str(COMMITMENT),
            "-in", str(TOKEN),
            "-CAfile", str(CACERT),
            "-untrusted", str(TSACERT),
        ],
        capture_output=True,
        text=True,
    )
    transcript = (result.stdout + result.stderr).strip()
    return "Verification: OK" in transcript, transcript


def token_time() -> str | None:
    result = subprocess.run(
        ["openssl", "ts", "-reply", "-in", str(TOKEN), "-text"],
        capture_output=True,
        text=True,
    )
    for line in result.stdout.splitlines():
        if "Time stamp:" in line:
            return line.split("Time stamp:", 1)[1].strip()
    return None


def build() -> dict[str, Any]:
    commitment = freeze_commitment()
    fetch(CACERT_URL, CACERT)
    fetch(TSACERT_URL, TSACERT)
    request_token()
    verified, transcript = verify_token()
    stamped = token_time()
    return {
        "schema_version": "telos.iter222.transparency_timestamp.v1",
        "gate": "experiments/iter222_tcp1_agent_solvable_admission_evidence/HYPOTHESIS.md",
        "authority": "freetsa.org (RFC 3161)",
        "commitment": commitment,
        "commitment_sha256": sha256_file(COMMITMENT),
        "token_file": TOKEN.relative_to(ROOT).as_posix(),
        "token_sha256": sha256_file(TOKEN),
        "cacert_sha256": sha256_file(CACERT),
        "tsa_cert_sha256": sha256_file(TSACERT),
        "verified": verified,
        "verification_transcript": transcript,
        "timestamp_utc": stamped,
        "meaning": (
            "A third-party authority signed a token asserting the commitment digest existed "
            "at the stated time. It is an external anchor independent of this repository's "
            "Git history. It attests existence-at-time, not authorship or semantic truth."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="validate the committed token")
    args = parser.parse_args()

    if args.check:
        for path in (COMMITMENT, TOKEN, CACERT, TSACERT, RECORD):
            if not path.exists():
                print(f"iter222 timestamp artifact missing: {path.name}")
                return 1
        record = json.loads(RECORD.read_text(encoding="utf-8"))
        if record.get("verified") is not True:
            print("iter222 timestamp record is not a verified token")
            return 1
        # Re-verify the committed token offline against the committed cert chain and
        # commitment.  This proves the token still verifies, not merely that a flag was set.
        verified, _ = verify_token()
        if not verified:
            print("iter222 committed timestamp token does not re-verify")
            return 1
        if sha256_file(TOKEN) != record["token_sha256"]:
            print("iter222 committed token digest differs from the record")
            return 1
        if sha256_file(COMMITMENT) != record["commitment_sha256"]:
            print("iter222 committed commitment digest differs from the record")
            return 1
        print(f"iter222 transparency timestamp re-verified (stamped {record['timestamp_utc']})")
        return 0

    PROOF.mkdir(parents=True, exist_ok=True)
    try:
        record = build()
    except Exception as error:  # noqa: BLE001 — a blocked result is a legitimate outcome
        blocked = {
            "schema_version": "telos.iter222.transparency_timestamp.v1",
            "status": "blocked",
            "reason": f"{type(error).__name__}: {error}",
            "verified": False,
        }
        RECORD.write_text(json.dumps(blocked, indent=1, sort_keys=True) + "\n", encoding="utf-8")
        print(f"iter222 transparency timestamp BLOCKED: {blocked['reason']}")
        return 1

    RECORD.write_text(json.dumps(record, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    if not record["verified"]:
        print("iter222 transparency timestamp token did not verify")
        return 1
    print(f"iter222 transparency timestamp written and verified (stamped {record['timestamp_utc']})")
    print(f"  token sha256: {record['token_sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
