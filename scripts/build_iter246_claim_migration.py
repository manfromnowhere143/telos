#!/usr/bin/env python3
"""Build the reviewed Iter245-to-Iter246 public-claim migration."""

from __future__ import annotations

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts import build_iter241_claim_migration as base  # noqa: E402


FROM_GATE = "experiments/iter245_offline_verified_python_bootstrap/HYPOTHESIS.md"
TO_GATE = "experiments/iter246_iter245_baton_refresh/HYPOTHESIS.md"
PRIOR_CANONICAL_SHA256 = (
    "eac4f8c792854ecb9c2ac08232b39d3164b711dd3dfad1e117ac9aeb0d7616b5"
)
PRIOR_EVIDENCE = {
    "commit": "27ce35b5494440e8ce14e8d086f6af2d67c9e847",
    "registry_path": "mission/claim_registry.json",
    "registry_sha256": (
        "e884ee69d39b8c96908cbf0d913649f4fbc42d823ff1ce5c149a370c26759749"
    ),
    "coverage_report_path": (
        "experiments/iter245_offline_verified_python_bootstrap/proof/"
        "claim_coverage_report.json"
    ),
    "coverage_report_sha256": (
        "fa64ef20ea1df2f960390e83a6e2f4b7f78d37db7b5439dfe4594b49b584fca7"
    ),
    "report_seal_id": "iter245-completed-evidence-seal",
}
EXPECTED_AUTHORIZATION = (
    "e8744867aa9228157d89805d022473c9bb4808dc37487eed0b45021d5b6cc252"
)


def configure() -> None:
    """Bind the generic reviewed migration builder to the Iter246 transition."""

    experiment = ROOT / "experiments/iter246_iter245_baton_refresh"
    base.PLAN = experiment / "proof/claim_registry_migration.json"
    base.REPORT = experiment / "proof/claim_coverage_report.json"
    base.REGISTRY = ROOT / "mission/claim_registry.json"
    base.FROM_GATE = FROM_GATE
    base.TO_GATE = TO_GATE
    base.PRIOR_CANONICAL_SHA256 = PRIOR_CANONICAL_SHA256
    base.PRIOR_EVIDENCE = PRIOR_EVIDENCE
    base.EXPECTED_AUTHORIZATION = EXPECTED_AUTHORIZATION
    base.MIGRATION_LABEL = "iter246"
    base.REPLACEABLE_REGISTRY_DESCRIPTION = (
        "the sealed Iter245 authority nor an exact reviewed Iter246 transition"
    )
    base.REPLACEABLE_REGISTRY_SHA256 = set()
    base.REPLACEABLE_PLAN_SHA256 = set()


def main() -> int:
    configure()
    return base.main()


if __name__ == "__main__":
    raise SystemExit(main())
