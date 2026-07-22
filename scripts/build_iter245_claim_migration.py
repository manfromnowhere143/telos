#!/usr/bin/env python3
"""Build the reviewed Iter243-to-Iter245 public-claim migration."""

from __future__ import annotations

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts import build_iter241_claim_migration as base  # noqa: E402


FROM_GATE = "experiments/iter243_iter242_remote_ci_recovery/HYPOTHESIS.md"
TO_GATE = "experiments/iter245_offline_verified_python_bootstrap/HYPOTHESIS.md"
PRIOR_CANONICAL_SHA256 = (
    "82a2dd92546ba11caa799f8e0485813d8e030ab2b244c7171a9c9e19a1e46fce"
)
PRIOR_EVIDENCE = {
    "commit": "02f89c21a7c2e89a287f4946f44414a98210ea03",
    "registry_path": "mission/claim_registry.json",
    "registry_sha256": (
        "12aa1fde5594ec77e92bfaab9060bcebe36f5285317346e670504d738cfc603c"
    ),
    "coverage_report_path": (
        "experiments/iter243_iter242_remote_ci_recovery/proof/"
        "claim_coverage_report.json"
    ),
    "coverage_report_sha256": (
        "8e56f7547bc3ae16bb7f8d65810754fc05bbdfeeb0602e348cde3913cfa90476"
    ),
    "report_seal_id": "iter243-completed-evidence-seal",
}
EXPECTED_AUTHORIZATION = (
    "c97fe9256390a50778f491b1c7a9821fc7591d6322a8e815b317331edf5e2b84"
)


def configure() -> None:
    """Bind the generic reviewed migration builder to the Iter245 transition."""

    experiment = ROOT / "experiments/iter245_offline_verified_python_bootstrap"
    base.PLAN = experiment / "proof/claim_registry_migration.json"
    base.REPORT = experiment / "proof/claim_coverage_report.json"
    base.REGISTRY = ROOT / "mission/claim_registry.json"
    base.FROM_GATE = FROM_GATE
    base.TO_GATE = TO_GATE
    base.PRIOR_CANONICAL_SHA256 = PRIOR_CANONICAL_SHA256
    base.PRIOR_EVIDENCE = PRIOR_EVIDENCE
    base.EXPECTED_AUTHORIZATION = EXPECTED_AUTHORIZATION
    base.MIGRATION_LABEL = "iter245"
    base.REPLACEABLE_REGISTRY_DESCRIPTION = (
        "the sealed Iter243 authority nor an exact reviewed Iter245 transition"
    )
    base.REPLACEABLE_REGISTRY_SHA256 = {
        "cdda0723ee47e507890583f63c5946799aa487da837196d2f12740b165d67ce4",
        "e47ff907bb5f33e26e940feb324d3c45ee34417a867506a1177f92c165af5406",
    }
    base.REPLACEABLE_PLAN_SHA256 = {
        "840bfc6a0dcaf05189e90b9bc3dde9e55ff3163b4278653fc79c7e05a5bd03cf",
    }


def main() -> int:
    configure()
    return base.main()


if __name__ == "__main__":
    raise SystemExit(main())
