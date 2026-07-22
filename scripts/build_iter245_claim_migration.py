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
    "333eebc2ae21ea15b2cf8b884431176ba65f07767e39762b82a353a50987c876"
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
    base.REPLACEABLE_REGISTRY_SHA256 = set()
    base.REPLACEABLE_PLAN_SHA256 = set()


def main() -> int:
    configure()
    return base.main()


if __name__ == "__main__":
    raise SystemExit(main())
