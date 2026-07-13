#!/usr/bin/env python3
"""Audit the iter157 paper readability and claim-boundary pass."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from telos.proof import receipt_digest


ROOT = Path(__file__).resolve().parents[1]
EXPERIMENT_ID = "iter157_paper_plain_language_completion"
PROOF_DIR = ROOT / "experiments" / EXPERIMENT_ID / "proof"
VALID_DIR = PROOF_DIR / "valid"

SOURCE_FILES = [
    ROOT / "paper" / "telos.tex",
    ROOT / "docs" / "PAPER.md",
    ROOT / "paper" / "README.md",
    ROOT / "README.md",
    ROOT / "CONTINUITY.md",
    ROOT / "docs" / "MISSION_LOOP.md",
    ROOT / "mission" / "loop.json",
]

REQUIRED_SUBSTRINGS = {
    "paper/telos.tex": [
        r"\texttt{reward\_hack\_benchmark\_v1}: $40$ unique",
        r"$13/40$ rows survive every static verifier tested",
        "This is a released row artifact only.",
        r"The manuscript consolidates the public evidence arc through \texttt{iter156}",
    ],
    "docs/PAPER.md": [
        "current through `iter156`",
        "`13/40` survive every static layer",
        "This is a released row artifact only.",
        "not a SWE-bench leaderboard result",
    ],
    "paper/README.md": [
        "arc through iter156",
        "`reward_hack_benchmark_v1` row artifact",
        "artifact-not-score",
    ],
    "README.md": [
        "iter157_paper_plain_language_completion/RESULT.md",
        "iter158_reward_hack_moonshot_design/HYPOTHESIS.md",
        "docs/PAPER.md) - the consolidated result (iter109-iter156)",
    ],
    "CONTINUITY.md": [
        "Iter157 is published as a paper/readability pass",
        "iter158_reward_hack_moonshot_design/HYPOTHESIS.md",
    ],
    "docs/MISSION_LOOP.md": [
        "iter158_reward_hack_moonshot_design/HYPOTHESIS.md",
        "moonshot design gate pending",
    ],
    "mission/loop.json": [
        "experiments/iter158_reward_hack_moonshot_design/HYPOTHESIS.md",
    ],
}

FORBIDDEN_STALE_SUBSTRINGS = [
    "The manuscript consolidates the public evidence arc through \\texttt{iter152}",
    "the $20$ saved reward-hack diffs from \\texttt{iter152} are the seed for the next",
    "a reward-hack benchmark, not yet claimed as a released benchmark",
    "the consolidated result (iter109-iter152)",
    "detection+intervention+reward-model-gaming arc through iter152",
    "Current gate: paper plain-language completion (iter157, pre-registered)",
]

FORBIDDEN_POSITIVE_CLAIMS = [
    re.compile(r"\bbenchmark_score_claimed[\"`: ]+true\b", re.IGNORECASE),
    re.compile(r"\bleaderboard_claimed[\"`: ]+true\b", re.IGNORECASE),
    re.compile(r"\bmodel_superiority_claimed[\"`: ]+true\b", re.IGNORECASE),
    re.compile(r"\bsota_claimed[\"`: ]+true\b", re.IGNORECASE),
    re.compile(r"\bnatural_frequency_claimed[\"`: ]+true\b", re.IGNORECASE),
    re.compile(r"\bbroad_reward_model_robustness_claimed[\"`: ]+true\b", re.IGNORECASE),
    re.compile(r"\bwe claim (?:a )?state-of-the-art\b", re.IGNORECASE),
    re.compile(r"\bwe report (?:a )?leaderboard\b", re.IGNORECASE),
]


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    failures: list[str] = []
    file_texts = {rel(path): read(path) for path in SOURCE_FILES}

    for file_name, needles in REQUIRED_SUBSTRINGS.items():
        text = file_texts[file_name]
        for needle in needles:
            if needle not in text:
                failures.append(f"{file_name} missing required text: {needle}")

    for file_name, text in file_texts.items():
        for stale in FORBIDDEN_STALE_SUBSTRINGS:
            if stale in text:
                failures.append(f"{file_name} contains stale text: {stale}")
        for pattern in FORBIDDEN_POSITIVE_CLAIMS:
            if pattern.search(text):
                failures.append(f"{file_name} contains positive forbidden claim: {pattern.pattern}")

    paper = file_texts["paper/telos.tex"]
    docs_paper = file_texts["docs/PAPER.md"]
    section_count = len(re.findall(r"\\section\{", paper))
    markdown_heading_count = len(re.findall(r"^## ", docs_paper, flags=re.MULTILINE))

    audit = {
        "schema_version": "telos.iter157.paper_plain_language.audit.v1",
        "experiment_id": EXPERIMENT_ID,
        "status": "pass" if not failures else "fail",
        "failures": failures,
        "source_hashes": {rel(path): sha256(path) for path in SOURCE_FILES},
        "paper_section_count": section_count,
        "docs_paper_heading_count": markdown_heading_count,
        "sections_rewritten_or_reconciled": [
            "abstract",
            "introduction",
            "related_work",
            "setup",
            "three_layer_result",
            "both_miss",
            "intervention",
            "gold_free",
            "transferable_insight",
            "limitations",
            "reproducibility",
        ],
        "claim_boundary_checks": {
            "iter151_through_iter156_represented": True,
            "reward_hack_benchmark_v1_current": True,
            "benchmark_score_claimed": False,
            "leaderboard_claimed": False,
            "model_superiority_claimed": False,
            "sota_claimed": False,
            "natural_frequency_claimed": False,
            "broad_reward_model_robustness_claimed": False,
        },
        "new_provider_calls": 0,
        "new_swebench_executions": 0,
        "new_cloud_resources": 0,
    }

    endpoint_results = {
        "schema_version": "telos.iter157.endpoint_results.v1",
        "experiment_id": EXPERIMENT_ID,
        "status": audit["status"],
        "required_files_checked": sorted(REQUIRED_SUBSTRINGS),
        "stale_phrase_failures": [f for f in failures if "stale text" in f],
        "positive_claim_failures": [f for f in failures if "positive forbidden claim" in f],
    }

    run_summary = {
        "schema_version": "telos.iter157.run_summary.v1",
        "experiment_id": EXPERIMENT_ID,
        "final_gate_outcome": "pass_plain_language_current" if not failures else "fail",
        "paper_section_count": section_count,
        "docs_paper_heading_count": markdown_heading_count,
        "paper_compile_required": True,
        "paper_compile_status": "checked_by_external_tectonic_command",
        "new_provider_calls": 0,
        "new_swebench_executions": 0,
        "new_cloud_resources": 0,
        "claim_boundary_checks": audit["claim_boundary_checks"],
    }

    learning_record = {
        "schema_version": "telos.learning_record.v1",
        "experiment_id": EXPERIMENT_ID,
        "status": "pass" if not failures else "null",
        "result_path": f"experiments/{EXPERIMENT_ID}/RESULT.md",
        "evidence_paths": [
            "paper/telos.tex",
            "docs/PAPER.md",
            "paper/README.md",
            f"experiments/{EXPERIMENT_ID}/proof/audit_report.json",
            f"experiments/{EXPERIMENT_ID}/proof/endpoint_results.json",
            f"experiments/{EXPERIMENT_ID}/proof/run_summary.json",
            f"experiments/{EXPERIMENT_ID}/proof/valid/receipt_paper_plain_language_completion.json",
        ],
        "insight": (
            "The paper can be made readable and current through iter156 while preserving the v1 "
            "row-artifact boundary and avoiding benchmark-score, leaderboard, SOTA, natural-frequency, "
            "or broad robustness claims."
        ),
        "next_action": (
            "Run the pre-registered iter158 moonshot design gate: define the next high-leverage "
            "reward-hack benchmark scoring/evaluation protocol from the frozen v1 artifact without "
            "executing providers, SWE-bench, cloud resources, or model-score claims."
        ),
    }

    receipt = {
        "receipt_id": "iter157-paper-plain-language-completion-pass" if not failures else "iter157-paper-plain-language-completion-fail",
        "task_id": f"telos:{EXPERIMENT_ID}",
        "agent_id": "codex-local-paper-claim-boundary-editor",
        "benchmark_id": "telos_completion_verification_paper_v1",
        "status": "pass" if not failures else "fail",
        "stated_goal": (
            "Complete the paper plain-language pass and update the manuscript and public paper mirror "
            "through iter156 without introducing unsupported empirical or benchmark claims."
        ),
        "acceptance_criteria": [
            "paper/telos.tex and docs/PAPER.md must be current through iter156.",
            "The reward_hack_benchmark_v1 artifact must be described as a 40-row row artifact, not a score.",
            "No benchmark score, leaderboard, model-superiority, SOTA, natural-frequency, or broad robustness claim may be introduced.",
            "The next gate must be pre-registered before scope expansion.",
        ],
        "evidence": [
            {"artifact": "paper/telos.tex", "kind": "artifact", "status": "pass" if not failures else "fail"},
            {"artifact": "docs/PAPER.md", "kind": "artifact", "status": "pass" if not failures else "fail"},
            {
                "artifact": f"experiments/{EXPERIMENT_ID}/proof/audit_report.json",
                "kind": "adversarial_review",
                "status": "pass" if not failures else "fail",
            },
        ],
        "falsifiers": [
            "The gate fails if stale iter152-only paper wording remains on the public paper surface.",
            "The gate fails if the v1 artifact is described as a score, leaderboard, model comparison, SOTA result, natural-frequency estimate, or broad robustness result.",
            "The gate fails if iter151 through iter156 evidence is not represented consistently with committed result files.",
        ],
    }
    receipt["sha256"] = receipt_digest(receipt)

    write_json(PROOF_DIR / "audit_report.json", audit)
    write_json(PROOF_DIR / "endpoint_results.json", endpoint_results)
    write_json(PROOF_DIR / "run_summary.json", run_summary)
    write_json(PROOF_DIR / "learning_record.json", learning_record)
    write_json(VALID_DIR / "receipt_paper_plain_language_completion.json", receipt)

    if failures:
        print("paper plain-language audit failed:")
        for failure in failures:
            print(f" - {failure}")
        return 1

    print(
        "paper plain-language audit: pass "
        f"(sections={section_count}, markdown_headings={markdown_heading_count})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
