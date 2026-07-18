#!/usr/bin/env bash
# Iter231 gold-free execution oracle: apply each certified candidate patch in its pinned SWE-bench
# image and run the committed gold-free exercise against it, capturing the exercise's RESULT= line.
#
# This is deliberately NOT ci_iter200_execute.sh. That runner is bound to the certify +
# gold-differential schema: it needs an eval_script, a gold patch, and a scenario, and it runs the
# graded suite. Iter231 must never see a gold patch, a hidden test, or the gold-differential witness
# (a pre-registered falsifier), and it has no eval_script stage at all. The only inputs mounted into
# the container are the candidate patch and the exercise.
#
# An exercise that crashes is a MEASUREMENT, not an infrastructure failure: a non-zero exercise exit
# is exactly the signal the oracle is built to observe. Missing/apply/setup/absent-RESULT evidence is
# an infrastructure failure and makes the job fail after all rows have been attempted.
set -uo pipefail

ITER231_EXP="iter231_gold_free_execution_oracle"
ITER230_EXP="iter230_gold_free_detector_natural"
EVAL_SET="experiments/${ITER230_EXP}/proof/raw/eval_set.json"
EXDIR="experiments/${ITER231_EXP}/proof/raw/exercises"
OUTDIR="experiments/${ITER231_EXP}/proof/raw/execution"
SKIP_EXISTING="${TELOS_ITER231_SKIP_EXISTING:-0}"

# The frozen iter230 benchmark. Acceptance bar 1: this sha may not change.
FROZEN_EVAL_SET_SHA256="10dc898c3cdc6026aaedc57d469e546b279a982df3772ba3388c1dfb515b8928"

ITER231_APPLY_TIMEOUT_SECONDS=120
ITER231_EXERCISE_TIMEOUT_SECONDS=180
ITER231_KILL_GRACE_SECONDS=10
ITER231_EXERCISE_OUTPUT_LIMIT_BYTES=262144
# Wall-clock ceiling for one row, generously above pull + apply + exercise. A row that exceeds this
# is the reproducible-container-hang mode that cost ~4 hours on sympy-19040; it is bounded here and
# reported by the straggler monitor rather than being allowed to stall the shard.
ITER231_ROW_CEILING_SECONDS=1200

validate_shard_config() {
  local index="$1" count="$2"
  [[ "$index" =~ ^(0|[1-9][0-9]{0,2})$ ]] || return 1
  [[ "$count" =~ ^[1-9][0-9]{0,2}$ ]] || return 1
  local index_value=$((10#$index)) count_value=$((10#$count))
  (( count_value >= 1 && count_value <= 256 && index_value < count_value ))
}

shard_member() {
  local ordinal="$1"
  (( ordinal % SHARD_COUNT == SHARD_INDEX ))
}

SHARD_INDEX_RAW="${TELOS_ITER231_SHARD_INDEX-0}"
SHARD_COUNT_RAW="${TELOS_ITER231_SHARD_COUNT-1}"
if ! validate_shard_config "$SHARD_INDEX_RAW" "$SHARD_COUNT_RAW"; then
  echo "invalid shard config: index=$SHARD_INDEX_RAW count=$SHARD_COUNT_RAW" >&2
  exit 2
fi
SHARD_INDEX=$((10#$SHARD_INDEX_RAW))
SHARD_COUNT=$((10#$SHARD_COUNT_RAW))
mkdir -p "$OUTDIR"

# The safety instrument gates execution: an excluded_unsafe exercise is never committed and never
# run (a pre-registered falsifier). This is defense in depth on top of the container boundary.
python3 scripts/validate_iter231_execution_safety.py || exit 2

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
  # The local driver compresses rotated files by default, which Docker rejects at max-file=1
  # ("compression cannot be enabled when max file count is 1"). Observed live: every row failed
  # docker-run exit 125 before the container started.
  --log-opt compress=false
)

if ! row_output="$(python3 - "$EVAL_SET" "$EXDIR" "$FROZEN_EVAL_SET_SHA256" <<'PY'
import hashlib
import json
import re
import sys
from pathlib import Path

eval_path = Path(sys.argv[1])
exercise_dir = Path(sys.argv[2])
frozen_sha = sys.argv[3]

raw = eval_path.read_bytes()
if hashlib.sha256(raw).hexdigest() != frozen_sha:
    raise SystemExit("frozen iter230 benchmark sha changed; iter231 may not proceed")
data = json.loads(raw)
if data.get("schema_version") != "telos.iter230.natural_detector_eval.v1":
    raise SystemExit("eval set schema mismatch")
positives = data["positives"]
negatives = data["negatives"]
if data.get("positive_count") != len(positives) or len(positives) != 13:
    raise SystemExit("benchmark positive denominator is not the frozen 13")
if data.get("negative_count") != len(negatives) or len(negatives) != 54:
    raise SystemExit("benchmark negative denominator is not the frozen 54")

items = [dict(row, label="certified_yet_wrong") for row in positives]
items += [dict(row, label="certified_correct") for row in negatives]

summary = json.loads((exercise_dir / "exercises_summary.json").read_text())
if summary.get("schema_version") != "telos.iter231.exercises_summary.v1":
    raise SystemExit("exercises summary schema mismatch")
manifest = summary["manifest"]
if len(manifest) != len(items):
    raise SystemExit("exercise manifest does not cover the benchmark denominator")
by_key = {}
for row in manifest:
    key = (row["run"], row["instance_id"])
    if key in by_key:
        raise SystemExit(f"exercise manifest duplicates {key}")
    by_key[key] = row

# Ordinals run over the COMPLETE ordered 67-row benchmark, not over the executable subset, so every
# row -- including excluded_unsafe, no_exercise, and provider_error -- belongs to exactly one shard
# and is written out. The denominator is structurally complete; nothing is silently dropped. This is
# the corrected-denominator lesson from iter200 applied at the executor.
for ordinal, item in enumerate(items):
    iid = item["instance_id"]
    run = item["run"]
    if not re.fullmatch(r"[A-Za-z0-9_.-]+__[A-Za-z0-9_.-]+", iid):
        raise SystemExit(f"unsafe instance id: {iid!r}")
    if not re.fullmatch(r"[A-Za-z0-9_]+", run):
        raise SystemExit(f"unsafe run id: {run!r}")
    row = by_key.get((run, iid))
    if row is None:
        raise SystemExit(f"benchmark row has no exercise manifest entry: {run}/{iid}")
    if row.get("label") != item["label"]:
        raise SystemExit(f"exercise manifest label disagrees with benchmark for {iid}")
    stem = f"{run}__{iid.replace('/', '__')}"
    status = row["status"]

    if status != "exercise":
        # Non-executable by construction; recorded, never executed.
        print("\t".join([str(ordinal), stem, iid, status, "", "", ""]))
        continue

    patch_path = Path(item["model_patch_path"])
    if not patch_path.is_file():
        raise SystemExit(f"missing candidate patch: {patch_path}")
    patch_raw = patch_path.read_bytes()
    payload = patch_raw[:-1] if patch_raw.endswith(b"\n") else patch_raw
    if hashlib.sha256(payload).hexdigest() != item["model_patch_sha256"]:
        raise SystemExit(f"candidate patch hash mismatch for {iid}")

    exercise_path = exercise_dir / f"{stem}.exercise.py"
    if not exercise_path.is_file():
        raise SystemExit(f"missing committed exercise: {exercise_path}")
    ex_raw = exercise_path.read_bytes()
    ex_payload = ex_raw[:-1] if ex_raw.endswith(b"\n") else ex_raw
    if hashlib.sha256(ex_payload).hexdigest() != row["exercise_sha256"]:
        raise SystemExit(f"exercise hash mismatch for {stem}")

    image = "swebench/sweb.eval.x86_64." + re.sub("__", "_1776_", iid.lower()) + ":latest"
    print("\t".join([str(ordinal), stem, iid, status, image, str(patch_path), item["label"]]))
PY
)"; then
  echo "iter231 preflight failed closed" >&2
  exit 2
fi

ORDINALS=(); STEMS=(); IIDS=(); STATUSES=(); IMAGES=(); PATCHES=(); LABELS=()
while IFS=$'\t' read -r ordinal stem iid status image patch label; do
  [ -n "$ordinal" ] || continue
  if shard_member "$ordinal"; then
    ORDINALS+=("$ordinal"); STEMS+=("$stem"); IIDS+=("$iid"); STATUSES+=("$status")
    IMAGES+=("$image"); PATCHES+=("$patch"); LABELS+=("$label")
  fi
done <<< "$row_output"

echo "=== iter231 oracle shard $SHARD_INDEX/$SHARD_COUNT selected ${#STEMS[@]} of 67 benchmark rows ==="

# One committed observation per row. A row is complete when it carries its image provenance, its
# apply marker, a bounded exercise section, an explicit exit code, and exactly one RESULT= line.
row_complete() {
  local stem="$1" status="$2"
  local file="$OUTDIR/$stem.oracle.log"
  [ -f "$file" ] || return 1
  if [ "$status" != "exercise" ]; then
    [ "$(grep -E -c "^NOT_EXECUTED status=$status\$" "$file" 2>/dev/null)" -eq 1 ] || return 1
    return 0
  fi
  [ "$(grep -E -c '^IMAGE_ID=sha256:[0-9a-f]{64}$' "$file" 2>/dev/null)" -eq 1 ] || return 1
  [ "$(grep -E -c '^IMAGE_REPO_DIGEST=(UNAVAILABLE|[^[:space:]@]+@sha256:[0-9a-f]{64})$' "$file" 2>/dev/null)" -eq 1 ] || return 1
  [ "$(grep -F -x -c "APPLY_OK candidate" "$file" 2>/dev/null)" -eq 1 ] || return 1
  ! grep -E -q '^(APPLY_FAIL|SETUP_FAIL)' "$file" || return 1
  [ "$(grep -F -x -c ">>>>> Exercise Start" "$file" 2>/dev/null)" -eq 1 ] || return 1
  [ "$(grep -F -x -c ">>>>> Exercise End" "$file" 2>/dev/null)" -eq 1 ] || return 1
  [ "$(grep -E -c '^EXERCISE_EXIT=[0-9]+$' "$file" 2>/dev/null)" -eq 1 ] || return 1
  # Exactly one RESULT= observable. Zero means the exercise produced nothing to adjudicate, which is
  # an evidence failure, not a null observation.
  [ "$(grep -E -c '^RESULT=' "$file" 2>/dev/null)" -eq 1 ] || return 1
}

PROGRESS="$OUTDIR/_shard-$SHARD_INDEX-of-$SHARD_COUNT.progress.json"
write_progress() {
  local phase="$1" stem="$2" done_count="$3"
  printf '{"schema_version":"telos.iter231.shard_progress.v1","shard_index":%d,"shard_count":%d,"rows":%d,"completed":%d,"phase":"%s","current":"%s","updated_epoch":%d}\n' \
    "$SHARD_INDEX" "$SHARD_COUNT" "${#STEMS[@]}" "$done_count" "$phase" "$stem" "$(date -u +%s)" > "$PROGRESS"
}
write_progress "start" "" 0

failures=0
completed=0
for idx in "${!STEMS[@]}"; do
  stem="${STEMS[$idx]}"
  iid="${IIDS[$idx]}"
  status="${STATUSES[$idx]}"
  log="$OUTDIR/$stem.oracle.log"

  if [ "$SKIP_EXISTING" = "1" ] && row_complete "$stem" "$status"; then
    echo "=== $stem (complete committed observation retained) ==="
    completed=$((completed + 1))
    write_progress "retained" "$stem" "$completed"
    continue
  fi

  if [ "$status" != "exercise" ]; then
    # Reported, not dropped: the pre-registration requires every excluded_unsafe / no_exercise /
    # provider_error row to appear in the result.
    printf 'NOT_EXECUTED status=%s\n' "$status" > "$log"
    echo "=== $stem (not executed: $status) ==="
    completed=$((completed + 1))
    write_progress "not_executed" "$stem" "$completed"
    continue
  fi

  image="${IMAGES[$idx]}"
  patch="${PATCHES[$idx]}"
  row_start="$(date -u +%s)"
  write_progress "running" "$stem" "$completed"
  echo "=== $stem ($image) ==="
  echo "ROW_START stem=$stem epoch=$row_start"

  if ! timeout --signal=TERM --kill-after=60s 900s docker pull "$image" >/dev/null 2>&1; then
    echo "$stem PULL_FAIL" >&2
    failures=$((failures + 1))
    write_progress "pull_fail" "$stem" "$completed"
    continue
  fi
  image_id="$(docker image inspect --format '{{.Id}}' "$image" 2>/dev/null)"
  repo_digest="$(docker image inspect --format '{{if .RepoDigests}}{{index .RepoDigests 0}}{{end}}' "$image" 2>/dev/null)"
  [ -n "$repo_digest" ] || repo_digest="UNAVAILABLE"
  if [[ ! "$image_id" =~ ^sha256:[0-9a-f]{64}$ ]] \
    || [[ ! "$repo_digest" =~ ^(UNAVAILABLE|[^[:space:]@]+@sha256:[0-9a-f]{64})$ ]]; then
    echo "$stem IMAGE_PROVENANCE_INSPECTION_FAIL" >&2
    failures=$((failures + 1))
    docker rmi "$image" >/dev/null 2>&1 || true
    write_progress "provenance_fail" "$stem" "$completed"
    continue
  fi

  # Outer wall-clock ceiling. The inner `timeout` bounds the exercise; this bounds the whole
  # container, including a Docker-level hang that the inner timeout can never reach.
  row_rc=0
  timeout --signal=TERM --kill-after=60s "${ITER231_ROW_CEILING_SECONDS}s" \
    docker run --rm \
    "${DOCKER_SAFETY_ARGS[@]}" \
    -e STEM="$stem" \
    -e TELOS_IMAGE_ID="$image_id" \
    -e TELOS_IMAGE_REPO_DIGEST="$repo_digest" \
    -e TELOS_APPLY_TIMEOUT_SECONDS="$ITER231_APPLY_TIMEOUT_SECONDS" \
    -e TELOS_EXERCISE_TIMEOUT_SECONDS="$ITER231_EXERCISE_TIMEOUT_SECONDS" \
    -e TELOS_KILL_GRACE_SECONDS="$ITER231_KILL_GRACE_SECONDS" \
    -e TELOS_EXERCISE_OUTPUT_LIMIT_BYTES="$ITER231_EXERCISE_OUTPUT_LIMIT_BYTES" \
    -e TELOS_TIMEOUT_RESULT_LINE="RESULT=('TIMEOUT', $ITER231_EXERCISE_TIMEOUT_SECONDS)" \
    -v "$PWD/$patch:/telos/candidate.patch:ro" \
    -v "$PWD/$EXDIR/$stem.exercise.py:/telos/exercise.py:ro" \
    "$image" bash -lc '
set -uo pipefail
echo "IMAGE_ID=${TELOS_IMAGE_ID}"
echo "IMAGE_REPO_DIGEST=${TELOS_IMAGE_REPO_DIGEST}"
source /opt/miniconda3/bin/activate >/dev/null 2>&1 || { echo "SETUP_FAIL conda_source"; exit 20; }
conda activate testbed >/dev/null 2>&1 || { echo "SETUP_FAIL conda_activate"; exit 21; }
cd /testbed || { echo "SETUP_FAIL testbed_cd"; exit 22; }
git config --global --add safe.directory /testbed >/dev/null 2>&1 || { echo "SETUP_FAIL git_config"; exit 23; }
git checkout -- . >/dev/null 2>&1 || { echo "SETUP_FAIL git_checkout"; exit 24; }
git clean -fdq >/dev/null 2>&1 || { echo "SETUP_FAIL git_clean"; exit 25; }
if timeout --signal=TERM --kill-after="${TELOS_KILL_GRACE_SECONDS}s" \
  "${TELOS_APPLY_TIMEOUT_SECONDS}s" git apply -v /telos/candidate.patch >/dev/null 2>&1; then
  echo "APPLY_OK candidate"
else
  echo "APPLY_FAIL candidate"
  exit 26
fi
echo ">>>>> Exercise Start"
timeout --signal=TERM --kill-after="${TELOS_KILL_GRACE_SECONDS}s" \
  "${TELOS_EXERCISE_TIMEOUT_SECONDS}s" python /telos/exercise.py 2>&1 | python -c "
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
" "$TELOS_EXERCISE_OUTPUT_LIMIT_BYTES"
exercise_status=("${PIPESTATUS[@]}")
exercise_rc="${exercise_status[0]}"
if [ "${exercise_status[1]}" -eq 3 ]; then
  echo "TELOS_OUTPUT_LIMIT limit_bytes=${TELOS_EXERCISE_OUTPUT_LIMIT_BYTES}"
elif [ "${exercise_status[1]}" -ne 0 ]; then
  echo "SETUP_FAIL output_limiter exit=${exercise_status[1]}"
fi
# A timed-out exercise is a measurement outcome (the patched code hung), recorded as an explicit
# RESULT= so the adjudicator sees an observation rather than a hole.
if [ "$exercise_rc" -eq 124 ] || [ "$exercise_rc" -eq 137 ]; then
  echo "$TELOS_TIMEOUT_RESULT_LINE"
fi
echo "EXERCISE_EXIT=${exercise_rc}"
echo ">>>>> Exercise End"
exit 0
' > "$log" 2>&1 || row_rc=$?

  row_end="$(date -u +%s)"
  echo "ROW_END stem=$stem epoch=$row_end elapsed=$((row_end - row_start))"

  if [ "$row_rc" -eq 125 ]; then
    # Docker exit 125 is the daemon refusing to start the container -- a malformed flag set, not a
    # failing row. It is identical for every row, so grinding through the rest wastes the shard and
    # buries the cause under a pile of duplicate evidence errors. Abort loudly on the first one.
    echo "$stem CONTAINER_FLAGS_REJECTED exit=125" >&2
    echo "docker refused to start the container; the safety flag set is invalid on this daemon:" >&2
    head -3 "$log" >&2
    write_progress "flags_rejected" "$stem" "$completed"
    exit 2
  fi
  if [ "$row_rc" -eq 124 ] || [ "$row_rc" -eq 137 ]; then
    # The reproducible container-hang mode, bounded rather than allowed to stall the shard.
    echo "$stem ROW_CEILING_EXCEEDED seconds=$ITER231_ROW_CEILING_SECONDS" >&2
    printf 'ROW_CEILING_EXCEEDED seconds=%s\n' "$ITER231_ROW_CEILING_SECONDS" >> "$log"
  elif [ "$row_rc" -ne 0 ]; then
    echo "$stem ROW_INFRA_FAIL exit=$row_rc" >&2
  fi

  if ! row_complete "$stem" "$status"; then
    echo "$stem INCOMPLETE_ORACLE_EVIDENCE" >&2
    failures=$((failures + 1))
  else
    completed=$((completed + 1))
  fi
  echo "  observed: $(grep -m1 '^RESULT=' "$log" 2>/dev/null || echo none)"
  docker rmi "$image" >/dev/null 2>&1 || true
  write_progress "row_done" "$stem" "$completed"
done

# Reconcile every selected row, including retained ones, before allowing a green shard.
for idx in "${!STEMS[@]}"; do
  if ! row_complete "${STEMS[$idx]}" "${STATUSES[$idx]}"; then
    echo "${STEMS[$idx]} FINAL_EVIDENCE_MISSING_OR_INCOMPLETE" >&2
    failures=$((failures + 1))
  fi
done

write_progress "finished" "" "$completed"
if [ "$failures" -ne 0 ]; then
  echo "iter231 oracle execution failed closed: $failures evidence error(s)" >&2
  exit 1
fi
echo "=== iter231 oracle observations complete for shard $SHARD_INDEX/$SHARD_COUNT: ${#STEMS[@]} rows ==="
