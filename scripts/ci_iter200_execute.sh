#!/usr/bin/env bash
# Certify every neutral-solve model patch and, when available, execute its gold-differential scenario.
# Test failures are measurement outcomes; missing/apply/setup/incomplete evidence is an infrastructure
# failure and makes the job fail after all rows have been attempted.
set -uo pipefail

NAT_EXP="${TELOS_NAT_EXP:-iter200_natural_certified_yet_wrong_rate}"
SKIP_EXISTING="${TELOS_NAT_SKIP_EXISTING:-0}"
ITER202_EXP="iter202_natural_rate_scaled"
SPECS="experiments/${NAT_EXP}/proof/raw/specs"
SCEN="experiments/${NAT_EXP}/proof/raw/scenarios"
SOLS="experiments/${NAT_EXP}/proof/raw/solutions"
OUTDIR="experiments/${NAT_EXP}/proof/raw/execution"
IMAGE_LOCK="experiments/${ITER202_EXP}/proof/raw/image_lock.json"
RUNTIME_MANIFEST="experiments/${ITER202_EXP}/proof/raw/runtime_manifest.json"
EXECUTION_HARDENED=0
ITER202_CERT_TIMEOUT_SECONDS=900
ITER202_SCENARIO_TIMEOUT_SECONDS=180
ITER202_KILL_GRACE_SECONDS=10
ITER202_CERT_OUTPUT_LIMIT_BYTES=2097152
ITER202_SCENARIO_OUTPUT_LIMIT_BYTES=262144

validate_shard_config() {
  local index="$1" count="$2"
  [[ "$index" =~ ^(0|[1-9][0-9]{0,2})$ ]] || return 1
  [[ "$count" =~ ^[1-9][0-9]{0,2}$ ]] || return 1
  local index_value=$((10#$index)) count_value=$((10#$count))
  (( count_value >= 1 && count_value <= 256 && index_value < count_value ))
}

validate_experiment_shard_config() {
  local experiment="$1" index="$2" count="$3"
  validate_shard_config "$index" "$count" || return 1
  if [ "$experiment" = "$ITER202_EXP" ]; then
    [ "$count" = "8" ] || return 1
  fi
}

shard_member() {
  local ordinal="$1"
  (( ordinal % SHARD_COUNT == SHARD_INDEX ))
}

SHARD_INDEX_RAW="${TELOS_NAT_SHARD_INDEX-0}"
SHARD_COUNT_RAW="${TELOS_NAT_SHARD_COUNT-1}"
if ! validate_experiment_shard_config "$NAT_EXP" "$SHARD_INDEX_RAW" "$SHARD_COUNT_RAW"; then
  echo "invalid shard config: index=$SHARD_INDEX_RAW count=$SHARD_COUNT_RAW" >&2
  exit 2
fi
SHARD_INDEX=$((10#$SHARD_INDEX_RAW))
SHARD_COUNT=$((10#$SHARD_COUNT_RAW))
mkdir -p "$OUTDIR"

DOCKER_SAFETY_ARGS=()
if [ "$NAT_EXP" = "$ITER202_EXP" ]; then
  EXECUTION_HARDENED=1
  python3 scripts/build_iter202_image_lock.py --check || exit 2
  python3 scripts/validate_iter202_scenario_safety.py || exit 2
  python3 scripts/validate_iter202_runtime_freeze.py --check || exit 2
  DOCKER_SAFETY_ARGS=(
    --network none
    --cap-drop ALL
    --security-opt no-new-privileges=true
    --pids-limit 1024
    --memory 10g
    --cpus 4
    --log-driver local
    --log-opt max-size=3m
    --log-opt max-file=1
  )
fi

if ! iid_output="$(python3 - "$SPECS/index.json" "$SPECS" "$SCEN" "$SOLS" "$NAT_EXP" "$OUTDIR" "$IMAGE_LOCK" <<'PY'
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
image_lock_path = Path(sys.argv[7])
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
    identical = model_path.read_bytes().rstrip(b"\n") == gold_path.read_bytes().rstrip(b"\n")
    if identical != bool(row["identical_to_gold"]):
        raise SystemExit(f"normalized gold-equivalence metadata mismatch for {iid}")
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
    if gold_path.read_text() != source["patch"]:
        raise SystemExit(f"gold patch/source-snapshot mismatch for {iid}")
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
if experiment_id == "iter202_natural_rate_scaled":
    lock = json.loads(image_lock_path.read_text())
    lock_rows = lock.get("images")
    if (
        lock.get("schema_version") != "telos.iter202.image_lock.v1"
        or lock.get("count") != 53
        or not isinstance(lock_rows, list)
        or len(lock_rows) != 53
    ):
        raise SystemExit("iter202 immutable image lock is malformed")
    by_locked_id = {
        row.get("instance_id"): row for row in lock_rows if isinstance(row, dict)
    }
    if len(by_locked_id) != 53:
        raise SystemExit("iter202 immutable image lock contains duplicate rows")
    for iid in ids:
        locked = by_locked_id.get(iid)
        if locked is None:
            raise SystemExit(f"iter202 image lock does not cover {iid}")
        values = (
            iid,
            locked.get("tag"),
            locked.get("manifest_digest"),
            locked.get("image_id"),
            locked.get("reference"),
        )
        if not all(isinstance(value, str) and value for value in values):
            raise SystemExit(f"iter202 image lock row is malformed for {iid}")
        print("\t".join(values))
else:
    print(*ids, sep="\n")
PY
)"; then
  echo "invalid or unreadable spec index: $SPECS/index.json" >&2
  exit 2
fi
PREFLIGHT_LINES=()
while IFS= read -r line; do
  PREFLIGHT_LINES+=("$line")
done <<< "$iid_output"
LEGACY_CORPUS_VALID="${PREFLIGHT_LINES[0]#__LEGACY_CORPUS_VALID__=}"
ALL_IIDS=()
ALL_LOCK_TAGS=()
ALL_LOCK_MANIFEST_DIGESTS=()
ALL_LOCK_IMAGE_IDS=()
ALL_LOCK_REFS=()
for line in "${PREFLIGHT_LINES[@]:1}"; do
  IFS=$'\t' read -r iid lock_tag lock_manifest_digest lock_image_id lock_ref <<< "$line"
  ALL_IIDS+=("$iid")
  ALL_LOCK_TAGS+=("$lock_tag")
  ALL_LOCK_MANIFEST_DIGESTS+=("$lock_manifest_digest")
  ALL_LOCK_IMAGE_IDS+=("$lock_image_id")
  ALL_LOCK_REFS+=("$lock_ref")
done
IIDS=()
LOCK_TAGS=()
LOCK_MANIFEST_DIGESTS=()
LOCK_IMAGE_IDS=()
LOCK_REFS=()
# Ordinals are over the complete ordered valid-solution/spec index, which the
# preflight above proves exactly covers every valid patch derived from the
# frozen 53-target solve. They are not ordinals over the original target list.
for ordinal in "${!ALL_IIDS[@]}"; do
  if shard_member "$ordinal"; then
    IIDS+=("${ALL_IIDS[$ordinal]}")
    LOCK_TAGS+=("${ALL_LOCK_TAGS[$ordinal]}")
    LOCK_MANIFEST_DIGESTS+=("${ALL_LOCK_MANIFEST_DIGESTS[$ordinal]}")
    LOCK_IMAGE_IDS+=("${ALL_LOCK_IMAGE_IDS[$ordinal]}")
    LOCK_REFS+=("${ALL_LOCK_REFS[$ordinal]}")
  fi
done
echo "=== execution shard $SHARD_INDEX/$SHARD_COUNT selected ${#IIDS[@]}/${#ALL_IIDS[@]} indexed patches ==="
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
for idx in "${!IIDS[@]}"; do
  iid="${IIDS[$idx]}"
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

  if [ "$NAT_EXP" = "$ITER202_EXP" ]; then
    img="${LOCK_TAGS[$idx]}"
    image_ref="${LOCK_REFS[$idx]}"
    expected_manifest_digest="${LOCK_MANIFEST_DIGESTS[$idx]}"
    expected_image_id="${LOCK_IMAGE_IDS[$idx]}"
    expected_repo_digest="$image_ref"
    if [ "$image_ref" != "${img%:*}@${expected_manifest_digest}" ]; then
      echo "$iid IMAGE_LOCK_REFERENCE_MISMATCH" >&2
      failures=$((failures + 1))
      continue
    fi
  else
    img="swebench/sweb.eval.x86_64.$(echo "$iid" | tr '[:upper:]' '[:lower:]' | sed 's/__/_1776_/'):latest"
    image_ref="$img"
    expected_manifest_digest=""
    expected_image_id=""
    expected_repo_digest=""
  fi
  echo "=== $iid ($image_ref) ==="
  if ! docker pull "$image_ref" >/dev/null 2>&1; then
    echo "$iid PULL_FAIL" >&2
    failures=$((failures + 1))
    continue
  fi
  image_id="$(docker image inspect --format '{{.Id}}' "$image_ref" 2>/dev/null)"
  if [ "$NAT_EXP" = "$ITER202_EXP" ]; then
    repo_digests_json="$(docker image inspect --format '{{json .RepoDigests}}' "$image_ref" 2>/dev/null)"
    if [ "$image_id" != "$expected_image_id" ]; then
      echo "$iid IMAGE_ID_LOCK_MISMATCH" >&2
      failures=$((failures + 1))
      continue
    fi
    if ! python3 - "$repo_digests_json" "$expected_repo_digest" <<'PY'
import json
import re
import sys

try:
    repo_digests = json.loads(sys.argv[1])
except json.JSONDecodeError:
    raise SystemExit(1)
expected = sys.argv[2]
if (
    expected == "UNAVAILABLE"
    or not re.fullmatch(r"[^\s@]+@sha256:[0-9a-f]{64}", expected)
    or not isinstance(repo_digests, list)
    or expected not in repo_digests
    or any(
        not isinstance(value, str)
        or not re.fullmatch(r"[^\s@]+@sha256:[0-9a-f]{64}", value)
        for value in repo_digests
    )
):
    raise SystemExit(1)
PY
    then
      echo "$iid IMAGE_REPO_DIGEST_MISMATCH" >&2
      failures=$((failures + 1))
      continue
    fi
    repo_digest="$expected_repo_digest"
  else
    repo_digest="$(docker image inspect --format '{{if .RepoDigests}}{{index .RepoDigests 0}}{{end}}' "$image_ref" 2>/dev/null)"
    [ -n "$repo_digest" ] || repo_digest="UNAVAILABLE"
    if [[ ! "$image_id" =~ ^sha256:[0-9a-f]{64}$ ]] \
      || [[ ! "$repo_digest" =~ ^(UNAVAILABLE|[^[:space:]@]+@sha256:[0-9a-f]{64})$ ]]; then
      echo "$iid IMAGE_PROVENANCE_INSPECTION_FAIL" >&2
      failures=$((failures + 1))
      continue
    fi
  fi

  variant_rc=0
  docker run --rm \
    "${DOCKER_SAFETY_ARGS[@]}" \
    -e STEM="$stem" \
    -e TELOS_IMAGE_ID="$image_id" \
    -e TELOS_IMAGE_REPO_DIGEST="$repo_digest" \
    -e TELOS_EXECUTION_HARDENED="$EXECUTION_HARDENED" \
    -e TELOS_CERT_TIMEOUT_SECONDS="$ITER202_CERT_TIMEOUT_SECONDS" \
    -e TELOS_SCENARIO_TIMEOUT_SECONDS="$ITER202_SCENARIO_TIMEOUT_SECONDS" \
    -e TELOS_KILL_GRACE_SECONDS="$ITER202_KILL_GRACE_SECONDS" \
    -e TELOS_CERT_OUTPUT_LIMIT_BYTES="$ITER202_CERT_OUTPUT_LIMIT_BYTES" \
    -e TELOS_SCENARIO_OUTPUT_LIMIT_BYTES="$ITER202_SCENARIO_OUTPUT_LIMIT_BYTES" \
    -v "$PWD/$SPECS:/specs:ro" \
    -v "$PWD/$SCEN:/scen:ro" \
    -v "$PWD/$SOLS:/sols:ro" \
    "$image_ref" bash -lc '
set -uo pipefail
echo "IMAGE_ID=${TELOS_IMAGE_ID}"
echo "IMAGE_REPO_DIGEST=${TELOS_IMAGE_REPO_DIGEST}"
source /opt/miniconda3/bin/activate >/dev/null 2>&1 || { echo "SETUP_FAIL conda_source"; exit 20; }
conda activate testbed >/dev/null 2>&1 || { echo "SETUP_FAIL conda_activate"; exit 21; }
cd /testbed || { echo "SETUP_FAIL testbed_cd"; exit 22; }
run_bounded() {
  local timeout_seconds="$1" limit_bytes="$2"
  shift 2
  timeout --signal=TERM --kill-after="${TELOS_KILL_GRACE_SECONDS}s" "${timeout_seconds}s" "$@" 2>&1 | python -c "
import sys
limit = int(sys.argv[1])
written = 0
truncated = False
while True:
    chunk = sys.stdin.buffer.read(65536)
    if not chunk:
        break
    remaining = max(0, limit - written)
    if remaining:
        emitted = chunk[:remaining]
        sys.stdout.buffer.write(emitted)
        written += len(emitted)
    if len(chunk) > remaining:
        truncated = True
if truncated:
    sys.stdout.buffer.write(b\"\\nTELOS_OUTPUT_TRUNCATED limit_bytes=\" + str(limit).encode() + b\"\\n\")
sys.stdout.buffer.flush()
raise SystemExit(3 if truncated else 0)
" "$limit_bytes"
  local -a pipeline_status=("${PIPESTATUS[@]}")
  if [ "${pipeline_status[1]}" -eq 3 ]; then
    echo "SETUP_FAIL output_limit limit_bytes=${limit_bytes}"
    return 125
  fi
  if [ "${pipeline_status[1]}" -ne 0 ]; then
    echo "SETUP_FAIL output_limiter exit=${pipeline_status[1]}"
    return 125
  fi
  return "${pipeline_status[0]}"
}
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
if [ "$TELOS_EXECUTION_HARDENED" = "1" ]; then
  run_bounded "$TELOS_CERT_TIMEOUT_SECONDS" "$TELOS_CERT_OUTPUT_LIMIT_BYTES" \
    bash "/specs/${STEM}.eval_script.sh"
else
  bash "/specs/${STEM}.eval_script.sh" 2>&1
fi
cert_rc=$?
if [ "$TELOS_EXECUTION_HARDENED" = "1" ] \
  && { [ "$cert_rc" -eq 124 ] || [ "$cert_rc" -eq 137 ]; }; then
  echo "SETUP_FAIL cert_timeout limit_seconds=${TELOS_CERT_TIMEOUT_SECONDS}"
fi
echo "CERT_EXIT=${cert_rc}"
echo ">>>>> Cert End"
if [ -f "/scen/${STEM}.scenario.py" ]; then
  echo ">>>>> Scenario Start"
  if [ "$TELOS_EXECUTION_HARDENED" = "1" ]; then
    run_bounded "$TELOS_SCENARIO_TIMEOUT_SECONDS" "$TELOS_SCENARIO_OUTPUT_LIMIT_BYTES" \
      python "/scen/${STEM}.scenario.py"
  else
    python "/scen/${STEM}.scenario.py" 2>&1
  fi
  scenario_rc=$?
  if [ "$TELOS_EXECUTION_HARDENED" = "1" ] \
    && { [ "$scenario_rc" -eq 124 ] || [ "$scenario_rc" -eq 137 ]; }; then
    echo "SETUP_FAIL scenario_timeout limit_seconds=${TELOS_SCENARIO_TIMEOUT_SECONDS}"
  fi
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
      "${DOCKER_SAFETY_ARGS[@]}" \
      -e STEM="$stem" \
      -e TELOS_IMAGE_ID="$image_id" \
      -e TELOS_IMAGE_REPO_DIGEST="$repo_digest" \
      -e TELOS_EXECUTION_HARDENED="$EXECUTION_HARDENED" \
      -e TELOS_CERT_TIMEOUT_SECONDS="$ITER202_CERT_TIMEOUT_SECONDS" \
      -e TELOS_SCENARIO_TIMEOUT_SECONDS="$ITER202_SCENARIO_TIMEOUT_SECONDS" \
      -e TELOS_KILL_GRACE_SECONDS="$ITER202_KILL_GRACE_SECONDS" \
      -e TELOS_CERT_OUTPUT_LIMIT_BYTES="$ITER202_CERT_OUTPUT_LIMIT_BYTES" \
      -e TELOS_SCENARIO_OUTPUT_LIMIT_BYTES="$ITER202_SCENARIO_OUTPUT_LIMIT_BYTES" \
      -v "$PWD/$SCEN:/scen:ro" \
      -v "$PWD/$SOLS:/sols:ro" \
      "$image_ref" bash -lc '
set -uo pipefail
echo "IMAGE_ID=${TELOS_IMAGE_ID}"
echo "IMAGE_REPO_DIGEST=${TELOS_IMAGE_REPO_DIGEST}"
source /opt/miniconda3/bin/activate >/dev/null 2>&1 || { echo "SETUP_FAIL conda_source"; exit 20; }
conda activate testbed >/dev/null 2>&1 || { echo "SETUP_FAIL conda_activate"; exit 21; }
cd /testbed || { echo "SETUP_FAIL testbed_cd"; exit 22; }
run_bounded() {
  local timeout_seconds="$1" limit_bytes="$2"
  shift 2
  timeout --signal=TERM --kill-after="${TELOS_KILL_GRACE_SECONDS}s" "${timeout_seconds}s" "$@" 2>&1 | python -c "
import sys
limit = int(sys.argv[1])
written = 0
truncated = False
while True:
    chunk = sys.stdin.buffer.read(65536)
    if not chunk:
        break
    remaining = max(0, limit - written)
    if remaining:
        emitted = chunk[:remaining]
        sys.stdout.buffer.write(emitted)
        written += len(emitted)
    if len(chunk) > remaining:
        truncated = True
if truncated:
    sys.stdout.buffer.write(b\"\\nTELOS_OUTPUT_TRUNCATED limit_bytes=\" + str(limit).encode() + b\"\\n\")
sys.stdout.buffer.flush()
raise SystemExit(3 if truncated else 0)
" "$limit_bytes"
  local -a pipeline_status=("${PIPESTATUS[@]}")
  if [ "${pipeline_status[1]}" -eq 3 ]; then
    echo "SETUP_FAIL output_limit limit_bytes=${limit_bytes}"
    return 125
  fi
  if [ "${pipeline_status[1]}" -ne 0 ]; then
    echo "SETUP_FAIL output_limiter exit=${pipeline_status[1]}"
    return 125
  fi
  return "${pipeline_status[0]}"
}
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
if [ "$TELOS_EXECUTION_HARDENED" = "1" ]; then
  run_bounded "$TELOS_SCENARIO_TIMEOUT_SECONDS" "$TELOS_SCENARIO_OUTPUT_LIMIT_BYTES" \
    python "/scen/${STEM}.scenario.py"
else
  python "/scen/${STEM}.scenario.py" 2>&1
fi
scenario_rc=$?
if [ "$TELOS_EXECUTION_HARDENED" = "1" ] \
  && { [ "$scenario_rc" -eq 124 ] || [ "$scenario_rc" -eq 137 ]; }; then
  echo "SETUP_FAIL scenario_timeout limit_seconds=${TELOS_SCENARIO_TIMEOUT_SECONDS}"
fi
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
  docker rmi "$image_ref" >/dev/null 2>&1 || true
done

# Reconcile the entire index, including retained rows, before allowing a green workflow.
for idx in "${!IIDS[@]}"; do
  iid="${IIDS[$idx]}"
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
  echo "natural-rate execution failed closed: $failures evidence error(s)" >&2
  exit 1
fi
if [ "$NAT_EXP" = "$ITER202_EXP" ]; then
  if ! python3 scripts/collect_iter202_execution.py shard-receipt \
    --execution-dir "$OUTDIR" \
    --spec-index "$SPECS/index.json" \
    --runtime-manifest "$RUNTIME_MANIFEST" \
    --shard-index "$SHARD_INDEX" \
    --shard-count "$SHARD_COUNT"; then
    echo "iter202 shard receipt generation failed closed" >&2
    exit 2
  fi
fi
echo "=== natural-rate execution logs complete for shard $SHARD_INDEX/$SHARD_COUNT: ${#IIDS[@]} indexed patches ==="
