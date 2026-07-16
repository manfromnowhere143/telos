#!/usr/bin/env python3
"""Validate the current paper/claim surfaces without rewriting historical proof."""

from __future__ import annotations

import hashlib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PAPER_SOURCE = ROOT / "paper/telos.tex"
PAPER_PDF = ROOT / "paper/telos.pdf"
EXPECTED_SOURCE_SHA256 = "0c79ea20a0cfabe402222c76558020ff921b5206e7770e346d5a2dcf0d3f0e43"
EXPECTED_PDF_SHA256 = "d992d1088e47a4a1437e0c69592e5d740b1a018f42d206210ce7932fef401bb4"

REQUIRED_TEXT = {
    PAPER_SOURCE: (
        r"\date{July 16, 2026}",
        "twenty-two patches across eight repositories",
        "$20/22$",
        "$8/88$",
        "$3/19$",
        "$1/24$",
        "$7/24$",
        "$1/18$",
        "locator-assisted,",
        "gold-validated property pipeline",
        "iter193--iter199 construction",
        r"mutable \texttt{:latest}",
        "exact historical container bytes",
        "scenario-safety protocol/execution null",
        "post-provider iter203 recovery",
        "Iter203 is an execution-infrastructure null",
        "public workflow-dispatch count at closure is zero",
        "closure snapshot contains two public push records",
        "Iter204 is a pre-dispatch infrastructure null",
        "No iter205 dispatch request",
        "no dispatch API response or rejection exists",
        "Iter205 is a",
        "pre-dispatch admission-history null",
        "Iter206 is the pending exact-six admission recovery",
    ),
    ROOT / "paper/README.md": (
        "current through the iter205 pre-dispatch admission-history null; iter206 remains pre-result",
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
        "frozen closure snapshot",
        "No iter205 dispatch request was issued",
        "no dispatch API response or rejection exists",
    ),
    ROOT / "README.md": (
        "22` execution-verified certified-resolved reward hacks across `8` repositories",
        "exact historical container bytes are not reconstructible",
        "provider-complete safety null",
    ),
    ROOT / "benchmarks/certified_resolved_reward_hack_v2/README.md": (
        "reference-differential operational label",
        "mutable `:latest`",
        "no resolved image digest",
        "interpretation limit rather than a second protocol deviation",
    ),
    ROOT / "experiments/iter195_synthesized_input_differential_oracle/RESULT.md": (
        "Standing provenance correction (2026-07-15)",
        "not immutable image provenance",
    ),
    ROOT / "experiments/iter199_benchmark_expansion_across_repos/RESULT.md": (
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
    ),
    ROOT / "paper/README.md": (
        "No iter205 request, API rejection",
        "No iter205 API request",
        "pre-request admission-history null",
    ),
    ROOT / "benchmarks/certified_resolved_reward_hack_v2/README.md": (
        "pinned-container execution",
        "used gold during property inclusion and therefore record protocol `FAIL`",
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
