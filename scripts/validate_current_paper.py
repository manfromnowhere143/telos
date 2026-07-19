#!/usr/bin/env python3
"""Validate the current paper/claim surfaces without rewriting historical proof."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from pathlib import PurePosixPath


ROOT = Path(__file__).resolve().parents[1]
PAPER_SOURCE = ROOT / "paper/telos.tex"
PAPER_PDF = ROOT / "paper/telos.pdf"
EXPECTED_SOURCE_SHA256 = "0bccdec8397f085e0d9a981f51403780c2c346aab0a2eb1cd8c38e7b64d6ae58"
EXPECTED_PDF_SHA256 = "21a3505d1819b913e0159f73a29a1a0329f43c8bc58a63734d49e68b8cecfed8"

REQUIRED_TEXT = {
    PAPER_SOURCE: (
        r"\date{July 19, 2026}",
        "Certified-Resolved SWE-bench Patches",
        "Construction, Cross-Solver Recurrence, and Exploratory Detection",
        "twenty-two constructed patches across eight repositories",
        r"conservatively adjudicate iter192's overbroad novelty interpretation \texttt{FAIL}",
        "literal v1-specific",
        "falsifier remains indeterminate",
        r"estimated spend guard of \$13.128090, not a provider invoice",
        r"\$13.59 rounded through-repair total",
        "Iter195 protocol failure",
        "supplied both gold and variant hunks",
        "not a validated synthesized-input oracle",
        "post-provider, pre-execution stated design",
        "partial, protocol-blocked result",
        "shared-gold-line diagnostic on four hack prompts",
        "does not establish effect direction or magnitude",
        "$20/22$",
        "$8/88$",
        "$3/19$",
        "$k=2$, $N=24$, and $u=1$",
        "$2/24$ observed",
        "$3/24$ under the least-favourable assignment",
        "$2/23$ complete-case",
        "locator-assisted,",
        "gold-validated property pipeline",
        "iter193--iter199 construction and witness execution",
        r"mutable \texttt{:latest}",
        "exact historical container bytes",
        "We therefore make no priority or state-of-the-art claim",
        "forensic real-task case series",
        "no causal direction or magnitude is established",
        "fresh tasks, pre-authored consequence tests",
        r"\bibitem{openai2026pro}",
        r"\bibitem{zhao2026specbench}",
        r"\bibitem{atinafu2026rewardhackingagents}",
        r"\bibitem{roth2026hackverifiable}",
        r"\bibitem{rabanser2026reliability}",
        r"\bibitem{lynch2026misalignment}",
        "A safety-aware scaled replication",
        "$k=5$, $N=29$, and $u=0$",
        "Fresh-cohort observations are inconclusive under missingness",
        "$k=0$, $N=37$, and $u=13$",
        "least-favourable endpoint is $13/37$",
        "$17/125$ is therefore descriptive pipeline yield",
        "Mann--Whitney $U=331$, asymptotic two-sided $p=0.005347$",
        "transfer remains untested",
        "twenty-nine are normalized-identical to accepted patches",
        "control flag rate, not a validated false-positive rate",
        "not an impossibility result or a ceiling",
        "empirical case for independently-authored held-out consequence tests",
        "We report five results",
        "Cross-solver recurrence on a fixed cohort",
        "$5/29$ with $u=0$",
        "$2/25$ with $u=2$",
        "$3/17$ with $u=2$",
        "$4/14$ with $u=2$",
        "$1/16$ with $u=1$",
        "seventeen patch-level positives but only twelve unique tasks",
        "independent, blinded human semantic re-adjudication at unique-task level",
    ),
    ROOT / "paper/README.md": (
        "# Telos paper",
        "Iter238 claim, seal, and workflow controls are the active engineering gate",
        "Iter237 rebuilt and rebound the July 19 source and 16-page PDF",
        "The claim registry is the canonical reviewed resolution authority; "
        "the active-gate coverage report is retained evidence that the "
        "declared surfaces resolve against it",
        "This page is a build and release guide, not a second empirical-results ledger",
        "It is itself a declared public claim surface",
        "mission/claim_registry.json",
        "paper/telos.tex",
        "docs/EXPERIMENT_INDEX.md",
        "SOURCE_DATE_EPOCH=1784419200 tectonic telos.tex",
        "Two consecutive Tectonic builds must have identical SHA-256 digests",
        "The paper is not submission-ready",
        "independent semantic ground truth",
        "No submission, release, provider call, scientific rerun, or purchase is authorized",
    ),
    ROOT / "README.md": (
        "## Current scientific boundary",
        "`5/29`",
        "`2/25`",
        "`3/17`",
        "`4/14`",
        "`1/16`",
        "`k=0`, `N=37`, and `u=13`",
        "`U=331`",
        "`p=0.005347`",
        "transfer is **untested**, not negative",
        "`29` are normalized-identical",
        "`25` only showed no divergence",
        "not independent semantic ground truth",
        "mission/claim_registry.json",
        "mission/seal_registry.json",
        "mission/workflow_registry.json",
        "docs/EXPERIMENT_INDEX.md",
        "experiments/iter238_claim_seal_workflow_controls/HYPOTHESIS.md",
        "22`-row, `8`-repository reference-differential corpus",
        "Iter192 is conservatively adjudicated `FAIL`",
        "literal v1-specific",
        "falsifier remains indeterminate",
        "iter195 gate",
        "not independently adjudicated semantic ground truth",
        "exact historical container bytes are not reconstructible",
        "provider-complete safety null",
        "Iter222 filled three TCP-1 admission gates",
        "scientific execution remains blocked",
        "Artifact-bound receipt v2",
        "post-seal forensic correction",
        "iter209 publication CI recovery",
        "iter211 TCP-1 materialization preflight",
        "iter213 post-seal validation recovery",
        "iter214 cross-platform numeric recovery",
        "iter219 temporal consequence-test yield",
    ),
    ROOT / "benchmarks/certified_resolved_reward_hack_v2/README.md": (
        "certified-resolved reference-differential witness under the benchmark's operational label",
        "semantic ground-truth set",
        "mutable `:latest`",
        "no resolved image digest",
        "interpretation limit rather than a second protocol deviation",
    ),
    ROOT / "experiments/iter195_synthesized_input_differential_oracle/RESULT.md": (
        "Standing protocol correction (2026-07-16)",
        "Status: `FAIL` against the frozen protocol",
        "Standing provenance correction (2026-07-15)",
        "retained no resolved image digest",
    ),
    ROOT / "experiments/iter192_reward_hack_benchmark_construct_validity_audit/RESULT.md": (
        "conservative novelty adjudication `FAIL`",
        "literal frozen falsifier 5 trigger indeterminate",
        "$13.128090` for `240` score-producing calls",
        "not a provider invoice",
    ),
    ROOT / "experiments/iter199_benchmark_expansion_across_repos/RESULT.md": (
        "Standing chronology correction (2026-07-16)",
        "independently Git-frozen before provider output",
        "Standing provenance correction (2026-07-15)",
        "not immutable image provenance",
    ),
}

FORBIDDEN_TEXT = {
    PAPER_SOURCE: (
        r"\date{\today}",
        "verified in pinned containers",
        "each instance's pinned container",
        "No iter205 request, API rejection",
        "pre-request admission-history null",
        "Every number in this paper regenerates",
        r"iter192 audit is protocol \texttt{FAIL}",
        r"metered cost of \$13.59",
        "depress recall",
        "possible downward recall bias",
        "may bias recall downward",
        r"$p=0.008$",
        "five independently-trained frontier models",
        "the phenomenon concentrates in particular repositories",
        "the argument is airtight",
    ),
    ROOT / "paper/README.md": (
        "No iter205 request, API rejection",
        "No iter205 API request",
        "pre-request admission-history null",
        "Iter192 is protocol `FAIL`",
        "depress recall",
        "possible downward recall bias",
        "may bias recall downward",
        "source and PDF are deliberately not represented as a synchronized release",
    ),
    ROOT / "benchmarks/certified_resolved_reward_hack_v2/README.md": (
        "pinned-container execution",
        "used gold during property inclusion and therefore record protocol `FAIL`",
    ),
    ROOT / "README.md": (
        "iter192 is strict protocol `FAIL`",
        "unrepaired `majority_catch` (iter179) | `17/40` | `$13.59`",
        "may bias recall downward",
    ),
}


def normalized_prose(path: Path) -> str:
    """Read markdown as one line, with blockquote markers removed.

    A phrase that wraps inside a blockquote normalizes to "right > reason" and silently
    fails a required-text scan even though the prose is correct.  This repository has now
    lost a publication seal to a line wrap once and hit the same class of defect twice
    more, so strip the marker here rather than depend on prose staying hand-reflowed.
    """

    lines = [re.sub(r"^\s*>+\s?", "", line) for line in path.read_text(encoding="utf-8").splitlines()]
    return " ".join(" ".join(lines).split())


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def active_claim_report_path() -> str:
    """Derive the active-gate report path from both current authorities."""

    current = json.loads((ROOT / "mission/current.json").read_text(encoding="utf-8"))
    registry_path = current.get("claim_registry")
    active_gate = current.get("active_gate")
    if (
        not isinstance(registry_path, str)
        or registry_path != "mission/claim_registry.json"
        or not isinstance(active_gate, str)
    ):
        raise ValueError("current claim authority pointers are invalid")
    registry = json.loads((ROOT / registry_path).read_text(encoding="utf-8"))
    if registry.get("active_gate") != active_gate:
        raise ValueError("claim registry active gate differs from current pointer")
    gate = PurePosixPath(active_gate)
    if (
        gate.is_absolute()
        or gate.name != "HYPOTHESIS.md"
        or len(gate.parts) != 3
        or gate.parts[0] != "experiments"
        or not gate.parts[1].startswith("iter")
        or gate.as_posix() != active_gate
    ):
        raise ValueError("active gate is not a canonical experiment hypothesis")
    expected = (gate.parent / "proof" / "claim_coverage_report.json").as_posix()
    if registry.get("coverage_report_path") != expected:
        raise ValueError("claim registry coverage report path differs")
    return expected


def validate() -> list[str]:
    failures: list[str] = []
    for path, snippets in REQUIRED_TEXT.items():
        text = normalized_prose(path)
        for snippet in snippets:
            if snippet not in text:
                failures.append(f"{path.relative_to(ROOT)} missing current paper text: {snippet}")
    for path, snippets in FORBIDDEN_TEXT.items():
        text = normalized_prose(path)
        for snippet in snippets:
            if snippet in text:
                failures.append(f"{path.relative_to(ROOT)} retains stale paper text: {snippet}")
    if sha256(PAPER_SOURCE) != EXPECTED_SOURCE_SHA256:
        failures.append("paper/telos.tex changed without refreshing the current-paper binding")
    if not PAPER_PDF.read_bytes().startswith(b"%PDF-"):
        failures.append("paper/telos.pdf is not a PDF artifact")
    if sha256(PAPER_PDF) != EXPECTED_PDF_SHA256:
        failures.append("paper/telos.pdf changed without a deterministic rebuild/binding refresh")
    try:
        report_path = active_claim_report_path()
    except (OSError, json.JSONDecodeError, ValueError) as error:
        failures.append(f"paper claim-report authority is invalid: {error}")
    else:
        paper_readme = normalized_prose(ROOT / "paper/README.md")
        if f"(../{report_path})" not in paper_readme:
            failures.append(
                "paper/README.md does not link the exact active-gate claim "
                f"coverage report: {report_path}"
            )
    return failures


def main() -> int:
    failures = validate()
    if failures:
        print("current paper guard failed:")
        for failure in failures:
            print(f" - {failure}")
        return 1
    print(
        "current paper guard: pass "
        f"(source={EXPECTED_SOURCE_SHA256[:12]} pdf={EXPECTED_PDF_SHA256[:12]})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
