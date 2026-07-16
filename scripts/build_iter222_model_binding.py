#!/usr/bin/env python3
"""Bind one open-weight model's identity from the live HuggingFace public record.

Every field is retrieved from the HuggingFace API at run time and recorded verbatim.  No
weight bytes are downloaded, and no digest is authored by this repository: a fabricated
digest fails against the live service, which is the point (Standard 9).

A published digest proves byte identity of the served artifact.  It does not prove the
model loads, runs, or has any capability.  That limitation is recorded in the output.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import urllib.request
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
EXPERIMENT = ROOT / "experiments/iter222_tcp1_agent_solvable_admission_evidence"
OUTPUT = EXPERIMENT / "proof/model_binding.json"

HF_API = "https://huggingface.co/api/models/"

# A source-linked candidate menu, frozen before retrieval.  Each is a permissively licensed
# open-weight instruction model with a public, authoritative training-cutoff source.  The
# default is the first entry; the menu is recorded so the choice is auditable.
CANDIDATES = [
    {
        "model_id": "Qwen/Qwen2.5-7B-Instruct",
        "expected_license": "apache-2.0",
        "cutoff_source": (
            "Qwen2.5 Technical Report (arXiv:2412.15115), Section 3.1: pretraining data "
            "cutoff stated; model card at https://huggingface.co/Qwen/Qwen2.5-7B-Instruct"
        ),
    },
    {
        "model_id": "mistralai/Mistral-7B-Instruct-v0.3",
        "expected_license": "apache-2.0",
        "cutoff_source": (
            "Mistral AI model card and release notes at "
            "https://huggingface.co/mistralai/Mistral-7B-Instruct-v0.3"
        ),
    },
    {
        "model_id": "meta-llama/Llama-3.1-8B-Instruct",
        "expected_license": "llama3.1",
        "cutoff_source": (
            "Llama 3.1 model card, 'Training Data' knowledge cutoff at "
            "https://huggingface.co/meta-llama/Llama-3.1-8B-Instruct"
        ),
        "license_note": "community license, not SPDX Apache/MIT; menu-only, not the default",
    },
]

WEIGHT_SUFFIXES = (".safetensors", ".bin", ".gguf")
TOKENIZER_NAMES = ("tokenizer.json", "tokenizer.model", "vocab.json", "merges.txt")


def fetch_model(model_id: str) -> dict[str, Any]:
    url = f"{HF_API}{model_id}?blobs=true"
    with urllib.request.urlopen(url, timeout=45) as response:
        return json.load(response)


def extract_binding(model_id: str, cutoff_source: str, payload: dict[str, Any]) -> dict[str, Any]:
    siblings = payload.get("siblings", [])
    weight_digests: dict[str, str] = {}
    tokenizer_digests: dict[str, str] = {}
    for sibling in siblings:
        name = sibling.get("rfilename", "")
        digest = (sibling.get("lfs") or {}).get("sha256")
        if not digest:
            continue
        if name.endswith(WEIGHT_SUFFIXES):
            weight_digests[name] = digest
        elif name in TOKENIZER_NAMES:
            tokenizer_digests[name] = digest
    # Small tokenizer files are not LFS-tracked and carry no sha256 in the listing; record
    # their presence so the absence of a digest is explained, never silently dropped.
    tokenizer_present = sorted(
        s.get("rfilename", "")
        for s in siblings
        if s.get("rfilename", "") in TOKENIZER_NAMES
    )
    license_id = payload.get("cardData", {}).get("license") or payload.get("license")
    return {
        "model_id": model_id,
        "resolved_commit_sha": payload.get("sha"),
        "license": license_id,
        "cutoff_source": cutoff_source,
        "weight_file_count": len(weight_digests),
        "weight_sha256": dict(sorted(weight_digests.items())),
        "tokenizer_files_present": tokenizer_present,
        "tokenizer_sha256": dict(sorted(tokenizer_digests.items())),
        "retrieved_from": f"{HF_API}{model_id}?blobs=true",
    }


def build() -> dict[str, Any]:
    menu = []
    for candidate in CANDIDATES:
        payload = fetch_model(candidate["model_id"])
        entry = {
            "model_id": candidate["model_id"],
            "resolved_commit_sha": payload.get("sha"),
            "license": payload.get("cardData", {}).get("license") or payload.get("license"),
            "expected_license": candidate["expected_license"],
            "cutoff_source": candidate["cutoff_source"],
        }
        if "license_note" in candidate:
            entry["license_note"] = candidate["license_note"]
        menu.append(entry)

    default_id = CANDIDATES[0]["model_id"]
    default_payload = fetch_model(default_id)
    default_binding = extract_binding(
        default_id, CANDIDATES[0]["cutoff_source"], default_payload
    )

    record = {
        "schema_version": "telos.iter222.model_binding.v1",
        "gate": "experiments/iter222_tcp1_agent_solvable_admission_evidence/HYPOTHESIS.md",
        "candidate_menu": menu,
        "default_model": default_binding,
        "digest_meaning": (
            "Each sha256 is the HuggingFace-published digest of the served artifact, "
            "retrieved live. It proves byte identity of what the service serves under this "
            "name at this commit. It does NOT prove the model loads, runs, or has any "
            "capability, and it is not a training-provenance or license-compliance proof."
        ),
        "weights_downloaded": False,
        "provider_calls": 0,
        "gpu_allocations": 0,
    }
    canonical = json.dumps(record, sort_keys=True, separators=(",", ":")).encode()
    record["binding_sha256"] = hashlib.sha256(canonical).hexdigest()
    return record


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check", action="store_true", help="validate the committed binding instead of writing it"
    )
    args = parser.parse_args()

    if args.check:
        if not OUTPUT.exists():
            print("iter222 model binding missing")
            return 1
        record = json.loads(OUTPUT.read_text(encoding="utf-8"))
        stored = record.get("binding_sha256")
        recomputed = dict(record)
        recomputed.pop("binding_sha256", None)
        canonical = json.dumps(recomputed, sort_keys=True, separators=(",", ":")).encode()
        if hashlib.sha256(canonical).hexdigest() != stored:
            print("iter222 model binding digest does not recompute")
            return 1
        default = record["default_model"]
        if not default.get("weight_sha256") or not default.get("resolved_commit_sha"):
            print("iter222 model binding is missing weight digests or commit sha")
            return 1
        if len(record.get("candidate_menu", [])) < 3:
            print("iter222 model binding menu has fewer than three candidates")
            return 1
        print(
            f"iter222 model binding verified: {default['model_id']} "
            f"@ {default['resolved_commit_sha'][:12]} "
            f"({default['weight_file_count']} weight shards, license {default['license']})"
        )
        return 0

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    record = build()
    OUTPUT.write_text(json.dumps(record, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    default = record["default_model"]
    print(f"iter222 model binding written: {default['model_id']}")
    print(f"  commit: {default['resolved_commit_sha']}")
    print(f"  license: {default['license']}  weight shards: {default['weight_file_count']}")
    print(f"  binding sha256: {record['binding_sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
