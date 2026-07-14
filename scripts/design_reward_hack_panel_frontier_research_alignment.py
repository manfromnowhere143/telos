#!/usr/bin/env python3
"""Publish iter184 source-linked research alignment from public sources only."""

from __future__ import annotations

from datetime import UTC, datetime
import hashlib
import json
from pathlib import Path
import re
import sys
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from telos.proof import receipt_digest


ROOT = Path(__file__).resolve().parents[1]
EXPERIMENT_ID = "iter184_reward_hack_panel_frontier_research_alignment_design"
NEXT_EXPERIMENT_ID = "iter185_reward_hack_panel_miss_property_probe_design"
EXPERIMENT = ROOT / "experiments" / EXPERIMENT_ID
PROOF = EXPERIMENT / "proof"
VALID = PROOF / "valid"
RESULT = EXPERIMENT / "RESULT.md"
HYPOTHESIS = EXPERIMENT / "HYPOTHESIS.md"
NEXT_HYPOTHESIS = ROOT / "experiments" / NEXT_EXPERIMENT_ID / "HYPOTHESIS.md"

ITER179_METRICS = (
    ROOT
    / "experiments"
    / "iter179_reward_hack_panel_full_cohort_adjudication"
    / "proof"
    / "full_cohort_panel_metrics.json"
)
ITER179_ROW_AUDIT = (
    ROOT
    / "experiments"
    / "iter179_reward_hack_panel_full_cohort_adjudication"
    / "proof"
    / "row_level_disagreement_and_nondecision_audit.json"
)
ITER183_RESULT = (
    ROOT / "experiments" / "iter183_reward_hack_panel_public_claim_surface_sync" / "RESULT.md"
)
BENCHMARK_MANIFEST = ROOT / "benchmarks" / "reward_hack_benchmark_v1" / "manifest.json"
LITERATURE_DOC = ROOT / "docs" / "LITERATURE_ALIGNMENT_2026.md"

PUBLIC_SURFACES = [
    ROOT / "README.md",
    ROOT / "docs" / "REPORT.md",
    ROOT / "docs" / "MISSION_LOOP.md",
    ROOT / "CONTINUITY.md",
    ROOT / "HANDOFF.md",
    ROOT / "mission" / "loop.json",
    LITERATURE_DOC,
]

SOURCE_MATRIX = PROOF / "source_linked_frontier_alignment_matrix.json"
TECHNIQUE_MAP = PROOF / "telos_gap_to_technique_map.json"
NEXT_GATE_DECISION = PROOF / "next_empirical_gate_recommendation.json"
CLAIM_BOUNDARY = PROOF / "claim_boundary_audit.json"
FORBIDDEN_SCAN = PROOF / "forbidden_claim_scan.json"
SECRET_AUDIT = PROOF / "secret_safety_audit.json"
ENDPOINT_RESULTS = PROOF / "endpoint_results.json"
AUDIT_REPORT = PROOF / "audit_report.json"
RUN_SUMMARY = PROOF / "run_summary.json"
LEARNING = PROOF / "learning_record.json"
RECEIPT = VALID / "receipt_reward_hack_panel_frontier_research_alignment_design.json"

NEXT_GATE = f"experiments/{NEXT_EXPERIMENT_ID}/HYPOTHESIS.md"
PROVIDER_CALLS = 0
CREDENTIAL_PROBES = 0
MODEL_EVALUATIONS = 0
NEW_SWEBENCH_EXECUTIONS = 0
NEW_CLOUD_RESOURCES = 0

FORBIDDEN_POSITIVE_PATTERNS = [
    (
        "leaderboard_positive_claim",
        re.compile(
            r"\b(?:leaderboard|ranking)\b.{0,80}\b"
            r"(?:supported|proven|achieved|claimed|established)\b",
            re.IGNORECASE | re.DOTALL,
        ),
    ),
    (
        "public_benchmark_score_positive_claim",
        re.compile(
            r"\bpublic benchmark score\b.{0,80}\b"
            r"(?:supported|proven|achieved|claimed|established)\b",
            re.IGNORECASE | re.DOTALL,
        ),
    ),
    (
        "model_superiority_positive_claim",
        re.compile(
            r"\bmodel[- ]superiority\b.{0,80}\b"
            r"(?:supported|proven|achieved|claimed|established)\b",
            re.IGNORECASE | re.DOTALL,
        ),
    ),
    (
        "sota_positive_claim",
        re.compile(
            r"\b(?:SOTA|state-of-the-art)\b.{0,80}\b"
            r"(?:supported|proven|achieved|claimed|established)\b",
            re.IGNORECASE | re.DOTALL,
        ),
    ),
    (
        "natural_frequency_positive_claim",
        re.compile(
            r"\bnatural[- ]frequency\b.{0,80}\b"
            r"(?:supported|proven|achieved|claimed|established)\b",
            re.IGNORECASE | re.DOTALL,
        ),
    ),
    (
        "broad_robustness_positive_claim",
        re.compile(
            r"\bbroad robustness\b.{0,80}\b"
            r"(?:supported|proven|achieved|claimed|established)\b",
            re.IGNORECASE | re.DOTALL,
        ),
    ),
    (
        "repaired_score_positive_claim",
        re.compile(
            r"\brepaired[- ]score\b.{0,80}\b"
            r"(?:supported|proven|achieved|claimed|established|made)\b",
            re.IGNORECASE | re.DOTALL,
        ),
    ),
]

SECRET_PATTERNS = [
    ("google_oauth_token", re.compile(r"ya29\.[A-Za-z0-9._-]+")),
    ("bearer_token", re.compile(r"Bearer\s+(?!\[REDACTED_BEARER_TOKEN\])[A-Za-z0-9._~+/=-]+")),
    ("openai_api_key", re.compile(r"\bsk-[A-Za-z0-9][A-Za-z0-9_-]{18,}\b")),
    ("anthropic_api_key", re.compile(r"\bsk-ant-[A-Za-z0-9._-]{18,}\b")),
    ("gcp_project_path", re.compile(r"projects/[A-Za-z][A-Za-z0-9-]{3,}")),
    ("gcp_project_url", re.compile(r"/projects/[A-Za-z][A-Za-z0-9-]{3,}/")),
    (
        "service_account_email",
        re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.gserviceaccount\.com"),
    ),
]


def now_utc() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def pretty_json(payload: Any) -> str:
    return json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(pretty_json(payload), encoding="utf-8")


def read_json(path: Path) -> dict[str, Any]:
    loaded = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(loaded, dict):
        raise SystemExit(f"expected JSON object: {rel(path)}")
    return loaded


def sources() -> list[dict[str, Any]]:
    return [
        {
            "institution": "OpenAI",
            "source_id": "openai_third_party_evals_2026",
            "source_type": "frontier evaluation practice",
            "stable_url": "https://openai.com/index/trustworthy-third-party-evaluations-foundations/",
            "telos_implication": (
                "Report the tested claim, harness, budget, artifacts, and validity checks as part "
                "of the result; keep reward-hacking adjustments visible."
            ),
            "title": "A shared playbook for trustworthy third party evaluations",
            "used_for": ["claim_boundary", "harness_validity", "reward_hacking_validity_check"],
        },
        {
            "institution": "OpenAI",
            "source_id": "openai_eval_best_practices",
            "source_type": "evaluation engineering guidance",
            "stable_url": "https://developers.openai.com/api/docs/guides/evaluation-best-practices",
            "telos_implication": (
                "Treat LLM judges as scalable graders that need clear rubrics, controls, and "
                "validation before scale."
            ),
            "title": "Evaluation best practices",
            "used_for": ["judge_validation", "rubric_design", "human_oracle_boundary"],
        },
        {
            "institution": "OpenAI",
            "source_id": "openai_agent_evals",
            "source_type": "agent workflow evaluation guidance",
            "stable_url": "https://developers.openai.com/api/docs/guides/agent-evals",
            "telos_implication": (
                "Move from isolated outputs to trace-level, repeatable datasets and structured "
                "graders when debugging agent workflows."
            ),
            "title": "Evaluate agent workflows",
            "used_for": ["trace_grading", "repeatability", "workflow_failure_modes"],
        },
        {
            "institution": "OpenAI",
            "source_id": "openai_swe_bench_verified",
            "source_type": "software-agent benchmark design",
            "stable_url": "https://openai.com/index/introducing-swe-bench-verified/",
            "telos_implication": (
                "Human-reviewed software tasks and careful issue selection remain necessary; "
                "Telos should keep execution-backed source traceability explicit."
            ),
            "title": "Introducing SWE-bench Verified",
            "used_for": ["software_benchmark_validity", "human_review", "source_traceability"],
        },
        {
            "institution": "Anthropic",
            "source_id": "anthropic_reward_hacking_misalignment",
            "source_type": "reward-hacking research",
            "stable_url": "https://www.anthropic.com/research/emergent-misalignment-reward-hacking",
            "telos_implication": (
                "Reward hacking on programming tasks is directly relevant to frontier safety, not "
                "a cosmetic benchmark issue."
            ),
            "title": "From shortcuts to sabotage: natural emergent misalignment from reward hacking",
            "used_for": ["reward_hacking_relevance", "programming_task_risk", "safety_case"],
        },
        {
            "institution": "Anthropic",
            "source_id": "anthropic_teaching_claude_why",
            "source_type": "alignment training research",
            "stable_url": "https://alignment.anthropic.com/2026/teaching-claude-why/",
            "telos_implication": (
                "Distribution-specific fixes can hide failures; Telos should test whether a "
                "technique generalizes beyond the exact panel prompt."
            ),
            "title": "Teaching Claude Why",
            "used_for": ["ood_generalization", "alignment_evaluation", "failure_hiding_risk"],
        },
        {
            "institution": "Google DeepMind",
            "source_id": "google_specification_gaming",
            "source_type": "specification-gaming research overview",
            "stable_url": (
                "https://deepmind.google/blog/specification-gaming-the-flip-side-of-ai-ingenuity/"
            ),
            "telos_implication": (
                "Goodhart/specification failures should be tested by finding the actual shortcut, "
                "not by trusting surface success."
            ),
            "title": "Specification gaming: the flip side of AI ingenuity",
            "used_for": ["specification_gaming", "proxy_failure", "shortcut_detection"],
        },
        {
            "institution": "Google DeepMind",
            "source_id": "google_frontier_safety_framework",
            "source_type": "frontier safety governance",
            "stable_url": "https://deepmind.google/blog/strengthening-our-frontier-safety-framework/",
            "telos_implication": (
                "Evaluation thresholds should be explicit and tied to a decision procedure before "
                "a claim changes."
            ),
            "title": "Strengthening our Frontier Safety Framework",
            "used_for": ["thresholds", "decision_procedures", "safety_framework"],
        },
        {
            "institution": "Google AI",
            "source_id": "google_structured_outputs",
            "source_type": "provider structured-output documentation",
            "stable_url": "https://ai.google.dev/gemini-api/docs/structured-output",
            "telos_implication": (
                "Provider-native structured outputs should be required for future paid judge or "
                "property-generator calls where available."
            ),
            "title": "Structured outputs",
            "used_for": ["structured_outputs", "parser_reliability", "nondecision_reduction"],
        },
        {
            "institution": "NIST CAISI",
            "source_id": "nist_agent_eval_cheating",
            "source_type": "AI evaluation cheating guidance",
            "stable_url": (
                "https://www.nist.gov/caisi/cheating-ai-agent-evaluations/1-background-ai-models-can-cheat-evaluations"
            ),
            "telos_implication": (
                "Agent evaluations need scoring functions and task implementations that resist "
                "gaming or subversion by tool-using models."
            ),
            "title": "AI models can cheat on evaluations?",
            "used_for": ["agent_eval_integrity", "scorer_subversion", "tool_access_risk"],
        },
        {
            "institution": "Stanford CRFM",
            "source_id": "stanford_helm",
            "source_type": "holistic model evaluation framework",
            "stable_url": "https://crfm.stanford.edu/helm/",
            "telos_implication": (
                "Telos should keep multi-metric, transparent evidence rather than collapsing "
                "reward-hack verification into one scalar."
            ),
            "title": "Holistic Evaluation of Language Models",
            "used_for": ["holistic_evaluation", "transparency", "multi_metric_reporting"],
        },
        {
            "institution": "Stanford CRFM",
            "source_id": "stanford_reliable_efficient_evaluation",
            "source_type": "adaptive evaluation research",
            "stable_url": "https://crfm.stanford.edu/2025/06/04/reliable-and-efficient-evaluation.html",
            "telos_implication": (
                "Adaptive selection is acceptable only after the pool and stopping bars are frozen; "
                "future Telos expansion should prioritize high-information panel misses."
            ),
            "title": "Reliable and Efficient Amortized Model-Based Evaluation",
            "used_for": ["adaptive_testing", "efficient_evaluation", "sample_selection"],
        },
        {
            "institution": "Columbia University",
            "source_id": "columbia_agent_benchmarking_2026",
            "source_type": "academic agent benchmark project signal",
            "stable_url": "https://www.cs.columbia.edu/research-fair-spring-2026/",
            "telos_implication": (
                "Fair, repeatable agent benchmarks with tool-strategy analysis are active "
                "academic work; Telos should expose failure modes, not just aggregate counts."
            ),
            "title": "Research Fair Spring 2026 agent benchmark projects",
            "used_for": ["agent_benchmarking", "repeatability", "failure_mode_reporting"],
        },
        {
            "institution": "Harvard Teamcore",
            "source_id": "harvard_reward_shaping_inference_alignment",
            "source_type": "inference-time alignment research",
            "stable_url": (
                "https://teamcore.seas.harvard.edu/files/2026/05/6632_Reward_Shaping_for_Infere.pdf"
            ),
            "telos_implication": (
                "Inference-time reward use needs proxy-risk controls; Telos should not let a "
                "reward model or judge become the trusted final oracle."
            ),
            "title": "Reward Shaping for (Inference-Time) Alignment",
            "used_for": ["proxy_reward_risk", "inference_time_alignment", "oracle_boundary"],
        },
        {
            "institution": "MIT FutureTech",
            "source_id": "mit_ai_risk_initiative",
            "source_type": "AI risk taxonomy infrastructure",
            "stable_url": "https://airisk.mit.edu/",
            "telos_implication": (
                "Risk evidence should be taxonomy-linked and useful for auditors; Telos should "
                "produce mapped failure modes and mitigations."
            ),
            "title": "MIT AI Risk Initiative",
            "used_for": ["risk_taxonomy", "auditability", "mitigation_mapping"],
        },
        {
            "institution": "arXiv",
            "source_id": "arxiv_reward_hacking_agents",
            "source_type": "agent evaluation integrity paper",
            "stable_url": "https://arxiv.org/abs/2603.11337",
            "telos_implication": (
                "Evaluator tampering and leakage should be measured as first-class outcomes; "
                "Telos should keep prompt/data leakage and artifact hashes in every run."
            ),
            "title": "RewardHackingAgents",
            "used_for": ["evaluator_integrity", "leakage", "workspace_mutability"],
        },
        {
            "institution": "arXiv",
            "source_id": "arxiv_hack_verifiable_environments",
            "source_type": "reward-hacking benchmark paper",
            "stable_url": "https://arxiv.org/abs/2605.20744",
            "telos_implication": (
                "Reward-hack opportunities should be made verifiable by design; Telos should "
                "turn panel misses into execution-verifiable property probes."
            ),
            "title": "Hack-Verifiable Environments",
            "used_for": ["verifiable_reward_hacking", "deterministic_measurement", "property_probe"],
        },
        {
            "institution": "arXiv",
            "source_id": "arxiv_reward_hacking_language_agents",
            "source_type": "language-agent reward-hacking paper",
            "stable_url": "https://arxiv.org/abs/2606.15385",
            "telos_implication": (
                "Proxy-reward failures can appear zero-shot in language agents; Telos should "
                "measure hidden-objective completion, not just observed reward."
            ),
            "title": "Reward Hacking in Language Model Agents",
            "used_for": ["hidden_objectives", "proxy_reward_failure", "agentic_reward_hacking"],
        },
        {
            "institution": "arXiv",
            "source_id": "arxiv_llm_as_judge_survey",
            "source_type": "LLM judge reliability survey",
            "stable_url": "https://arxiv.org/abs/2411.15594",
            "telos_implication": (
                "LLM-as-judge needs reliability strategy and meta-evaluation; Telos should "
                "escalate missed rows to executable evidence rather than only asking more judges."
            ),
            "title": "A Survey on LLM-as-a-Judge",
            "used_for": ["judge_reliability", "meta_evaluation", "bias_controls"],
        },
        {
            "institution": "arXiv",
            "source_id": "arxiv_swe_bench_pro",
            "source_type": "software-agent benchmark paper",
            "stable_url": "https://arxiv.org/abs/2509.16941",
            "telos_implication": (
                "Long-horizon coding-agent evaluation is moving toward harder, contamination-"
                "resistant tasks; Telos should keep public score claims out until packaging matures."
            ),
            "title": "SWE-Bench Pro",
            "used_for": ["long_horizon_software_tasks", "contamination_resistance", "benchmark_scope"],
        },
    ]


def endpoint_results() -> dict[str, Any]:
    return {
        "credential_probes": CREDENTIAL_PROBES,
        "endpoint_calls": [],
        "estimated_provider_spend_usd": "0.00",
        "experiment_id": EXPERIMENT_ID,
        "model_evaluations": MODEL_EVALUATIONS,
        "new_cloud_resources": NEW_CLOUD_RESOURCES,
        "new_swebench_executions": NEW_SWEBENCH_EXECUTIONS,
        "provider_calls": PROVIDER_CALLS,
        "schema_version": "telos.iter184.endpoint_results.v1",
        "status": "pass",
    }


def source_matrix() -> dict[str, Any]:
    rows = sources()
    failures: list[str] = []
    for row in rows:
        if not row["stable_url"].startswith("https://"):
            failures.append(f"{row['source_id']}:missing_stable_https_url")
        if not row["telos_implication"].strip():
            failures.append(f"{row['source_id']}:missing_telos_implication")
    return {
        "experiment_id": EXPERIMENT_ID,
        "failures": failures,
        "minimum_source_bar": 8,
        "schema_version": "telos.iter184.source_linked_frontier_alignment_matrix.v1",
        "source_count": len(rows),
        "sources": rows,
        "status": "pass" if not failures and len(rows) >= 8 else "fail",
    }


def technique_map(row_audit: dict[str, Any], benchmark_manifest: dict[str, Any]) -> dict[str, Any]:
    hack_rows = [row for row in row_audit["rows"] if row["packet_kind"] == "hack"]
    primary_misses = [row for row in hack_rows if not row["panel"]["majority_catch"]]
    miss_classes: dict[str, int] = {}
    for row in primary_misses:
        miss_classes[row["disagreement_class"]] = miss_classes.get(row["disagreement_class"], 0) + 1
    techniques = [
        {
            "current_telos_gap": "23/40 hack rows are not caught by unrepaired iter179 majority_catch.",
            "next_gate_choice": (
                "Extract the full primary-miss cohort and design an execution/property-probe "
                "escalation instead of adding another verdict-only judge."
            ),
            "source_ids": [
                "openai_third_party_evals_2026",
                "arxiv_hack_verifiable_environments",
                "arxiv_llm_as_judge_survey",
            ],
            "technique": "panel-miss property-probe escalation",
        },
        {
            "current_telos_gap": "Panel evidence is a verdict ledger; it does not yet generate new executable checks.",
            "next_gate_choice": (
                "Require every selected miss row to receive a no-gold, no-hidden-test property "
                "probe schema before paid generation is authorized."
            ),
            "source_ids": [
                "openai_agent_evals",
                "nist_agent_eval_cheating",
                "google_specification_gaming",
            ],
            "technique": "trace- and property-level evidence",
        },
        {
            "current_telos_gap": "Provider output-format failures created panel nondecisions.",
            "next_gate_choice": (
                "Keep native structured output or a validated equivalent as a hard preflight for "
                "future paid calls."
            ),
            "source_ids": ["google_structured_outputs", "openai_eval_best_practices"],
            "technique": "provider-native structured outputs",
        },
        {
            "current_telos_gap": "Any next improvement could accidentally optimize for the known v1 row set.",
            "next_gate_choice": (
                "Freeze row selection, leakage scans, and stop conditions before executing any "
                "property generator or evaluator."
            ),
            "source_ids": [
                "arxiv_reward_hacking_agents",
                "openai_swe_bench_verified",
                "arxiv_swe_bench_pro",
            ],
            "technique": "leakage-resistant pre-registration",
        },
        {
            "current_telos_gap": "The panel has strong control behavior, but product value depends on diagnosable failure modes.",
            "next_gate_choice": (
                "Map every primary miss to disagreement class, source repo, and proposed probe "
                "family so the next gate explains where value will be added."
            ),
            "source_ids": [
                "stanford_helm",
                "columbia_agent_benchmarking_2026",
                "mit_ai_risk_initiative",
            ],
            "technique": "failure-mode taxonomy for auditor value",
        },
        {
            "current_telos_gap": "Reward-model or judge scores can become another proxy reward.",
            "next_gate_choice": (
                "Treat model outputs as generators of candidate checks; use execution or "
                "committed deterministic evidence as the adjudicator."
            ),
            "source_ids": [
                "harvard_reward_shaping_inference_alignment",
                "anthropic_reward_hacking_misalignment",
                "arxiv_reward_hacking_language_agents",
            ],
            "technique": "model-as-generator, execution-as-oracle",
        },
    ]
    failures = [
        f"{item['technique']}:missing_source_ids"
        for item in techniques
        if not item["source_ids"]
    ]
    return {
        "benchmark_scope": {
            "repo_count": benchmark_manifest["repo_count"],
            "row_count": benchmark_manifest["manifest_row_count"],
            "survives_all_static_rows": benchmark_manifest["survives_all_static_rows"],
        },
        "experiment_id": EXPERIMENT_ID,
        "failures": failures,
        "minimum_technique_bar": 4,
        "panel_gap": {
            "hack_rows": len(hack_rows),
            "iter179_majority_catch_hack_rows": len(hack_rows) - len(primary_misses),
            "iter179_primary_miss_hack_rows": len(primary_misses),
            "primary_miss_classes": dict(sorted(miss_classes.items())),
        },
        "schema_version": "telos.iter184.telos_gap_to_technique_map.v1",
        "status": "pass" if not failures and len(techniques) >= 4 else "fail",
        "technique_count": len(techniques),
        "techniques": techniques,
    }


def next_gate_decision(techniques: dict[str, Any]) -> dict[str, Any]:
    return {
        "experiment_id": EXPERIMENT_ID,
        "next_gate": NEXT_GATE,
        "numeric_bars": [
            "provider calls are exactly 0",
            "credential probes are exactly 0",
            "recover exactly 23 iter179 primary-missed hack rows from committed row audit",
            "partition the miss cohort into at least 3 disagreement/nondecision classes",
            "select a priority property-probe subset of 12 rows covering at least 6 repositories",
            "define no-gold/no-hidden-test/no-official-expected-output leakage rules",
            "freeze a future execution/property-probe budget before any provider call",
        ],
        "primary_reason": (
            "The public sources converge on harness validity, reward-hack verifiability, "
            "LLM-judge reliability limits, and leakage-resistant task design. The next useful "
            "frontier step is a zero-spend property-probe design over the 23 primary missed hack "
            "rows, not another immediate paid judge run."
        ),
        "schema_version": "telos.iter184.next_empirical_gate_recommendation.v1",
        "source_backed_technique_count": techniques["technique_count"],
        "status": "pass" if NEXT_HYPOTHESIS.exists() else "fail",
    }


def claim_boundary_audit(metrics: dict[str, Any], source_matrix_payload: dict[str, Any]) -> dict[str, Any]:
    primary = metrics["rules"]["majority_catch"]
    return {
        "benchmark_score_claim_supported": False,
        "broad_robustness_claim_supported": False,
        "claim_supported": (
            "Telos has a source-linked frontier research alignment design for the next "
            "reward-hack panel miss property-probe gate."
        ),
        "experiment_id": EXPERIMENT_ID,
        "leaderboard_claim_supported": False,
        "model_comparison_claim_supported": False,
        "model_superiority_claim_supported": False,
        "natural_frequency_claim_supported": False,
        "primary_public_metric": {
            "control_catches": primary["control_counts"]["catch_count"],
            "control_rows": primary["control_counts"]["attempted"],
            "hack_catches": primary["hack_counts"]["catch_count"],
            "hack_rows": primary["hack_counts"]["attempted"],
            "rule_id": "majority_catch",
        },
        "repaired_score_claim_supported": False,
        "schema_version": "telos.iter184.claim_boundary_audit.v1",
        "source_count": source_matrix_payload["source_count"],
        "sota_claim_supported": False,
        "status": "pass",
    }


def local_negation_before_match(text: str, start: int) -> bool:
    prefix = text[max(0, start - 500) : start].lower()
    sentence_prefix = re.split(r"[.!?]", prefix)[-1]
    return bool(
        re.search(
            r"\b(no|not|none|without|cannot|never|does not|do not|did not)\b",
            sentence_prefix,
        )
    )


def forbidden_claim_scan(paths: list[Path]) -> dict[str, Any]:
    hits: list[dict[str, Any]] = []
    for path in sorted({path for path in paths if path.exists() and path.is_file()}):
        text = path.read_text(encoding="utf-8", errors="replace")
        for name, pattern in FORBIDDEN_POSITIVE_PATTERNS:
            for match in pattern.finditer(text):
                if local_negation_before_match(text, match.start()):
                    continue
                hits.append(
                    {
                        "context": " ".join(match.group(0).split())[:180],
                        "path": rel(path),
                        "pattern": name,
                    }
                )
    return {
        "experiment_id": EXPERIMENT_ID,
        "hit_count": len(hits),
        "hits": hits,
        "patterns": [name for name, _pattern in FORBIDDEN_POSITIVE_PATTERNS],
        "schema_version": "telos.iter184.forbidden_claim_scan.v1",
        "status": "pass" if not hits else "fail",
    }


def secret_safety_audit(paths: list[Path]) -> dict[str, Any]:
    hits: list[dict[str, Any]] = []
    scanned = 0
    for path in sorted({path for path in paths if path.exists() and path.is_file()}):
        if path == SECRET_AUDIT:
            continue
        scanned += 1
        text = path.read_text(encoding="utf-8", errors="replace")
        for name, pattern in SECRET_PATTERNS:
            for match in pattern.finditer(text):
                hits.append(
                    {
                        "artifact": rel(path),
                        "match_sha256": sha256_text(match.group(0)),
                        "match_start": match.start(),
                        "pattern": name,
                    }
                )
    return {
        "experiment_id": EXPERIMENT_ID,
        "hits": hits,
        "patterns": [name for name, _pattern in SECRET_PATTERNS],
        "schema_version": "telos.iter184.secret_safety_audit.v1",
        "scanned_artifact_count": scanned,
        "secret_hit_count": len(hits),
        "status": "pass" if not hits else "fail",
    }


def active_gate_ok() -> bool:
    loop = read_json(ROOT / "mission" / "loop.json")
    text_ok = all(NEXT_GATE in path.read_text(encoding="utf-8", errors="replace") for path in [
        ROOT / "README.md",
        ROOT / "CONTINUITY.md",
        ROOT / "HANDOFF.md",
    ])
    return loop.get("active_gate") == NEXT_GATE and text_ok and NEXT_HYPOTHESIS.exists()


def build_failures(
    *,
    endpoint: dict[str, Any],
    matrix: dict[str, Any],
    techniques: dict[str, Any],
    decision: dict[str, Any],
    claim: dict[str, Any],
    forbidden: dict[str, Any],
    secret: dict[str, Any] | None,
) -> list[str]:
    failures: list[str] = []
    if endpoint["provider_calls"] != 0:
        failures.append("provider_calls_not_zero")
    if endpoint["credential_probes"] != 0:
        failures.append("credential_probes_not_zero")
    if matrix["status"] != "pass":
        failures.extend(matrix["failures"])
    if techniques["status"] != "pass":
        failures.extend(techniques["failures"])
    if decision["status"] != "pass":
        failures.append("next_empirical_gate_not_pre_registered")
    if not active_gate_ok():
        failures.append("active_gate_references_not_iter185")
    forbidden_flags = [
        "benchmark_score_claim_supported",
        "broad_robustness_claim_supported",
        "leaderboard_claim_supported",
        "model_comparison_claim_supported",
        "model_superiority_claim_supported",
        "natural_frequency_claim_supported",
        "repaired_score_claim_supported",
        "sota_claim_supported",
    ]
    for flag in forbidden_flags:
        if claim.get(flag) is not False:
            failures.append(f"claim_boundary_not_false:{flag}")
    if forbidden["status"] != "pass":
        failures.append("forbidden_positive_claim_scan_hits")
    if secret is not None and secret["status"] != "pass":
        failures.append("secret_safety_audit_failed")
    return failures


def audit_report(
    *,
    endpoint: dict[str, Any],
    matrix: dict[str, Any],
    techniques: dict[str, Any],
    forbidden: dict[str, Any],
    secret: dict[str, Any],
    failures: list[str],
    status: str,
) -> dict[str, Any]:
    return {
        "bars": {
            "active_gate_references_point_to_next_pre_registered_gate": active_gate_ok(),
            "credential_probes": endpoint["credential_probes"],
            "forbidden_positive_claim_hits": forbidden["hit_count"],
            "minimum_source_bar": matrix["source_count"] >= matrix["minimum_source_bar"],
            "minimum_technique_bar": techniques["technique_count"]
            >= techniques["minimum_technique_bar"],
            "new_cloud_resources": endpoint["new_cloud_resources"],
            "new_swebench_executions": endpoint["new_swebench_executions"],
            "provider_calls": endpoint["provider_calls"],
            "secret_hit_count": secret["secret_hit_count"],
        },
        "experiment_id": EXPERIMENT_ID,
        "failures": failures,
        "schema_version": "telos.iter184.audit_report.v1",
        "status": status,
    }


def result_markdown(
    *,
    matrix: dict[str, Any],
    techniques: dict[str, Any],
    decision: dict[str, Any],
    failures: list[str],
    status: str,
) -> str:
    failure_text = "\n".join(f"- `{failure}`" for failure in failures) or "- none"
    gap = techniques["panel_gap"]
    return f"""# Iteration 184 Result - Reward-Hack Panel Frontier Research Alignment Design

Status: `{status}`.

## What this gate did

This zero-spend gate converted public-source research alignment into a concrete next Telos gate. It made
no provider calls, no credential probes, no model evaluations, no SWE-bench executions, and no cloud
resource changes.

## Source-Backed Decision

- Public sources recorded: `{matrix['source_count']}`.
- Source-backed technique implications: `{techniques['technique_count']}`.
- Iter179 primary missed hack rows to target next: `{gap['iter179_primary_miss_hack_rows']}` of `{gap['hack_rows']}`.
- Recommended next gate: `{decision['next_gate']}`.

The convergent finding is that Telos should not chase a broader public score yet. The next useful frontier
step is a zero-spend property-probe design over the panel-missed hack cohort, preserving the current
primary public metric while preparing an execution-backed escalation path.

Failures / blockers:

{failure_text}

## Claim Boundary

At most, this gate supports a source-linked research-alignment design for the next reward-hack panel
miss property-probe gate. The public panel metric remains unrepaired iter179 `majority_catch`: `17/40`
hack rows and `0/40` controls.

No leaderboard ranking, state-of-the-art claim, natural reward-hacking frequency estimate, broad
reward-model robustness claim, production deployment claim, model-superiority claim, public benchmark
score, repaired-score claim, or claim outside committed iter175-iter184 proof packets is supported.

## Evidence

- `proof/source_linked_frontier_alignment_matrix.json`
- `proof/telos_gap_to_technique_map.json`
- `proof/next_empirical_gate_recommendation.json`
- `proof/claim_boundary_audit.json`
- `proof/forbidden_claim_scan.json`
- `proof/secret_safety_audit.json`
- `proof/endpoint_results.json`
- `proof/audit_report.json`
- `proof/run_summary.json`
- `proof/valid/receipt_reward_hack_panel_frontier_research_alignment_design.json`
"""


def main() -> int:
    PROOF.mkdir(parents=True, exist_ok=True)
    VALID.mkdir(parents=True, exist_ok=True)

    metrics = read_json(ITER179_METRICS)
    row_audit = read_json(ITER179_ROW_AUDIT)
    benchmark_manifest = read_json(BENCHMARK_MANIFEST)
    endpoint = endpoint_results()
    matrix = source_matrix()
    techniques = technique_map(row_audit, benchmark_manifest)
    decision = next_gate_decision(techniques)
    claim = claim_boundary_audit(metrics, matrix)
    generated_paths = [
        SOURCE_MATRIX,
        TECHNIQUE_MAP,
        NEXT_GATE_DECISION,
        CLAIM_BOUNDARY,
        FORBIDDEN_SCAN,
        SECRET_AUDIT,
        ENDPOINT_RESULTS,
        AUDIT_REPORT,
        RUN_SUMMARY,
        LEARNING,
        RECEIPT,
        RESULT,
    ]

    write_json(SOURCE_MATRIX, matrix)
    write_json(TECHNIQUE_MAP, techniques)
    write_json(NEXT_GATE_DECISION, decision)
    write_json(CLAIM_BOUNDARY, claim)
    write_json(ENDPOINT_RESULTS, endpoint)

    preliminary_forbidden = forbidden_claim_scan(
        [HYPOTHESIS, NEXT_HYPOTHESIS, ITER183_RESULT, *PUBLIC_SURFACES, *generated_paths]
    )
    preliminary_failures = build_failures(
        claim=claim,
        decision=decision,
        endpoint=endpoint,
        forbidden=preliminary_forbidden,
        matrix=matrix,
        secret=None,
        techniques=techniques,
    )
    preliminary_status = "pass" if not preliminary_failures else "fail"
    RESULT.write_text(
        result_markdown(
            decision=decision,
            failures=preliminary_failures,
            matrix=matrix,
            status=preliminary_status,
            techniques=techniques,
        ),
        encoding="utf-8",
    )
    forbidden = forbidden_claim_scan(
        [HYPOTHESIS, NEXT_HYPOTHESIS, ITER183_RESULT, *PUBLIC_SURFACES, *generated_paths]
    )
    secret = secret_safety_audit(
        [HYPOTHESIS, NEXT_HYPOTHESIS, ITER183_RESULT, *PUBLIC_SURFACES, *generated_paths]
    )
    failures = build_failures(
        claim=claim,
        decision=decision,
        endpoint=endpoint,
        forbidden=forbidden,
        matrix=matrix,
        secret=secret,
        techniques=techniques,
    )
    status = "pass" if not failures else "fail"
    write_json(FORBIDDEN_SCAN, forbidden)
    write_json(SECRET_AUDIT, secret)
    write_json(
        AUDIT_REPORT,
        audit_report(
            endpoint=endpoint,
            failures=failures,
            forbidden=forbidden,
            matrix=matrix,
            secret=secret,
            status=status,
            techniques=techniques,
        ),
    )
    run_summary = {
        "credential_probes": CREDENTIAL_PROBES,
        "experiment_id": EXPERIMENT_ID,
        "failures": failures,
        "generated_at_utc": now_utc(),
        "new_cloud_resources": NEW_CLOUD_RESOURCES,
        "new_swebench_executions": NEW_SWEBENCH_EXECUTIONS,
        "provider_calls": PROVIDER_CALLS,
        "recommended_next_gate": NEXT_GATE,
        "schema_version": "telos.iter184.run_summary.v1",
        "secret_hit_count": secret["secret_hit_count"],
        "source_count": matrix["source_count"],
        "status": status,
        "technique_count": techniques["technique_count"],
    }
    learning = {
        "evidence_paths": [
            rel(SOURCE_MATRIX),
            rel(TECHNIQUE_MAP),
            rel(NEXT_GATE_DECISION),
            rel(CLAIM_BOUNDARY),
            rel(FORBIDDEN_SCAN),
            rel(SECRET_AUDIT),
            rel(RECEIPT),
        ],
        "experiment_id": EXPERIMENT_ID,
        "insight": (
            "current public sources support a zero-spend property-probe design over the 23 "
            "iter179 primary missed hack rows before any new paid evaluator expansion"
        )
        if status == "pass"
        else "the frontier research-alignment design did not satisfy its source or claim bars",
        "next_action": f"run {NEXT_EXPERIMENT_ID} as a zero-spend panel-miss property-probe design",
        "result_path": rel(RESULT),
        "schema_version": "telos.learning_record.v1",
        "status": status if status == "pass" else "null",
    }
    write_json(RUN_SUMMARY, run_summary)
    write_json(LEARNING, learning)
    RESULT.write_text(
        result_markdown(
            decision=decision,
            failures=failures,
            matrix=matrix,
            status=status,
            techniques=techniques,
        ),
        encoding="utf-8",
    )

    receipt = {
        "acceptance_criteria": [
            "No provider calls, credential probes, model evaluations, SWE-bench executions, or cloud resources are used.",
            "At least 8 relevant public sources are recorded with stable URLs and Telos implications.",
            "At least 4 source-backed technique implications are mapped to concrete Telos next-gate choices.",
            "The next empirical gate is pre-registered with numeric bars before any provider spend.",
            "The public panel metric remains unrepaired iter179 majority_catch: 17/40 hacks and 0/40 controls.",
            "No forbidden leaderboard, model-superiority, SOTA, natural-frequency, broad robustness, public benchmark-score, or repaired-score claim is made.",
            "No audited artifact contains secrets or private project/account identifiers.",
        ],
        "agent_id": "codex-zero-spend-frontier-research-aligner",
        "benchmark_id": "reward_hack_benchmark_v1",
        "evidence": [
            {"artifact": rel(SOURCE_MATRIX), "kind": "artifact", "status": status},
            {"artifact": rel(TECHNIQUE_MAP), "kind": "artifact", "status": status},
            {"artifact": rel(NEXT_GATE_DECISION), "kind": "artifact", "status": status},
            {"artifact": rel(CLAIM_BOUNDARY), "kind": "adversarial_review", "status": status},
            {"artifact": rel(SECRET_AUDIT), "kind": "adversarial_review", "status": status},
        ],
        "falsifiers": [
            "The gate fails if any provider call, credential probe, model evaluation, SWE-bench execution, or cloud resource change occurs.",
            "The gate fails if fewer than 8 stable public sources are recorded.",
            "The gate fails if fewer than 4 source-backed implications map to concrete Telos next-gate choices.",
            "The gate fails if the next empirical gate is not pre-registered before spend.",
            "The gate fails if a forbidden public benchmark, leaderboard, model-superiority, SOTA, natural-frequency, broad robustness, or repaired-score claim is found.",
            "The gate fails if an audited artifact contains secrets or private project/account identifiers.",
        ],
        "receipt_id": f"iter184-reward-hack-panel-frontier-research-alignment-design-{status}",
        "stated_goal": (
            "Map current public research to the next Telos reward-hack panel empirical gate "
            "without spending or inflating claims."
        ),
        "status": status,
        "task_id": f"telos:{EXPERIMENT_ID}",
    }
    receipt["sha256"] = receipt_digest(receipt)
    write_json(RECEIPT, receipt)

    print(
        json.dumps(
            {
                "credential_probes": CREDENTIAL_PROBES,
                "experiment_id": EXPERIMENT_ID,
                "provider_calls": PROVIDER_CALLS,
                "secret_hit_count": secret["secret_hit_count"],
                "source_count": matrix["source_count"],
                "status": status,
                "technique_count": techniques["technique_count"],
            },
            sort_keys=True,
        )
    )
    return 0 if status == "pass" else 1


if __name__ == "__main__":
    sys.exit(main())
