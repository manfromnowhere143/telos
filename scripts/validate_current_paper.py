#!/usr/bin/env python3
"""Validate the current paper/claim surfaces without rewriting historical proof."""

from __future__ import annotations

import hashlib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PAPER_SOURCE = ROOT / "paper/telos.tex"
PAPER_PDF = ROOT / "paper/telos.pdf"
EXPECTED_SOURCE_SHA256 = "141ceaf867412ea39f1d0491eadd0a9b6f29561b50be1780b273a107bb9afd08"
EXPECTED_PDF_SHA256 = "fc8a7d25a066ba490f5e089d0eb4166c2242a123b19fa28b785c02bffee00fbb"

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
        "iter204 runtime recovery is pre-result",
    ),
    ROOT / "paper/README.md": (
        "current through the iter203 infrastructure null; iter204 remains pre-result",
        "Historical image provenance is bounded",
        "SOURCE_DATE_EPOCH=1784160000 tectonic telos.tex",
        "29451691560",
        "29452243832",
        "29460393525",
        "stderr was not retained",
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
        text = path.read_text(encoding="utf-8")
        for snippet in snippets:
            if snippet not in text:
                failures.append(f"{path.relative_to(ROOT)} missing current paper text: {snippet}")
    for path, snippets in FORBIDDEN_TEXT.items():
        text = path.read_text(encoding="utf-8")
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
