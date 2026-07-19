#!/usr/bin/env python3
"""Validate the current paper/claim surfaces without rewriting historical proof."""

from __future__ import annotations

import hashlib
import re
from pathlib import Path


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
        "iter237 truth maintenance is the active gate",
        "cross-solver recurrence on one fixed fifty-three-target cohort",
        "`5/29`, `2/25`, `3/17`, `4/14`, and `1/16`",
        "fresh-cohort concentration and causal repository explanations are `inconclusive`",
        "transfer is `untested`",
        "flag rates, not validated false-positive rates",
        "Iter192's overbroad novelty interpretation is conservatively adjudicated `FAIL`",
        "literal v1-specific falsifier trigger is indeterminate",
        "Iter195 is protocol `FAIL`",
        "design is post-provider and pre-execution",
        "partial/protocol-blocked Detector A only",
        "shared-gold-line diagnostic triggers",
        "Historical image provenance is bounded",
        "SOURCE_DATE_EPOCH=1784419200 tectonic telos.tex",
        "29451691560",
        "29452243832",
        "29460393525",
        "29465584664",
        "29465924803",
        "29468769187",
        "314141096",
        "stderr was not retained",
        "both complete histories are empty",
        "comparison establishes an effect direction or magnitude",
        "frozen closure snapshot",
        "No iter205 dispatch request was issued",
        "no dispatch API response or rejection exists",
        "bibliography contains eighteen entries",
    ),
    ROOT / "README.md": (
        "22`-row, `8`-repository reference-differential corpus",
        "Iter192 is conservatively adjudicated `FAIL`",
        "literal v1-specific",
        "falsifier remains indeterminate",
        "$13.128090` for `240` score-producing calls",
        "iter195 gate",
        "not independently adjudicated semantic ground truth",
        "Iter206 was sealed locally",
        "iter207_claim_integrity_and_admission_recovery",
        "exact historical container bytes are not reconstructible",
        "provider-complete safety null",
        "Iter222 filled three TCP-1 admission gates",
        "scientific execution remains blocked",
        "moving TCP-1 admission from `2/11` to `5/11` while keeping execution unauthorized",
        "Artifact-bound receipt v2",
        "post-seal forensic correction",
        "iter209 publication CI recovery",
        "iter211 TCP-1 materialization preflight",
        "iter213 iter211 post-seal validation recovery",
        "iter214 TCP-1 cross-platform numeric recovery",
        # The null's two load-bearing sentences.  A reader who sees only the forward yield
        # and the cross-repository control would read a 10^-24 effect that is not there.
        "tests added *before* the task reference them at `0.4336`",
        "artifact of a control that cannot fail for the right reason",
        "the underlying harvest idea is untested and remains open",
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
