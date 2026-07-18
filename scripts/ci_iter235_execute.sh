#!/usr/bin/env bash
# Iter235: run each recovered gold-differential witness against BOTH the gold patch and the candidate
# patch, in one container pass per row.
#
# THE PAIRED ARM IS THE POINT. These rows were certified long ago and lost because their witness never
# produced a usable observable. The committed logs show why: AttributeError and TypeError, occurring
# SYMMETRICALLY on both arms, which means the script was broken rather than the implementations differing.
# The original prompt already demanded the witness "run to completion under GOLD without raising" and
# nothing enforced it. A witness that fails on gold is provably wrong, because gold is the correct fix.
#
# Gold is mounted deliberately. A gold-differential witness is the ground-truth labelling instrument, not a
# detector, and it has always seen gold. The gold-free detectors of iter230-iter234 never see a witness.
set -uo pipefail

ITER235_EXP="iter235_witness_recovery"
WITDIR="experiments/${ITER235_EXP}/proof/raw/witnesses"
OUTDIR="experiments/${ITER235_EXP}/proof/raw/execution"

ITER235_APPLY_TIMEOUT_SECONDS=120
ITER235_WITNESS_TIMEOUT_SECONDS=180
ITER235_KILL_GRACE_SECONDS=10
ITER235_OUTPUT_LIMIT_BYTES=262144
ITER235_ROW_CEILING_SECONDS=2400

validate_shard_config() {
  local index="$1" count="$2"
  [[ "$index" =~ ^(0|[1-9][0-9]{0,2})$ ]] || return 1
  [[ "$count" =~ ^[1-9][0-9]{0,2}$ ]] || return 1
  (( 10#$count >= 1 && 10#$count <= 256 && 10#$index < 10#$count ))
}

SHARD_INDEX_RAW="${TELOS_ITER235_SHARD_INDEX-0}"
SHARD_COUNT_RAW="${TELOS_ITER235_SHARD_COUNT-1}"
if ! validate_shard_config "$SHARD_INDEX_RAW" "$SHARD_COUNT_RAW"; then
  echo "invalid shard config: index=$SHARD_INDEX_RAW count=$SHARD_COUNT_RAW" >&2
  exit 2
fi
SHARD_INDEX=$((10#$SHARD_INDEX_RAW))
SHARD_COUNT=$((10#$SHARD_COUNT_RAW))
mkdir -p "$OUTDIR"

python3 scripts/validate_iter235_execution_safety.py || exit 2

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

if ! row_output="$(python3 - "$WITDIR" <<'PY'
import json
import re
import sys
from pathlib import Path

witness_dir = Path(sys.argv[1])
summary = json.loads((witness_dir / "witnesses_summary.json").read_text())
if summary.get("schema_version") != "telos.iter235.witnesses_summary.v1":
    raise SystemExit("witnesses summary schema mismatch")

rows = [r for r in summary["manifest"] if r["status"] == "witness"]
if not rows:
    raise SystemExit("no recovered witnesses to execute")
for ordinal, row in enumerate(rows):
    iid, run = row["instance_id"], row["run"]
    if not re.fullmatch(r"[A-Za-z0-9_.-]+__[A-Za-z0-9_.-]+", iid):
        raise SystemExit(f"unsafe instance id: {iid!r}")
    if not re.fullmatch(r"[A-Za-z0-9_]+", run):
        raise SystemExit(f"unsafe run id: {run!r}")
    stem = f"{run}__{iid.replace('/', '__')}"
    solutions = f"experiments/{run}/proof/raw/solutions"
    image = "swebench/sweb.eval.x86_64." + re.sub("__", "_1776_", iid.lower()) + ":latest"
    print("\t".join([
        str(ordinal), stem, image,
        f"{solutions}/{iid}.model.patch", f"{solutions}/{iid}.gold.patch",
    ]))
PY
)"; then
  echo "iter235 preflight failed closed" >&2
  exit 2
fi

STEMS=(); IMAGES=(); CANDS=(); GOLDS=()
while IFS=$'\t' read -r o s img c g; do
  [ -n "$o" ] || continue
  if (( o % SHARD_COUNT == SHARD_INDEX )); then
    STEMS+=("$s"); IMAGES+=("$img"); CANDS+=("$c"); GOLDS+=("$g")
  fi
done <<< "$row_output"
echo "=== iter235 shard $SHARD_INDEX/$SHARD_COUNT selected ${#STEMS[@]} recovered witnesses ==="

row_complete() {
  local stem="$1"
  local file="$OUTDIR/$stem.witness.log"
  [ -f "$file" ] || return 1
  [ "$(grep -E -c '^IMAGE_ID=sha256:[0-9a-f]{64}$' "$file" 2>/dev/null)" -eq 1 ] || return 1
  [ "$(grep -F -x -c "APPLY_OK candidate" "$file" 2>/dev/null)" -eq 1 ] || return 1
  [ "$(grep -F -x -c "APPLY_OK gold" "$file" 2>/dev/null)" -eq 1 ] || return 1
  ! grep -E -q '^(APPLY_FAIL|SETUP_FAIL)' "$file" || return 1
  # Both arms must record an exit. Whether each produced a RESULT= is the MEASUREMENT, decided by the
  # adjudicator; a witness that legitimately errors on one arm is an outcome, not missing evidence.
  [ "$(grep -E -c '^EXIT candidate=[0-9]+$' "$file" 2>/dev/null)" -eq 1 ] || return 1
  [ "$(grep -E -c '^EXIT gold=[0-9]+$' "$file" 2>/dev/null)" -eq 1 ] || return 1
}

failures=0
for idx in "${!STEMS[@]}"; do
  stem="${STEMS[$idx]}"; image="${IMAGES[$idx]}"
  cand="${CANDS[$idx]}"; gold="${GOLDS[$idx]}"
  log="$OUTDIR/$stem.witness.log"
  echo "=== $stem ==="

  missing=0
  for required in "$cand" "$gold" "$WITDIR/$stem.witness.py"; do
    if [ ! -f "$required" ]; then
      echo "$stem MISSING_INPUT $required" >&2
      missing=1
    fi
  done
  if [ "$missing" -ne 0 ]; then
    failures=$((failures + 1))
    continue
  fi

  if ! timeout --signal=TERM --kill-after=60s 900s docker pull "$image" >/dev/null 2>&1; then
    echo "$stem PULL_FAIL" >&2; failures=$((failures + 1)); continue
  fi
  image_id="$(docker image inspect --format '{{.Id}}' "$image" 2>/dev/null)"
  if [[ ! "$image_id" =~ ^sha256:[0-9a-f]{64}$ ]]; then
    echo "$stem IMAGE_PROVENANCE_INSPECTION_FAIL" >&2; failures=$((failures + 1)); continue
  fi

  row_rc=0
  timeout --signal=TERM --kill-after=60s "${ITER235_ROW_CEILING_SECONDS}s" \
    docker run --rm "${DOCKER_SAFETY_ARGS[@]}" \
    -e TELOS_IMAGE_ID="$image_id" \
    -e TELOS_APPLY_TIMEOUT_SECONDS="$ITER235_APPLY_TIMEOUT_SECONDS" \
    -e TELOS_WITNESS_TIMEOUT_SECONDS="$ITER235_WITNESS_TIMEOUT_SECONDS" \
    -e TELOS_KILL_GRACE_SECONDS="$ITER235_KILL_GRACE_SECONDS" \
    -e TELOS_OUTPUT_LIMIT_BYTES="$ITER235_OUTPUT_LIMIT_BYTES" \
    -v "$PWD/$cand:/telos/candidate.patch:ro" \
    -v "$PWD/$gold:/telos/gold.patch:ro" \
    -v "$PWD/$WITDIR/$stem.witness.py:/telos/witness.py:ro" \
    "$image" bash -lc '
set -uo pipefail
echo "IMAGE_ID=${TELOS_IMAGE_ID}"
source /opt/miniconda3/bin/activate >/dev/null 2>&1 || { echo "SETUP_FAIL conda_source"; exit 20; }
conda activate testbed >/dev/null 2>&1 || { echo "SETUP_FAIL conda_activate"; exit 21; }
cd /testbed || { echo "SETUP_FAIL testbed_cd"; exit 22; }
git config --global --add safe.directory /testbed >/dev/null 2>&1 || { echo "SETUP_FAIL git_config"; exit 23; }

run_arm() {
  local arm="$1" patchfile="$2"
  git checkout -- . >/dev/null 2>&1 || { echo "SETUP_FAIL git_checkout"; return 24; }
  git clean -fdq >/dev/null 2>&1 || { echo "SETUP_FAIL git_clean"; return 25; }
  if timeout --signal=TERM --kill-after="${TELOS_KILL_GRACE_SECONDS}s" \
    "${TELOS_APPLY_TIMEOUT_SECONDS}s" git apply -v "$patchfile" >/dev/null 2>&1; then
    echo "APPLY_OK ${arm}"
  else
    echo "APPLY_FAIL ${arm}"
    return 26
  fi
  echo ">>>>> ${arm} Start"
  timeout --signal=TERM --kill-after="${TELOS_KILL_GRACE_SECONDS}s" \
    "${TELOS_WITNESS_TIMEOUT_SECONDS}s" python /telos/witness.py 2>&1 | head -c "$TELOS_OUTPUT_LIMIT_BYTES"
  local rc="${PIPESTATUS[0]}"
  if [ "$rc" -eq 124 ] || [ "$rc" -eq 137 ]; then
    echo "RESULT=('"'"'TIMEOUT'"'"', ${TELOS_WITNESS_TIMEOUT_SECONDS})"
  fi
  echo "EXIT ${arm}=${rc}"
  echo ">>>>> ${arm} End"
}
run_arm candidate /telos/candidate.patch || exit $?
run_arm gold /telos/gold.patch || exit $?
exit 0
' > "$log" 2>&1 || row_rc=$?

  if [ "$row_rc" -eq 125 ]; then
    echo "$stem CONTAINER_FLAGS_REJECTED" >&2; head -3 "$log" >&2; exit 2
  fi
  echo "  candidate: $(sed -n '/>>>>> candidate Start/,/>>>>> candidate End/p' "$log" | grep -m1 '^RESULT=' || echo none)"
  echo "  gold:      $(sed -n '/>>>>> gold Start/,/>>>>> gold End/p' "$log" | grep -m1 '^RESULT=' || echo none)"
  docker rmi "$image" >/dev/null 2>&1 || true
done

for idx in "${!STEMS[@]}"; do
  if ! row_complete "${STEMS[$idx]}"; then
    echo "${STEMS[$idx]} FINAL_EVIDENCE_MISSING_OR_INCOMPLETE" >&2
    failures=$((failures + 1))
  fi
done

if [ "$failures" -ne 0 ]; then
  echo "iter235 execution failed closed: $failures evidence error(s)" >&2
  exit 1
fi
echo "=== iter235 complete for shard $SHARD_INDEX/$SHARD_COUNT: ${#STEMS[@]} rows ==="
