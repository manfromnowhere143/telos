#!/usr/bin/env python3
"""Build the reviewed Iter242-to-Iter243 public-claim migration."""

from __future__ import annotations

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts import build_iter241_claim_migration as base  # noqa: E402


FROM_GATE = "experiments/iter242_iter241_successor_closure/HYPOTHESIS.md"
TO_GATE = "experiments/iter243_iter242_remote_ci_recovery/HYPOTHESIS.md"
PRIOR_CANONICAL_SHA256 = (
    "411f63e5a2c54e24df6c4a2e3f6403d82e2fa72f8d45bb6c81da6693b3958a97"
)
PRIOR_EVIDENCE = {
    "commit": "5d81a2c844483b8451505ea61ded3dec271dc14e",
    "registry_path": "mission/claim_registry.json",
    "registry_sha256": (
        "092358f13d6011080b459a0d25ac643ae7b330a1f9a10402c4cdda1d7b157cc3"
    ),
    "coverage_report_path": (
        "experiments/iter242_iter241_successor_closure/proof/"
        "claim_coverage_report.json"
    ),
    "coverage_report_sha256": (
        "b83c534a3ba46b7350dc747e2bb73c598df14d03433117292065915a6fa6e5b6"
    ),
    "report_seal_id": "iter242-completed-evidence-seal",
}
EXPECTED_AUTHORIZATION = (
    "eedc04493e512b22e5341c4b2036e4060bfb724f743e13c507d74b716c46feec"
)


def configure() -> None:
    """Bind the generic reviewed migration builder to the Iter243 transition."""

    experiment = ROOT / "experiments/iter243_iter242_remote_ci_recovery"
    base.PLAN = experiment / "proof/claim_registry_migration.json"
    base.REPORT = experiment / "proof/claim_coverage_report.json"
    base.REGISTRY = ROOT / "mission/claim_registry.json"
    base.FROM_GATE = FROM_GATE
    base.TO_GATE = TO_GATE
    base.PRIOR_CANONICAL_SHA256 = PRIOR_CANONICAL_SHA256
    base.PRIOR_EVIDENCE = PRIOR_EVIDENCE
    base.EXPECTED_AUTHORIZATION = EXPECTED_AUTHORIZATION
    base.MIGRATION_LABEL = "iter243"
    base.REPLACEABLE_REGISTRY_DESCRIPTION = (
        "the sealed Iter242 authority nor an exact reviewed Iter243 transition"
    )
    base.REPLACEABLE_REGISTRY_SHA256 = {
        "67e71da83ed4985cfbe0d93eaa7eb64ec3129cfdbe03780bd4c58b6f826e87da",
        "cc3a243baceffd78bdb62e7806c8f9bb4693e04491e9adfc9bce3d37c579b7e2",
    }
    base.REPLACEABLE_PLAN_SHA256 = {
        "6fae3e21318fcdfdfb7dd52c9952f4a7219eba3b752f636a2279f21048de78fe",
        "2a889bc92271476af56bcdbbe003b95ce61695f1eb70064022987ab3a2437f18",
    }


def main() -> int:
    configure()
    return base.main()


if __name__ == "__main__":
    raise SystemExit(main())
