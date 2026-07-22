#!/usr/bin/env python3
"""Build the reviewed Iter241-to-Iter242 public-claim migration."""

from __future__ import annotations

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts import build_iter241_claim_migration as base  # noqa: E402


FROM_GATE = "experiments/iter241_iter240_repository_closure/HYPOTHESIS.md"
TO_GATE = "experiments/iter242_iter241_successor_closure/HYPOTHESIS.md"
PRIOR_CANONICAL_SHA256 = (
    "254142d7bb103c49f2063177c1baf586f42e29d7b9c7d9cf33eadb9bee091bb7"
)
PRIOR_EVIDENCE = {
    "commit": "09da0b64331d0f39980843ef48d6b7fd536cab0e",
    "registry_path": "mission/claim_registry.json",
    "registry_sha256": (
        "53f1db3723387c740abc97f7e836a120986206255cd009f4d0084ef560818803"
    ),
    "coverage_report_path": (
        "experiments/iter241_iter240_repository_closure/proof/"
        "claim_coverage_report.json"
    ),
    "coverage_report_sha256": (
        "5130ba3f0fcaec344c2e64abc4de26ffc64ee3d45a40be2b09bf6e84320cc2f6"
    ),
    "report_seal_id": "iter241-completed-evidence-seal",
}
EXPECTED_AUTHORIZATION = (
    "562d844f2e4b1e4880d876b3ee40df3c4c5a353473684a1ebc27ce426147a988"
)


def configure() -> None:
    """Bind the generic reviewed migration builder to the Iter242 transition."""

    experiment = ROOT / "experiments/iter242_iter241_successor_closure"
    base.PLAN = experiment / "proof/claim_registry_migration.json"
    base.REPORT = experiment / "proof/claim_coverage_report.json"
    base.REGISTRY = ROOT / "mission/claim_registry.json"
    base.FROM_GATE = FROM_GATE
    base.TO_GATE = TO_GATE
    base.PRIOR_CANONICAL_SHA256 = PRIOR_CANONICAL_SHA256
    base.PRIOR_EVIDENCE = PRIOR_EVIDENCE
    base.EXPECTED_AUTHORIZATION = EXPECTED_AUTHORIZATION
    base.MIGRATION_LABEL = "iter242"
    base.REPLACEABLE_REGISTRY_DESCRIPTION = (
        "the sealed iter241 authority nor an exact reviewed intermediate "
        "iter242 transition"
    )
    base.REPLACEABLE_REGISTRY_SHA256 = {
        "7d45335de0456d17cad613da1b220ee41745d5946f62018708aa43cc93027bc9"
    }


def main() -> int:
    configure()
    return base.main()


if __name__ == "__main__":
    raise SystemExit(main())
