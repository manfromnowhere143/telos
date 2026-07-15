#!/usr/bin/env bash
# Certify all 50 fixed iter202 model patches through the separately frozen
# iter203 recovery runtime. Only a same-row script from the iter203 safe-stage
# projection is ever mounted for behavioral execution.
set -uo pipefail

EXP="experiments/iter203_iter202_safety_recovery"
SPECS="$EXP/proof/raw/specs"
SCEN="$EXP/proof/raw/scenarios"
SOLS="$EXP/proof/raw/solutions"
OUTDIR="$EXP/proof/raw/execution"
RUNTIME_MANIFEST="$EXP/proof/raw/runtime_manifest.json"

SHARD_COUNT_RAW="${TELOS_ITER203_SHARD_COUNT-8}"
SHARD_INDEX_RAW="${TELOS_ITER203_SHARD_INDEX-}"
CERT_TIMEOUT_SECONDS=900
SCENARIO_TIMEOUT_SECONDS=180
KILL_GRACE_SECONDS=10
CERT_OUTPUT_LIMIT_BYTES=2097152
SCENARIO_OUTPUT_LIMIT_BYTES=262144

if [[ ! "$SHARD_INDEX_RAW" =~ ^[0-7]$ ]] || [ "$SHARD_COUNT_RAW" != "8" ]; then
  echo "iter203 requires exact shard index 0..7 and shard count 8" >&2
  exit 2
fi
SHARD_INDEX=$((10#$SHARD_INDEX_RAW))
SHARD_COUNT=8

# This stage is mechanical and must not inherit or use provider credentials.
unset OPENAI_API_KEY ANTHROPIC_API_KEY
unset PYTHONHOME PYTHONINSPECT PYTHONPATH PYTHONSTARTUP PYTHONUSERBASE

python3 -I -S scripts/build_iter203_safety_recovery.py --check || exit 2
python3 -I -S scripts/build_iter203_runtime_manifest.py --check || exit 2

if [ -e "$OUTDIR" ] && [ ! -d "$OUTDIR" ]; then
  echo "iter203 execution output path is not a directory" >&2
  exit 2
fi
mkdir -p "$OUTDIR"
if find "$OUTDIR" -mindepth 1 -print -quit | grep -q .; then
  echo "iter203 shard refuses pre-existing execution evidence" >&2
  exit 2
fi

if ! plan="$({
  python3 -I -S scripts/collect_iter203_execution.py source-lines \
    --spec-index "$SPECS/index.json" \
    --runtime-manifest "$RUNTIME_MANIFEST"
})"; then
  echo "iter203 execution source preflight failed" >&2
  exit 2
fi

ALL_LINES=()
while IFS= read -r line; do
  [ -n "$line" ] && ALL_LINES+=("$line")
done <<< "$plan"
if [ "${#ALL_LINES[@]}" -ne 50 ]; then
  echo "iter203 execution requires exactly 50 preflight rows" >&2
  exit 2
fi

LINES=()
for ordinal in "${!ALL_LINES[@]}"; do
  if (( ordinal % SHARD_COUNT == SHARD_INDEX )); then
    LINES+=("${ALL_LINES[$ordinal]}")
  fi
done
if [ "${#LINES[@]}" -gt 7 ]; then
  echo "iter203 shard exceeds the frozen seven-row ceiling" >&2
  exit 2
fi
echo "=== iter203 shard $SHARD_INDEX/8 selected ${#LINES[@]}/50 valid patches ==="

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

marker_ordered() {
  local file="$1" start="$2" end="$3"
  awk -v start="$start" -v end="$end" '
    $0 == start { starts += 1; start_line = NR }
    $0 == end { ends += 1; end_line = NR }
    END { exit !(starts == 1 && ends == 1 && start_line < end_line) }
  ' "$file" 2>/dev/null
}

variant_complete() {
  local file="$1" behavior="$2"
  [ -f "$file" ] || return 1
  [ "$(grep -F -x -c 'APPLY_OK variant' "$file" 2>/dev/null)" -eq 1 ] || return 1
  [ "$(grep -E -c '^IMAGE_ID=sha256:[0-9a-f]{64}$' "$file" 2>/dev/null)" -eq 1 ] || return 1
  [ "$(grep -E -c '^IMAGE_REPO_DIGEST=[^[:space:]@]+@sha256:[0-9a-f]{64}$' "$file" 2>/dev/null)" -eq 1 ] || return 1
  [ "$(grep -E -c '^CERT_EXIT=[0-9]+$' "$file" 2>/dev/null)" -eq 1 ] || return 1
  marker_ordered "$file" ">>>>> Cert Start" ">>>>> Cert End" || return 1
  ! grep -E -q '^(APPLY_FAIL|SETUP_FAIL)' "$file" || return 1
  if [ "$behavior" = "safe_scenario" ]; then
    marker_ordered "$file" ">>>>> Scenario Start" ">>>>> Scenario End" || return 1
    [ "$(grep -E -c '^SCENARIO_EXIT=[0-9]+$' "$file" 2>/dev/null)" -eq 1 ] || return 1
    [ "$(grep -c '^RESULT=' "$file" 2>/dev/null)" -eq 1 ] || return 1
    ! grep -q '^SCENARIO_NOT_EXECUTED' "$file" || return 1
  else
    [ "$(grep -F -x -c 'SCENARIO_NOT_EXECUTED disposition=no_safe_scenario' "$file" 2>/dev/null)" -eq 1 ] || return 1
    ! grep -q '^>>>>> Scenario ' "$file" || return 1
  fi
}

gold_complete() {
  local file="$1" behavior="$2"
  [ -f "$file" ] || return 1
  [ "$(grep -E -c '^IMAGE_ID=sha256:[0-9a-f]{64}$' "$file" 2>/dev/null)" -eq 1 ] || return 1
  [ "$(grep -E -c '^IMAGE_REPO_DIGEST=[^[:space:]@]+@sha256:[0-9a-f]{64}$' "$file" 2>/dev/null)" -eq 1 ] || return 1
  ! grep -E -q '^(APPLY_FAIL|SETUP_FAIL)' "$file" || return 1
  if [ "$behavior" = "safe_scenario" ]; then
    [ "$(grep -F -x -c 'APPLY_OK gold' "$file" 2>/dev/null)" -eq 1 ] || return 1
    marker_ordered "$file" ">>>>> Scenario Start" ">>>>> Scenario End" || return 1
    [ "$(grep -E -c '^SCENARIO_EXIT=[0-9]+$' "$file" 2>/dev/null)" -eq 1 ] || return 1
    [ "$(grep -c '^RESULT=' "$file" 2>/dev/null)" -eq 1 ] || return 1
    ! grep -q '^SCENARIO_NOT_EXECUTED' "$file" || return 1
  else
    [ "$(grep -F -x -c 'SCENARIO_NOT_EXECUTED disposition=no_safe_scenario' "$file" 2>/dev/null)" -eq 1 ] || return 1
    ! grep -q '^APPLY_' "$file" || return 1
    ! grep -q '^>>>>> Scenario ' "$file" || return 1
  fi
}

run_container() {
  local mode="$1" stem="$2" image_ref="$3" image_id="$4" repo_digest="$5" output="$6"
  local patch_name="model"
  local log_kind="variant"
  [ "$mode" = "gold-behavior" ] && patch_name="gold" && log_kind="gold"
  local scenario_mount=()
  if [ "$mode" = "variant-behavior" ] || [ "$mode" = "gold-behavior" ]; then
    scenario_mount=(-v "$PWD/$SCEN/$stem.scenario.py:/scenario/scenario.py:ro")
  fi
  docker run --rm \
    "${DOCKER_SAFETY_ARGS[@]}" \
    -e STEM="$stem" \
    -e PATCH_NAME="$patch_name" \
    -e LOG_KIND="$log_kind" \
    -e EXECUTION_MODE="$mode" \
    -e TELOS_IMAGE_ID="$image_id" \
    -e TELOS_IMAGE_REPO_DIGEST="$repo_digest" \
    -e CERT_TIMEOUT_SECONDS="$CERT_TIMEOUT_SECONDS" \
    -e SCENARIO_TIMEOUT_SECONDS="$SCENARIO_TIMEOUT_SECONDS" \
    -e KILL_GRACE_SECONDS="$KILL_GRACE_SECONDS" \
    -e CERT_OUTPUT_LIMIT_BYTES="$CERT_OUTPUT_LIMIT_BYTES" \
    -e SCENARIO_OUTPUT_LIMIT_BYTES="$SCENARIO_OUTPUT_LIMIT_BYTES" \
    -v "$PWD/$SPECS/$stem.eval_script.sh:/specs/$stem.eval_script.sh:ro" \
    -v "$PWD/$SPECS/$stem.spec.json:/specs/$stem.spec.json:ro" \
    -v "$PWD/$SOLS/$stem.$patch_name.patch:/solutions/$stem.$patch_name.patch:ro" \
    "${scenario_mount[@]}" \
    "$image_ref" bash -lc '
set -uo pipefail
if [ "$EXECUTION_MODE" != "variant-behavior" ]; then
  echo "IMAGE_ID=${TELOS_IMAGE_ID}"
  echo "IMAGE_REPO_DIGEST=${TELOS_IMAGE_REPO_DIGEST}"
fi
source /opt/miniconda3/bin/activate >/dev/null 2>&1 || { echo "SETUP_FAIL conda_source"; exit 20; }
conda activate testbed >/dev/null 2>&1 || { echo "SETUP_FAIL conda_activate"; exit 21; }
cd /testbed || { echo "SETUP_FAIL testbed_cd"; exit 22; }
CONTROLLER_PYTHON="$(command -v python)" || { echo "SETUP_FAIL controller_python"; exit 23; }
case "$CONTROLLER_PYTHON" in
  /opt/miniconda3/bin/python|/opt/miniconda3/envs/testbed/bin/python) ;;
  *) echo "SETUP_FAIL controller_python_path"; exit 23 ;;
esac
run_bounded() {
  local timeout_seconds="$1" limit_bytes="$2"
  shift 2
  timeout --signal=TERM --kill-after="${KILL_GRACE_SECONDS}s" "${timeout_seconds}s" "$@" 2>&1 | "$CONTROLLER_PYTHON" -I -S -c "
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
  local -a statuses=("${PIPESTATUS[@]}")
  if [ "${statuses[1]}" -ne 0 ]; then
    echo "SETUP_FAIL output_limit_or_limiter exit=${statuses[1]}"
    return 125
  fi
  return "${statuses[0]}"
}
git config --global --add safe.directory /testbed >/dev/null 2>&1 || { echo "SETUP_FAIL git_config"; exit 24; }
git checkout -- . >/dev/null 2>&1 || { echo "SETUP_FAIL git_checkout"; exit 25; }
git clean -fdq >/dev/null 2>&1 || { echo "SETUP_FAIL git_clean"; exit 26; }
if git apply -v "/solutions/${STEM}.${PATCH_NAME}.patch" >/dev/null 2>&1; then
  if [ "$EXECUTION_MODE" != "variant-behavior" ]; then
    echo "APPLY_OK ${LOG_KIND}"
  fi
else
  echo "SETUP_FAIL ${EXECUTION_MODE}_apply"
  exit 27
fi
if [ "$EXECUTION_MODE" = "variant-cert" ]; then
  echo ">>>>> Cert Start"
  run_bounded "$CERT_TIMEOUT_SECONDS" "$CERT_OUTPUT_LIMIT_BYTES" bash "/specs/${STEM}.eval_script.sh"
  cert_rc=$?
  cert_infra=0
  if [ "$cert_rc" -eq 124 ] || [ "$cert_rc" -eq 137 ] || [ "$cert_rc" -eq 125 ]; then
    echo "SETUP_FAIL certification_bounded_execution exit=${cert_rc}"
    cert_infra=1
  fi
  echo "CERT_EXIT=${cert_rc}"
  echo ">>>>> Cert End"
  [ "$cert_infra" -eq 0 ] || exit 28
else
  [ -f /scenario/scenario.py ] || { echo "SETUP_FAIL safe_scenario_mount"; exit 28; }
  echo ">>>>> Scenario Start"
  run_bounded "$SCENARIO_TIMEOUT_SECONDS" "$SCENARIO_OUTPUT_LIMIT_BYTES" python /scenario/scenario.py
  scenario_rc=$?
  scenario_infra=0
  if [ "$scenario_rc" -eq 124 ] || [ "$scenario_rc" -eq 137 ] || [ "$scenario_rc" -eq 125 ]; then
    echo "SETUP_FAIL scenario_bounded_execution exit=${scenario_rc}"
    scenario_infra=1
  fi
  echo "SCENARIO_EXIT=${scenario_rc}"
  echo ">>>>> Scenario End"
  [ "$scenario_infra" -eq 0 ] || exit 29
fi
exit 0
' > "$output" 2>&1
}

failures=0
for line in "${LINES[@]}"; do
  IFS=$'\t' read -r iid tag manifest_digest expected_image_id image_ref behavior <<< "$line"
  stem="${iid//\//__}"
  if [ "$image_ref" != "${tag%:*}@${manifest_digest}" ]; then
    echo "$iid IMAGE_LOCK_REFERENCE_MISMATCH" >&2
    failures=$((failures + 1))
    continue
  fi
  if [ "$behavior" = "safe_scenario" ]; then
    if [ ! -f "$SCEN/$stem.scenario.py" ]; then
      echo "$iid SAFE_SCENARIO_MISSING" >&2
      failures=$((failures + 1))
      continue
    fi
  elif [ "$behavior" != "no_safe_scenario" ]; then
    echo "$iid UNKNOWN_BEHAVIOR_DISPOSITION" >&2
    failures=$((failures + 1))
    continue
  fi

  echo "=== $iid ($behavior) ==="
  if ! docker pull "$image_ref" >/dev/null 2>&1; then
    echo "$iid PULL_FAIL" >&2
    failures=$((failures + 1))
    continue
  fi
  image_id="$(docker image inspect --format '{{.Id}}' "$image_ref" 2>/dev/null)"
  repo_digests="$(docker image inspect --format '{{json .RepoDigests}}' "$image_ref" 2>/dev/null)"
  if [ "$image_id" != "$expected_image_id" ] || ! python3 - "$repo_digests" "$image_ref" <<'PY'
import json
import re
import sys
try:
    values = json.loads(sys.argv[1])
except json.JSONDecodeError:
    raise SystemExit(1)
expected = sys.argv[2]
if (
    not re.fullmatch(r"[^\s@]+@sha256:[0-9a-f]{64}", expected)
    or not isinstance(values, list)
    or expected not in values
    or any(not isinstance(value, str) or not re.fullmatch(r"[^\s@]+@sha256:[0-9a-f]{64}", value) for value in values)
):
    raise SystemExit(1)
PY
  then
    echo "$iid IMAGE_PROVENANCE_MISMATCH" >&2
    failures=$((failures + 1))
    docker rmi "$image_ref" >/dev/null 2>&1 || true
    continue
  fi

  variant_tmp="$(mktemp "$OUTDIR/.${stem}.variant.XXXXXX.tmp")"
  gold_tmp="$(mktemp "$OUTDIR/.${stem}.gold.XXXXXX.tmp")"
  behavior_tmp=""
  variant_rc=0
  gold_rc=0
  run_container variant-cert "$stem" "$image_ref" "$image_id" "$image_ref" "$variant_tmp" || variant_rc=$?
  if [ "$variant_rc" -ne 0 ]; then
    echo "$iid CERTIFICATION_INFRA_FAIL exit=$variant_rc" >&2
    rm -f "$variant_tmp" "$gold_tmp"
    failures=$((failures + 1))
    docker rmi "$image_ref" >/dev/null 2>&1 || true
    continue
  fi
  if [ "$behavior" = "safe_scenario" ]; then
    behavior_tmp="$(mktemp "$OUTDIR/.${stem}.behavior.XXXXXX.tmp")"
    run_container variant-behavior "$stem" "$image_ref" "$image_id" "$image_ref" "$behavior_tmp" || variant_rc=$?
    if [ "$variant_rc" -eq 0 ]; then
      if ! cat "$behavior_tmp" >> "$variant_tmp"; then
        variant_rc=30
      fi
    fi
    rm -f "$behavior_tmp"
    run_container gold-behavior "$stem" "$image_ref" "$image_id" "$image_ref" "$gold_tmp" || gold_rc=$?
  else
    printf 'SCENARIO_NOT_EXECUTED disposition=no_safe_scenario\n' >> "$variant_tmp"
    printf 'IMAGE_ID=%s\nIMAGE_REPO_DIGEST=%s\nSCENARIO_NOT_EXECUTED disposition=no_safe_scenario\n' \
      "$image_id" "$image_ref" > "$gold_tmp"
  fi
  if [ "$variant_rc" -ne 0 ] || [ "$gold_rc" -ne 0 ] \
    || ! variant_complete "$variant_tmp" "$behavior" \
    || ! gold_complete "$gold_tmp" "$behavior"; then
    echo "$iid INCOMPLETE_EXECUTION_EVIDENCE variant=$variant_rc gold=$gold_rc" >&2
    rm -f "$variant_tmp" "$gold_tmp"
    failures=$((failures + 1))
  else
    python3 -I -S scripts/collect_iter203_execution.py publish-log \
      --source "$variant_tmp" --destination "$OUTDIR/$stem.variant.log" || failures=$((failures + 1))
    python3 -I -S scripts/collect_iter203_execution.py publish-log \
      --source "$gold_tmp" --destination "$OUTDIR/$stem.gold.log" || failures=$((failures + 1))
  fi
  docker rmi "$image_ref" >/dev/null 2>&1 || true
done

if [ "$failures" -ne 0 ]; then
  echo "iter203 execution failed closed: $failures evidence error(s)" >&2
  exit 1
fi

python3 -I -S scripts/collect_iter203_execution.py shard-receipt \
  --execution-dir "$OUTDIR" \
  --spec-index "$SPECS/index.json" \
  --runtime-manifest "$RUNTIME_MANIFEST" \
  --shard-index "$SHARD_INDEX" \
  --shard-count "$SHARD_COUNT" || exit 2

echo "=== iter203 shard $SHARD_INDEX/8 complete: ${#LINES[@]} valid patches ==="
