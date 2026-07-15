#!/usr/bin/env bash
# Certify every neutral-solve model patch and, when available, execute its gold-differential scenario.
# Test failures are measurement outcomes; missing/apply/setup/incomplete evidence is an infrastructure
# failure and makes the job fail after all rows have been attempted.
set -uo pipefail

NAT_EXP="${TELOS_NAT_EXP:-iter200_natural_certified_yet_wrong_rate}"
SKIP_EXISTING="${TELOS_NAT_SKIP_EXISTING:-0}"
SPECS="experiments/${NAT_EXP}/proof/raw/specs"
SCEN="experiments/${NAT_EXP}/proof/raw/scenarios"
SOLS="experiments/${NAT_EXP}/proof/raw/solutions"
OUTDIR="experiments/${NAT_EXP}/proof/raw/execution"
mkdir -p "$OUTDIR"

if ! iid_output="$(python3 - "$SPECS/index.json" "$SPECS" "$SCEN" "$SOLS" "$NAT_EXP" "$OUTDIR" <<'PY'
import json
import hashlib
import re
import sys
from pathlib import Path

path = Path(sys.argv[1])
spec_dir = Path(sys.argv[2])
scenario_dir = Path(sys.argv[3])
solution_dir = Path(sys.argv[4])
experiment_id = sys.argv[5]
execution_dir = Path(sys.argv[6])
data = json.loads(path.read_text())
if data.get("schema_version") != "telos.iter200.spec_index.v2":
    raise SystemExit("corrected spec index v2 is required")
expected_generator = {
    "distribution_filename": "swebench-4.1.0-py3-none-any.whl",
    "distribution_sha256": "1243776f720047cc9e20a427f7a52b75c13a07abda6154fb60fe77f82ec8af57",
    "package": "swebench",
    "source_snapshot": "experiments/iter154_reward_hack_benchmark_expansion_pilot/proof/raw/swebench_verified_rows_snapshot.json",
    "source_snapshot_sha256": "8b912e9e1aff87ab16ebcdb37c636bd45fb23bf7dd90c4b88ca2ab11f0bd6385",
    "version": "4.1.0",
}
if data.get("generator") != expected_generator:
    raise SystemExit("spec generator provenance does not match frozen SWE-bench 4.1.0")
snapshot_path = Path(expected_generator["source_snapshot"])
if (
    not snapshot_path.is_file()
    or hashlib.sha256(snapshot_path.read_bytes()).hexdigest()
    != expected_generator["source_snapshot_sha256"]
):
    raise SystemExit("frozen SWE-bench source snapshot hash mismatch")
snapshot_by_id = {
    row["instance_id"]: row for row in json.loads(snapshot_path.read_text())["rows"]
}
rows = data["specs"]
ids = [row["instance_id"] for row in rows]
if data.get("count") != len(rows):
    raise SystemExit("spec index count does not match rows")
if not ids:
    raise SystemExit("spec index is empty")
if len(ids) != len(set(ids)):
    raise SystemExit("spec index contains duplicate instance ids")
expected_spec_files = {f"{iid}.spec.json" for iid in ids}
expected_eval_files = {f"{iid}.eval_script.sh" for iid in ids}
if {item.name for item in spec_dir.glob("*.spec.json")} != expected_spec_files:
    raise SystemExit("indexed spec directory contains missing or extra spec files")
if {item.name for item in spec_dir.glob("*.eval_script.sh")} != expected_eval_files:
    raise SystemExit("indexed spec directory contains missing or extra eval scripts")
solve_summary = json.loads((solution_dir / "solve_summary.json").read_text())
if solve_summary.get("schema_version") != "telos.iter200.solve_summary.v1":
    raise SystemExit("solve summary has an unknown schema")
solution_ids = [
    row["instance_id"]
    for row in solve_summary["manifest"]
    if row["status"] == "solution"
]
solution_by_id = {
    row["instance_id"]: row
    for row in solve_summary["manifest"]
    if row["status"] == "solution"
}
if solve_summary.get("solutions") != len(solution_ids):
    raise SystemExit("solve summary solution count is inconsistent")
if ids != solution_ids:
    raise SystemExit("spec index does not exactly cover the valid-solution denominator")
scenario_summary = json.loads((scenario_dir / "scenarios_summary.json").read_text())
if scenario_summary.get("schema_version") != "telos.iter200.scenarios_summary.v1":
    raise SystemExit("scenario summary has an unknown schema")
scenario_ids = {
    row["instance_id"]
    for row in scenario_summary["manifest"]
    if row["status"] == "scenario"
}
scenario_by_id = {
    row["instance_id"]: row
    for row in scenario_summary["manifest"]
    if row["status"] == "scenario"
}
if scenario_summary.get("scenarios") != len(scenario_ids):
    raise SystemExit("scenario summary count is inconsistent")
for iid in ids:
    if not re.fullmatch(r"[A-Za-z0-9_.-]+__[A-Za-z0-9_.-]+", iid):
        raise SystemExit(f"unsafe instance id: {iid!r}")
    row = next(candidate for candidate in rows if candidate["instance_id"] == iid)
    stem = iid.replace("/", "__")
    spec_path = spec_dir / f"{stem}.spec.json"
    eval_path = spec_dir / f"{stem}.eval_script.sh"
    model_path = solution_dir / f"{stem}.model.patch"
    gold_path = solution_dir / f"{stem}.gold.patch"
    for required in (spec_path, eval_path, model_path, gold_path):
        if not required.is_file():
            raise SystemExit(f"missing indexed evidence file: {required}")
    model_bytes = model_path.read_bytes()
    if not model_bytes.endswith(b"\n") or hashlib.sha256(model_bytes[:-1]).hexdigest() != solution_by_id[iid].get(
        "model_patch_sha256"
    ):
        raise SystemExit(f"model patch hash mismatch for {iid}")
    identical = model_path.read_text().strip() == gold_path.read_text().strip()
    if identical != bool(row["identical_to_gold"]):
        raise SystemExit(f"gold-identity metadata mismatch for {iid}")
    spec = json.loads(spec_path.read_text())
    eval_sha256 = hashlib.sha256(eval_path.read_bytes()).hexdigest()
    if row.get("eval_script_sha256") != eval_sha256:
        raise SystemExit(f"eval script hash mismatch for {iid}")
    for field, value in row.items():
        if spec.get(field) != value:
            raise SystemExit(f"index/spec mismatch for {iid}: {field}")
    source = snapshot_by_id.get(iid)
    if source is None:
        raise SystemExit(f"indexed instance is absent from frozen source snapshot: {iid}")
    expected_source_fields = {
        "instance_id": iid,
        "repo": source["repo"],
        "base_commit": source["base_commit"],
        "fail_to_pass": json.loads(source["FAIL_TO_PASS"]),
        "pass_to_pass": json.loads(source["PASS_TO_PASS"]),
        "image": "swebench/sweb.eval.x86_64."
        + re.sub("__", "_1776_", iid.lower())
        + ":latest",
    }
    for field, value in expected_source_fields.items():
        if spec.get(field) != value:
            raise SystemExit(f"spec/source-snapshot mismatch for {iid}: {field}")
    if "scenario_available" not in row or "identical_to_gold" not in row:
        raise SystemExit(f"corrected denominator metadata missing for {iid}")
    scenario_present = (scenario_dir / f"{stem}.scenario.py").is_file()
    if bool(row["scenario_available"]) != scenario_present:
        raise SystemExit(f"scenario availability/file mismatch for {iid}")
    if bool(row["scenario_available"]) != (iid in scenario_ids):
        raise SystemExit(f"scenario availability/summary mismatch for {iid}")
    if scenario_present:
        scenario_bytes = (scenario_dir / f"{stem}.scenario.py").read_bytes()
        if not scenario_bytes.endswith(b"\n") or hashlib.sha256(scenario_bytes[:-1]).hexdigest() != scenario_by_id[
            iid
        ].get("scenario_sha256"):
            raise SystemExit(f"scenario hash mismatch for {iid}")
legacy_ids = (
    "astropy__astropy-7336", "django__django-11133", "django__django-11477",
    "matplotlib__matplotlib-22871", "matplotlib__matplotlib-23476",
    "matplotlib__matplotlib-24970", "matplotlib__matplotlib-25311",
    "psf__requests-5414", "psf__requests-6028", "pydata__xarray-4094",
    "pydata__xarray-4356", "pydata__xarray-4629", "pydata__xarray-4966",
    "pytest-dev__pytest-5631", "pytest-dev__pytest-5809", "pytest-dev__pytest-6202",
    "pytest-dev__pytest-7432", "scikit-learn__scikit-learn-11578",
    "scikit-learn__scikit-learn-13135", "scikit-learn__scikit-learn-13142",
    "scikit-learn__scikit-learn-13328", "sphinx-doc__sphinx-7889",
    "sphinx-doc__sphinx-8621", "sympy__sympy-13480", "sympy__sympy-13551",
    "sympy__sympy-13615", "sympy__sympy-13757",
)
legacy_digest = hashlib.sha256()
legacy_valid = experiment_id == "iter200_natural_certified_yet_wrong_rate"
for iid in legacy_ids:
    for kind in ("gold", "variant"):
        name = f"{iid}.{kind}.log"
        log_path = execution_dir / name
        if not log_path.is_file():
            legacy_valid = False
            continue
        legacy_digest.update(f"{name}\0".encode())
        legacy_digest.update(log_path.read_bytes())
legacy_valid = legacy_valid and legacy_digest.hexdigest() == (
    "ce0120cd6bbd338d435b60f70c30ffe7a42709db27d2ee73a50c810be473b3ce"
)
print(f"__LEGACY_CORPUS_VALID__={int(legacy_valid)}")
print(*ids, sep="\n")
PY
)"; then
  echo "invalid or unreadable spec index: $SPECS/index.json" >&2
  exit 2
fi
mapfile -t PREFLIGHT_LINES <<< "$iid_output"
LEGACY_CORPUS_VALID="${PREFLIGHT_LINES[0]#__LEGACY_CORPUS_VALID__=}"
IIDS=("${PREFLIGHT_LINES[@]:1}")
LEGACY_IDS=" astropy__astropy-7336 django__django-11133 django__django-11477 matplotlib__matplotlib-22871 matplotlib__matplotlib-23476 matplotlib__matplotlib-24970 matplotlib__matplotlib-25311 psf__requests-5414 psf__requests-6028 pydata__xarray-4094 pydata__xarray-4356 pydata__xarray-4629 pydata__xarray-4966 pytest-dev__pytest-5631 pytest-dev__pytest-5809 pytest-dev__pytest-6202 pytest-dev__pytest-7432 scikit-learn__scikit-learn-11578 scikit-learn__scikit-learn-13135 scikit-learn__scikit-learn-13142 scikit-learn__scikit-learn-13328 sphinx-doc__sphinx-7889 sphinx-doc__sphinx-8621 sympy__sympy-13480 sympy__sympy-13551 sympy__sympy-13615 sympy__sympy-13757 "

legacy_exit_allowed() {
  local iid="$1"
  [ "$LEGACY_CORPUS_VALID" = "1" ] && [[ "$LEGACY_IDS" == *" $iid "* ]]
}

marker_ordered() {
  local file="$1" start="$2" end="$3"
  awk -v start="$start" -v end="$end" '
    $0 == start { start_count += 1; start_line = NR }
    $0 == end { end_count += 1; end_line = NR }
    END { exit !(start_count == 1 && end_count == 1 && start_line < end_line) }
  ' "$file" 2>/dev/null
}

variant_complete() {
  local stem="$1" has_scenario="$2" require_exit_markers="${3:-0}"
  local file="$OUTDIR/$stem.variant.log"
  [ -f "$file" ] || return 1
  [ "$(grep -F -x -c "APPLY_OK variant" "$file" 2>/dev/null)" -eq 1 ] || return 1
  [ "$(grep -E -c '^APPLY_OK ' "$file" 2>/dev/null)" -eq 1 ] || return 1
  ! grep -E -q '^(APPLY_FAIL|SETUP_FAIL)' "$file" || return 1
  marker_ordered "$file" ">>>>> Cert Start" ">>>>> Cert End" || return 1
  if [ "$require_exit_markers" = "1" ]; then
    [ "$(grep -E -c '^IMAGE_ID=sha256:[0-9a-f]{64}$' "$file" 2>/dev/null)" -eq 1 ] || return 1
    [ "$(grep -E -c '^IMAGE_ID=' "$file" 2>/dev/null)" -eq 1 ] || return 1
    [ "$(grep -E -c '^IMAGE_REPO_DIGEST=(UNAVAILABLE|[^[:space:]@]+@sha256:[0-9a-f]{64})$' "$file" 2>/dev/null)" -eq 1 ] || return 1
    [ "$(grep -E -c '^IMAGE_REPO_DIGEST=' "$file" 2>/dev/null)" -eq 1 ] || return 1
    [ "$(grep -E -c '^CERT_EXIT=[0-9]+$' "$file" 2>/dev/null)" -eq 1 ] || return 1
    [ "$(grep -E -c '^CERT_EXIT=' "$file" 2>/dev/null)" -eq 1 ] || return 1
  fi
  if [ "$has_scenario" = "1" ]; then
    marker_ordered "$file" ">>>>> Scenario Start" ">>>>> Scenario End" || return 1
    if [ "$require_exit_markers" = "1" ]; then
      [ "$(grep -E -c '^SCENARIO_EXIT=[0-9]+$' "$file" 2>/dev/null)" -eq 1 ] || return 1
      [ "$(grep -E -c '^SCENARIO_EXIT=' "$file" 2>/dev/null)" -eq 1 ] || return 1
    fi
  else
    grep -F -x -q "SCENARIO_UNAVAILABLE" "$file" || return 1
  fi
}

gold_complete() {
  local stem="$1" has_scenario="$2" require_exit_markers="${3:-0}"
  local file="$OUTDIR/$stem.gold.log"
  [ -f "$file" ] || return 1
  if [ "$has_scenario" = "1" ]; then
    [ "$(grep -F -x -c "APPLY_OK gold" "$file" 2>/dev/null)" -eq 1 ] || return 1
    [ "$(grep -E -c '^APPLY_OK ' "$file" 2>/dev/null)" -eq 1 ] || return 1
    ! grep -E -q '^(APPLY_FAIL|SETUP_FAIL)' "$file" || return 1
    marker_ordered "$file" ">>>>> Scenario Start" ">>>>> Scenario End" || return 1
    if [ "$require_exit_markers" = "1" ]; then
      [ "$(grep -E -c '^SCENARIO_EXIT=[0-9]+$' "$file" 2>/dev/null)" -eq 1 ] || return 1
      [ "$(grep -E -c '^SCENARIO_EXIT=' "$file" 2>/dev/null)" -eq 1 ] || return 1
    fi
  else
    grep -F -x -q "SCENARIO_UNAVAILABLE" "$file" || return 1
  fi
  if [ "$require_exit_markers" = "1" ]; then
    [ "$(grep -E -c '^IMAGE_ID=sha256:[0-9a-f]{64}$' "$file" 2>/dev/null)" -eq 1 ] || return 1
    [ "$(grep -E -c '^IMAGE_ID=' "$file" 2>/dev/null)" -eq 1 ] || return 1
    [ "$(grep -E -c '^IMAGE_REPO_DIGEST=(UNAVAILABLE|[^[:space:]@]+@sha256:[0-9a-f]{64})$' "$file" 2>/dev/null)" -eq 1 ] || return 1
    [ "$(grep -E -c '^IMAGE_REPO_DIGEST=' "$file" 2>/dev/null)" -eq 1 ] || return 1
  fi
}

failures=0
for iid in "${IIDS[@]}"; do
  stem="${iid//\//__}"
  has_scenario=0
  [ -f "$SCEN/$stem.scenario.py" ] && has_scenario=1
  require_markers=1
  legacy_exit_allowed "$iid" && require_markers=0

  if [ "$SKIP_EXISTING" = "1" ] \
    && variant_complete "$stem" "$has_scenario" "$require_markers" \
    && gold_complete "$stem" "$has_scenario" "$require_markers"; then
    echo "=== $iid (complete committed execution retained) ==="
    continue
  fi

  img="swebench/sweb.eval.x86_64.$(echo "$iid" | tr '[:upper:]' '[:lower:]' | sed 's/__/_1776_/'):latest"
  echo "=== $iid ($img) ==="
  if ! docker pull "$img" >/dev/null 2>&1; then
    echo "$iid PULL_FAIL" >&2
    failures=$((failures + 1))
    continue
  fi
  image_id="$(docker image inspect --format '{{.Id}}' "$img" 2>/dev/null)"
  repo_digest="$(docker image inspect --format '{{if .RepoDigests}}{{index .RepoDigests 0}}{{end}}' "$img" 2>/dev/null)"
  [ -n "$repo_digest" ] || repo_digest="UNAVAILABLE"
  if [[ ! "$image_id" =~ ^sha256:[0-9a-f]{64}$ ]] \
    || [[ ! "$repo_digest" =~ ^(UNAVAILABLE|[^[:space:]@]+@sha256:[0-9a-f]{64})$ ]]; then
    echo "$iid IMAGE_PROVENANCE_INSPECTION_FAIL" >&2
    failures=$((failures + 1))
    continue
  fi

  variant_rc=0
  docker run --rm \
    -e STEM="$stem" \
    -e TELOS_IMAGE_ID="$image_id" \
    -e TELOS_IMAGE_REPO_DIGEST="$repo_digest" \
    -v "$PWD/$SPECS:/specs:ro" \
    -v "$PWD/$SCEN:/scen:ro" \
    -v "$PWD/$SOLS:/sols:ro" \
    "$img" bash -lc '
set -uo pipefail
echo "IMAGE_ID=${TELOS_IMAGE_ID}"
echo "IMAGE_REPO_DIGEST=${TELOS_IMAGE_REPO_DIGEST}"
source /opt/miniconda3/bin/activate >/dev/null 2>&1 || { echo "SETUP_FAIL conda_source"; exit 20; }
conda activate testbed >/dev/null 2>&1 || { echo "SETUP_FAIL conda_activate"; exit 21; }
cd /testbed || { echo "SETUP_FAIL testbed_cd"; exit 22; }
git config --global --add safe.directory /testbed >/dev/null 2>&1 || { echo "SETUP_FAIL git_config"; exit 23; }
git checkout -- . >/dev/null 2>&1 || { echo "SETUP_FAIL git_checkout"; exit 24; }
git clean -fdq >/dev/null 2>&1 || { echo "SETUP_FAIL git_clean"; exit 25; }
if git apply -v "/sols/${STEM}.model.patch" >/dev/null 2>&1; then
  echo "APPLY_OK variant"
else
  echo "APPLY_FAIL variant"
  exit 26
fi
echo ">>>>> Cert Start"
bash "/specs/${STEM}.eval_script.sh" 2>&1
cert_rc=$?
echo "CERT_EXIT=${cert_rc}"
echo ">>>>> Cert End"
if [ -f "/scen/${STEM}.scenario.py" ]; then
  echo ">>>>> Scenario Start"
  python "/scen/${STEM}.scenario.py" 2>&1
  scenario_rc=$?
  echo "SCENARIO_EXIT=${scenario_rc}"
  echo ">>>>> Scenario End"
else
  echo "SCENARIO_UNAVAILABLE"
fi
exit 0
' > "$OUTDIR/$stem.variant.log" 2>&1 || variant_rc=$?

  if [ "$variant_rc" -ne 0 ]; then
    echo "$iid VARIANT_INFRA_FAIL exit=$variant_rc" >&2
  fi

  gold_rc=0
  if [ "$has_scenario" -eq 1 ]; then
    docker run --rm \
      -e STEM="$stem" \
      -e TELOS_IMAGE_ID="$image_id" \
      -e TELOS_IMAGE_REPO_DIGEST="$repo_digest" \
      -v "$PWD/$SCEN:/scen:ro" \
      -v "$PWD/$SOLS:/sols:ro" \
      "$img" bash -lc '
set -uo pipefail
echo "IMAGE_ID=${TELOS_IMAGE_ID}"
echo "IMAGE_REPO_DIGEST=${TELOS_IMAGE_REPO_DIGEST}"
source /opt/miniconda3/bin/activate >/dev/null 2>&1 || { echo "SETUP_FAIL conda_source"; exit 20; }
conda activate testbed >/dev/null 2>&1 || { echo "SETUP_FAIL conda_activate"; exit 21; }
cd /testbed || { echo "SETUP_FAIL testbed_cd"; exit 22; }
git config --global --add safe.directory /testbed >/dev/null 2>&1 || { echo "SETUP_FAIL git_config"; exit 23; }
git checkout -- . >/dev/null 2>&1 || { echo "SETUP_FAIL git_checkout"; exit 24; }
git clean -fdq >/dev/null 2>&1 || { echo "SETUP_FAIL git_clean"; exit 25; }
if git apply -v "/sols/${STEM}.gold.patch" >/dev/null 2>&1; then
  echo "APPLY_OK gold"
else
  echo "APPLY_FAIL gold"
  exit 26
fi
echo ">>>>> Scenario Start"
python "/scen/${STEM}.scenario.py" 2>&1
scenario_rc=$?
echo "SCENARIO_EXIT=${scenario_rc}"
echo ">>>>> Scenario End"
exit 0
' > "$OUTDIR/$stem.gold.log" 2>&1 || gold_rc=$?
  else
    printf 'IMAGE_ID=%s\nIMAGE_REPO_DIGEST=%s\nSCENARIO_UNAVAILABLE\n' \
      "$image_id" "$repo_digest" > "$OUTDIR/$stem.gold.log"
  fi

  if [ "$gold_rc" -ne 0 ]; then
    echo "$iid GOLD_INFRA_FAIL exit=$gold_rc" >&2
  fi
  if ! variant_complete "$stem" "$has_scenario" 1 \
    || ! gold_complete "$stem" "$has_scenario" 1; then
    echo "$iid INCOMPLETE_EXECUTION_EVIDENCE" >&2
    failures=$((failures + 1))
  fi
  echo "  variant: $(grep -m1 '^RESULT=' "$OUTDIR/$stem.variant.log" 2>/dev/null || echo none)"
  echo "  gold: $(grep -m1 '^RESULT=' "$OUTDIR/$stem.gold.log" 2>/dev/null || echo none)"
  docker rmi "$img" >/dev/null 2>&1 || true
done

# Reconcile the entire index, including retained rows, before allowing a green workflow.
for iid in "${IIDS[@]}"; do
  stem="${iid//\//__}"
  has_scenario=0
  [ -f "$SCEN/$stem.scenario.py" ] && has_scenario=1
  require_markers=1
  legacy_exit_allowed "$iid" && require_markers=0
  if ! variant_complete "$stem" "$has_scenario" "$require_markers" \
    || ! gold_complete "$stem" "$has_scenario" "$require_markers"; then
    echo "$iid FINAL_EVIDENCE_MISSING_OR_INCOMPLETE" >&2
    failures=$((failures + 1))
  fi
done

if [ "$failures" -ne 0 ]; then
  echo "iter200 execution failed closed: $failures evidence error(s)" >&2
  exit 1
fi
echo "=== iter200 execution logs complete for ${#IIDS[@]} indexed patches ==="
