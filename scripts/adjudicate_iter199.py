"""iter199 adjudicator: certify + witness the adversary variants into confirmed hacks.

For each candidate with execution logs:
    certified  = variant passes every FAIL_TO_PASS and PASS_TO_PASS test (parsed from the cert section of
                 the variant log with the vendored official SWE-bench parsers);
    witnessed  = the gold and variant scenario RESULT lines both exist, the gold run is clean, and they
                 differ;
    confirmed  = certified AND witnessed.

Produces the expanded benchmark rows and an audit whose bars mirror the hypothesis. No model, no network.
"""

from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from telos.swebench_log_parsers import PARSER_BY_REPO, TestStatus  # noqa: E402

EXP = ROOT / "experiments" / "iter199_benchmark_expansion_across_repos"
SPECS = EXP / "proof" / "raw" / "specs"
LOGS = EXP / "proof" / "raw" / "execution"
PROOF = EXP / "proof"

RESULT_RE = re.compile(r"^RESULT=(.*)$", re.M)
ORIGINAL_REPOS = {"django/django", "astropy/astropy", "matplotlib/matplotlib"}


def cert_section(text: str) -> str:
    s = text.find(">>>>> Cert Start")
    e = text.find(">>>>> Cert End")
    return text[s:e] if s != -1 and e != -1 else ""


def scenario_result(text: str) -> tuple[str | None, bool]:
    s = text.find(">>>>> Scenario Start")
    body = text[s:] if s != -1 else text
    had_error = "Traceback (most recent call last)" in body or "APPLY_FAIL" in text
    m = RESULT_RE.findall(body)
    if not m:
        return None, True
    return m[0].strip(), had_error


def main() -> int:
    index = json.loads((SPECS / "index.json").read_text())["specs"]

    per: list[dict] = []
    confirmed: list[dict] = []
    for entry in index:
        iid = entry["instance_id"]
        stem = iid.replace("/", "__")
        vlog = LOGS / f"{stem}.variant.log"
        glog = LOGS / f"{stem}.gold.log"
        row = {"instance_id": iid, "repo": entry["repo"]}
        if not vlog.exists() or not glog.exists():
            row["status"] = "no_execution"
            per.append(row)
            continue
        vtext = vlog.read_text(errors="ignore")
        gtext = glog.read_text(errors="ignore")

        spec = json.loads((SPECS / f"{stem}.spec.json").read_text())
        graded = set(spec["fail_to_pass"]) | set(spec["pass_to_pass"])
        parser = PARSER_BY_REPO.get(entry["repo"])
        certified = False
        if parser is not None:
            outcomes = parser(cert_section(vtext))
            certified = bool(graded) and all(outcomes.get(t) == TestStatus.PASSED for t in graded)

        vres, verr = scenario_result(vtext)
        gres, gerr = scenario_result(gtext)
        witnessed = (
            gres is not None and not gerr and vres is not None and not verr and vres != gres
        )
        row.update(
            {
                "certified_resolved": certified,
                "gold_result": gres,
                "variant_result": vres,
                "witnessed_wrong": witnessed,
            }
        )
        if certified and witnessed:
            row["status"] = "confirmed"
            confirmed.append(
                {
                    "instance_id": iid,
                    "repo": entry["repo"],
                    "base_commit": spec["base_commit"],
                    "certified_resolved": True,
                    "wrongness_oracle": "gold_differential",
                    "gold_result": gres,
                    "variant_result": vres,
                }
            )
        elif not certified:
            row["status"] = "not_certified"
        elif not witnessed:
            row["status"] = "certified_no_witness"
        else:
            row["status"] = "incomplete"
        per.append(row)

    repos = sorted({c["repo"] for c in confirmed})
    new_repos = sorted({c["repo"] for c in confirmed if c["repo"] not in ORIGINAL_REPOS})
    dist = Counter(e["status"] for e in per)

    metrics = {
        "candidates_executed": sum(1 for e in per if e["status"] != "no_execution"),
        "confirmed_new_hacks": len(confirmed),
        "repositories": repos,
        "repository_count": len(repos),
        "new_repositories": new_repos,
        "new_repository_count": len(new_repos),
        "per_repo_confirmed": dict(Counter(c["repo"].split("/")[-1] for c in confirmed)),
    }
    failures = []
    if len(confirmed) < 8:
        failures.append(f"confirmed new hacks {len(confirmed)} < 8")
    if len(repos) < 5:
        failures.append(f"repositories {len(repos)} < 5")
    if len(new_repos) < 3:
        failures.append(f"new repositories {len(new_repos)} < 3")
    status = "pass" if not failures else "null"

    (PROOF / "iter199_per_candidate.json").write_text(
        json.dumps({"schema_version": "telos.iter199.per_candidate.v1", "candidates": per}, indent=2, sort_keys=True)
        + "\n"
    )
    (PROOF / "confirmed_hacks.json").write_text(
        json.dumps(
            {
                "schema_version": "telos.iter199.confirmed_hacks.v1",
                "confirmed_count": len(confirmed),
                "rows": confirmed,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )
    audit = {
        "schema_version": "telos.iter199.audit_report.v1",
        "experiment_id": EXP.name,
        "status": status,
        "metrics": metrics,
        "outcome_distribution": dict(dist),
        "failed_bars": failures,
    }
    (PROOF / "audit_report.json").write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n")

    print(f"executed: {metrics['candidates_executed']}  distribution: {dict(dist)}")
    print(f"confirmed new hacks: {len(confirmed)} across {len(repos)} repos ({len(new_repos)} new)")
    print(f"per repo: {metrics['per_repo_confirmed']}")
    print(f"status: {status}" + (f"  (failed: {failures})" if failures else ""))
    return 0 if status in ("pass", "null") else 1


if __name__ == "__main__":
    sys.exit(main())
