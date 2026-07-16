#!/usr/bin/env bash
# Certify the unchanged iter203 plan through the separately identified iter204
# infrastructure recovery. Historical iter203 runtime/evidence stays immutable.
set -uo pipefail

SOURCE_EXP="experiments/iter203_iter202_safety_recovery"
EXP="experiments/iter204_iter203_infrastructure_recovery"
SPECS="$SOURCE_EXP/proof/raw/specs"
SCEN="$SOURCE_EXP/proof/raw/scenarios"
SOLS="$SOURCE_EXP/proof/raw/solutions"
OUTDIR="$EXP/proof/raw/execution"
DIAGDIR="$EXP/proof/raw/runtime_diagnostics"
RUNTIME_MANIFEST="$EXP/proof/raw/runtime_manifest.json"

SHARD_COUNT_RAW="${TELOS_ITER204_SHARD_COUNT-8}"
SHARD_INDEX_RAW="${TELOS_ITER204_SHARD_INDEX-}"
CERT_TIMEOUT_SECONDS=900
SCENARIO_TIMEOUT_SECONDS=180
KILL_GRACE_SECONDS=10
CERT_OUTPUT_LIMIT_BYTES=2097152
SCENARIO_OUTPUT_LIMIT_BYTES=262144
LAUNCH_DIAGNOSTIC_LIMIT_BYTES=2162688

if [[ ! "$SHARD_INDEX_RAW" =~ ^[0-7]$ ]] || [ "$SHARD_COUNT_RAW" != "8" ]; then
  echo "iter204 requires exact shard index 0..7 and shard count 8" >&2
  exit 2
fi
SHARD_INDEX=$((10#$SHARD_INDEX_RAW))
SHARD_COUNT=8

# This stage is mechanical and must not inherit or use provider credentials.
unset OPENAI_API_KEY ANTHROPIC_API_KEY
unset PYTHONHOME PYTHONINSPECT PYTHONPATH PYTHONSTARTUP PYTHONUSERBASE

if [ "${GITHUB_RUN_ATTEMPT-}" != "1" ]; then
  echo "iter204 accepts canonical workflow attempt 1 only" >&2
  exit 2
fi
python3 -I -S scripts/build_iter203_safety_recovery.py --check || exit 2
python3 -I -S scripts/build_iter203_runtime_manifest.py --check || exit 2
python3 -I -S scripts/build_iter204_runtime_manifest.py --check || exit 2
python3 -I -S scripts/collect_iter204_execution.py smoke-check \
  --receipt "${TELOS_ITER204_SMOKE_RECEIPT-}" \
  --runtime-manifest "$RUNTIME_MANIFEST" || exit 2

python3 -I -S scripts/prepare_iter204_output_directory.py \
  --path "$OUTDIR" --empty || exit 2
python3 -I -S scripts/prepare_iter204_output_directory.py \
  --path "$DIAGDIR" --empty || exit 2
RUNTIME_HOST_RECEIPT="$DIAGDIR/shard-${SHARD_INDEX}.runtime-host.json"
python3 -I -S scripts/capture_iter204_runtime_host.py --write "$RUNTIME_HOST_RECEIPT" || exit 2
export TELOS_ITER204_RUNTIME_HOST_RECEIPT="$RUNTIME_HOST_RECEIPT"

if ! plan="$({
  python3 -I -S scripts/collect_iter204_execution.py source-lines \
    --spec-index "$SPECS/index.json" \
    --runtime-manifest "$RUNTIME_MANIFEST"
})"; then
  echo "iter204 execution source preflight failed" >&2
  exit 2
fi

ALL_LINES=()
while IFS= read -r line; do
  [ -n "$line" ] && ALL_LINES+=("$line")
done <<< "$plan"
if [ "${#ALL_LINES[@]}" -ne 50 ]; then
  echo "iter204 execution requires exactly 50 preflight rows" >&2
  exit 2
fi

LINES=()
for ordinal in "${!ALL_LINES[@]}"; do
  if (( ordinal % SHARD_COUNT == SHARD_INDEX )); then
    LINES+=("${ALL_LINES[$ordinal]}")
  fi
done
if [ "${#LINES[@]}" -gt 7 ]; then
  echo "iter204 shard exceeds the frozen seven-row ceiling" >&2
  exit 2
fi
echo "=== iter204 shard $SHARD_INDEX/8 selected ${#LINES[@]}/50 valid patches ==="

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
  --log-opt compress=false
)

argv_sha256() {
  python3 -I -S - "$@" <<'PY'
import hashlib
import sys
digest = hashlib.sha256()
for value in sys.argv[1:]:
    digest.update(value.encode())
    digest.update(b"\0")
print(digest.hexdigest())
PY
}

retain_launch_diagnostic() {
  local source="$1" destination="$2" phase="$3" row_id="$4" image_ref="$5" image_id="$6" exit_code="$7" argv_digest="$8"
  local metadata="${destination%.log}.receipt.json"
  python3 -I -S scripts/publish_iter204_runtime_diagnostic.py \
    --source "$source" \
    --destination "$destination" \
    --metadata-destination "$metadata" \
    --limit "$LAUNCH_DIAGNOSTIC_LIMIT_BYTES" \
    --phase "$phase" \
    --row-id "$row_id" \
    --image-ref "$image_ref" \
    --image-id "$image_id" \
    --shard-index "$SHARD_INDEX" \
    --exit-code "$exit_code" \
    --argv-sha256 "$argv_digest" \
    --runtime-manifest "$RUNTIME_MANIFEST" \
    --runtime-host-receipt "$RUNTIME_HOST_RECEIPT"
}

row_create_preflight() {
  local stem="$1" image_ref="$2" image_id="$3" iid="$4"
  local output="$DIAGDIR/$stem.row-create.work"
  local destination="$DIAGDIR/$stem.row-create.diagnostic.log"
  local cidfile="$DIAGDIR/$stem.row-create.cid"
  local -a create_args=(
    create
    "${DOCKER_SAFETY_ARGS[@]}"
    --cidfile "$cidfile"
    -v "$PWD/$SPECS/$stem.eval_script.sh:/specs/$stem.eval_script.sh:ro"
    -v "$PWD/$SPECS/$stem.spec.json:/specs/$stem.spec.json:ro"
    -v "$PWD/$SOLS/$stem.model.patch:/solutions/$stem.model.patch:ro"
    --entrypoint bash
    "$image_ref"
    --noprofile --norc -c "exit 0"
  )
  local argv_digest
  argv_digest="$(argv_sha256 docker "${create_args[@]}")" || return 2
  local create_rc=0
  (
    ulimit -f "$((LAUNCH_DIAGNOSTIC_LIMIT_BYTES / 1024))"
    docker "${create_args[@]}" > "$output" 2>&1
  ) || create_rc=$?
  local cid=""
  if [ -f "$cidfile" ]; then
    cid="$(tr -d '\r\n' < "$cidfile")"
  fi
  rm -f "$cidfile"
  local remove_rc=0
  if [ -n "$cid" ]; then
    docker rm "$cid" >/dev/null 2>&1 || remove_rc=$?
  fi
  if ! retain_launch_diagnostic \
    "$output" "$destination" "row_container_create" "$iid" "$image_ref" "$image_id" \
    "$create_rc" "$argv_digest"; then
    echo "$iid ROW_CREATE_DIAGNOSTIC_FAIL" >&2
    return 2
  fi
  if [ "$create_rc" -ne 0 ] || [ "$remove_rc" -ne 0 ] \
    || [[ ! "$cid" =~ ^[0-9a-f]{64}$ ]]; then
    echo "$iid ROW_CREATE_PREFLIGHT_FAIL create=$create_rc remove=$remove_rc" >&2
    return 1
  fi
  return 0
}

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

LAST_LAUNCH_ARGV_SHA256=""
run_container() {
  local mode="$1" stem="$2" image_ref="$3" image_id="$4" repo_digest="$5" output="$6"
  local patch_name="model"
  local log_kind="variant"
  [ "$mode" = "gold-behavior" ] && patch_name="gold" && log_kind="gold"
  local scenario_mount=()
  if [ "$mode" = "variant-behavior" ] || [ "$mode" = "gold-behavior" ]; then
    scenario_mount=(-v "$PWD/$SCEN/$stem.scenario.py:/scenario/scenario.py:ro")
  fi
  local container_program
  IFS= read -r -d '' container_program <<'CONTAINER_PROGRAM' || true
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
CONTAINER_PROGRAM
  local -a run_args=(
    run --rm
    "${DOCKER_SAFETY_ARGS[@]}"
    -e STEM="$stem"
    -e PATCH_NAME="$patch_name"
    -e LOG_KIND="$log_kind"
    -e EXECUTION_MODE="$mode"
    -e TELOS_IMAGE_ID="$image_id"
    -e TELOS_IMAGE_REPO_DIGEST="$repo_digest"
    -e CERT_TIMEOUT_SECONDS="$CERT_TIMEOUT_SECONDS"
    -e SCENARIO_TIMEOUT_SECONDS="$SCENARIO_TIMEOUT_SECONDS"
    -e KILL_GRACE_SECONDS="$KILL_GRACE_SECONDS"
    -e CERT_OUTPUT_LIMIT_BYTES="$CERT_OUTPUT_LIMIT_BYTES"
    -e SCENARIO_OUTPUT_LIMIT_BYTES="$SCENARIO_OUTPUT_LIMIT_BYTES"
    -v "$PWD/$SPECS/$stem.eval_script.sh:/specs/$stem.eval_script.sh:ro"
    -v "$PWD/$SPECS/$stem.spec.json:/specs/$stem.spec.json:ro"
    -v "$PWD/$SOLS/$stem.$patch_name.patch:/solutions/$stem.$patch_name.patch:ro"
    "${scenario_mount[@]}"
    "$image_ref" bash -lc "$container_program"
  )
  LAST_LAUNCH_ARGV_SHA256="$(argv_sha256 docker "${run_args[@]}")" || return 2
  (
    ulimit -f "$((LAUNCH_DIAGNOSTIC_LIMIT_BYTES / 1024))"
    docker "${run_args[@]}" > "$output" 2>&1
  )
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

  if ! row_create_preflight "$stem" "$image_ref" "$image_id" "$iid"; then
    failures=$((failures + 1))
    docker rmi "$image_ref" >/dev/null 2>&1 || true
    continue
  fi

  variant_tmp="$(mktemp "$DIAGDIR/${stem}.variant-cert.XXXXXX.work")"
  gold_tmp="$(mktemp "$DIAGDIR/${stem}.gold-behavior.XXXXXX.work")"
  behavior_tmp=""
  variant_rc=0
  gold_rc=0
  run_container variant-cert "$stem" "$image_ref" "$image_id" "$image_ref" "$variant_tmp" || variant_rc=$?
  variant_cert_argv="$LAST_LAUNCH_ARGV_SHA256"
  if [ "$variant_rc" -ne 0 ]; then
    echo "$iid CERTIFICATION_INFRA_FAIL exit=$variant_rc" >&2
    if ! retain_launch_diagnostic \
      "$variant_tmp" "$DIAGDIR/$stem.variant-cert.diagnostic.log" \
      "scientific_container_launch_variant_cert" "$iid" "$image_ref" "$image_id" \
      "$variant_rc" "$variant_cert_argv"; then
      echo "$iid CERTIFICATION_DIAGNOSTIC_PUBLICATION_FAIL" >&2
    fi
    rm -f "$gold_tmp"
    failures=$((failures + 1))
    docker rmi "$image_ref" >/dev/null 2>&1 || true
    continue
  fi
  if [ "$behavior" = "safe_scenario" ]; then
    behavior_tmp="$(mktemp "$DIAGDIR/${stem}.variant-behavior.XXXXXX.work")"
    run_container variant-behavior "$stem" "$image_ref" "$image_id" "$image_ref" "$behavior_tmp" || variant_rc=$?
    variant_behavior_argv="$LAST_LAUNCH_ARGV_SHA256"
    if [ "$variant_rc" -eq 0 ]; then
      if ! cat "$behavior_tmp" >> "$variant_tmp"; then
        variant_rc=30
      fi
      rm -f "$behavior_tmp"
    else
      if ! retain_launch_diagnostic \
        "$behavior_tmp" "$DIAGDIR/$stem.variant-behavior.diagnostic.log" \
        "scientific_container_launch_variant_behavior" "$iid" "$image_ref" "$image_id" \
        "$variant_rc" "$variant_behavior_argv"; then
        echo "$iid VARIANT_BEHAVIOR_DIAGNOSTIC_PUBLICATION_FAIL" >&2
      fi
    fi
    run_container gold-behavior "$stem" "$image_ref" "$image_id" "$image_ref" "$gold_tmp" || gold_rc=$?
    gold_behavior_argv="$LAST_LAUNCH_ARGV_SHA256"
    if [ "$gold_rc" -ne 0 ]; then
      if ! retain_launch_diagnostic \
        "$gold_tmp" "$DIAGDIR/$stem.gold-behavior.diagnostic.log" \
        "scientific_container_launch_gold_behavior" "$iid" "$image_ref" "$image_id" \
        "$gold_rc" "$gold_behavior_argv"; then
        echo "$iid GOLD_BEHAVIOR_DIAGNOSTIC_PUBLICATION_FAIL" >&2
      fi
    fi
  else
    printf 'SCENARIO_NOT_EXECUTED disposition=no_safe_scenario\n' >> "$variant_tmp"
    printf 'IMAGE_ID=%s\nIMAGE_REPO_DIGEST=%s\nSCENARIO_NOT_EXECUTED disposition=no_safe_scenario\n' \
      "$image_id" "$image_ref" > "$gold_tmp"
  fi
  if [ "$variant_rc" -ne 0 ] || [ "$gold_rc" -ne 0 ] \
    || ! variant_complete "$variant_tmp" "$behavior" \
    || ! gold_complete "$gold_tmp" "$behavior"; then
    echo "$iid INCOMPLETE_EXECUTION_EVIDENCE variant=$variant_rc gold=$gold_rc" >&2
    if [ -f "$variant_tmp" ]; then
      if ! retain_launch_diagnostic \
        "$variant_tmp" "$DIAGDIR/$stem.incomplete-variant.diagnostic.log" \
        "incomplete_scientific_variant_evidence" "$iid" "$image_ref" "$image_id" \
        "$variant_rc" "$variant_cert_argv"; then
        echo "$iid INCOMPLETE_VARIANT_DIAGNOSTIC_PUBLICATION_FAIL" >&2
      fi
    fi
    if [ -f "$gold_tmp" ]; then
      if ! retain_launch_diagnostic \
        "$gold_tmp" "$DIAGDIR/$stem.incomplete-gold.diagnostic.log" \
        "incomplete_scientific_gold_evidence" "$iid" "$image_ref" "$image_id" \
        "$gold_rc" "${gold_behavior_argv-$variant_cert_argv}"; then
        echo "$iid INCOMPLETE_GOLD_DIAGNOSTIC_PUBLICATION_FAIL" >&2
      fi
    fi
    failures=$((failures + 1))
  else
    python3 -I -S scripts/collect_iter204_execution.py publish-log \
      --source "$variant_tmp" --destination "$OUTDIR/$stem.variant.log" || failures=$((failures + 1))
    python3 -I -S scripts/collect_iter204_execution.py publish-log \
      --source "$gold_tmp" --destination "$OUTDIR/$stem.gold.log" || failures=$((failures + 1))
  fi
  docker rmi "$image_ref" >/dev/null 2>&1 || true
done

if [ "$failures" -ne 0 ]; then
  echo "iter204 execution failed closed: $failures evidence error(s)" >&2
  exit 1
fi

python3 -I -S scripts/collect_iter204_execution.py shard-receipt \
  --execution-dir "$OUTDIR" \
  --spec-index "$SPECS/index.json" \
  --runtime-manifest "$RUNTIME_MANIFEST" \
  --shard-index "$SHARD_INDEX" \
  --shard-count "$SHARD_COUNT" || exit 2

echo "=== iter204 shard $SHARD_INDEX/8 complete: ${#LINES[@]} valid patches ==="
