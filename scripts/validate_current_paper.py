#!/usr/bin/env python3
"""Validate the current paper/claim surfaces without rewriting historical proof."""

from __future__ import annotations

import hashlib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PAPER_SOURCE = ROOT / "paper/telos.tex"
PAPER_PDF = ROOT / "paper/telos.pdf"
EXPECTED_SOURCE_SHA256 = "383f00dc8fb835c83f3b8b27bd5b58c1999017af61976a6dcf76f085e5daa0b8"
EXPECTED_PDF_SHA256 = "75888392584a093d5d2e82ef5d969ffc88211bd4bb3d970dd7a1256981d9671d"

REQUIRED_TEXT = {
    PAPER_SOURCE: (
        r"\date{July 16, 2026}",
        "Certified-Resolved SWE-bench Patches",
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
        "$1/24$",
        "$7/24$",
        "$1/18$",
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
        "Iter202 through iter207 produced only safety, infrastructure,",
    ),
    ROOT / "paper/README.md": (
        "iter207 is a sealed local correction baseline; iter208 passed local forensic correction",
        "Iter192's overbroad novelty interpretation is conservatively adjudicated `FAIL`",
        "literal v1-specific falsifier trigger is indeterminate",
        "Iter195 is protocol `FAIL`",
        "design is post-provider and pre-execution",
        "partial/protocol-blocked Detector A only",
        "shared-gold-line diagnostic triggers",
        "Historical image provenance is bounded",
        "SOURCE_DATE_EPOCH=1784160000 tectonic telos.tex",
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
        "TCP-1 materialization preflight PASS — scientific execution BLOCKED",
        "Artifact-bound receipt v2",
        "post-seal forensic correction",
        "iter209 publication CI recovery",
        "iter211 TCP-1 materialization preflight",
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
    ),
    ROOT / "paper/README.md": (
        "No iter205 request, API rejection",
        "No iter205 API request",
        "pre-request admission-history null",
        "Iter192 is protocol `FAIL`",
        "depress recall",
        "possible downward recall bias",
        "may bias recall downward",
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


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate() -> list[str]:
    failures: list[str] = []
    for path, snippets in REQUIRED_TEXT.items():
        text = " ".join(path.read_text(encoding="utf-8").split())
        for snippet in snippets:
            if snippet not in text:
                failures.append(f"{path.relative_to(ROOT)} missing current paper text: {snippet}")
    for path, snippets in FORBIDDEN_TEXT.items():
        text = " ".join(path.read_text(encoding="utf-8").split())
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
