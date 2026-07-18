#!/usr/bin/env bash
# Iter234: run three patch-blind authors' consequence tests against each candidate patch, and against the
# gold patch, in one container pass per benchmark row.
#
# WHY GOLD IS MOUNTED HERE AND WHY THAT IS NOT A LEAK. The pre-registration defines two arms: a gold-free
# arm (every test counts) and a gold-validated arm (only tests that PASS on gold count). The second needs
# gold results, so this executor applies the gold patch too. The AUTHOR never saw gold -- it saw only the
# issue text, and scripts/validate_iter234_execution_safety.py checks the prompt for that. Authoring
# blindness is the experiment's integrity condition; the scorer is allowed a reference the author was denied.
#
# One pull per row, not per test: images are multi-GB and 3 authors x 2 patches would otherwise mean six
# pulls for the same image.
set -uo pipefail

ITER234_EXP="iter234_issue_only_consequence_tests"
EVAL_SET="experiments/iter230_gold_free_detector_natural/proof/raw/eval_set.json"
TESTDIR="experiments/${ITER234_EXP}/proof/raw/tests"
OUTDIR="experiments/${ITER234_EXP}/proof/raw/execution"

FROZEN_EVAL_SET_SHA256="10dc898c3cdc6026aaedc57d469e546b279a982df3772ba3388c1dfb515b8928"
ITER234_APPLY_TIMEOUT_SECONDS=120
ITER234_TEST_TIMEOUT_SECONDS=180
ITER234_KILL_GRACE_SECONDS=10
ITER234_OUTPUT_LIMIT_BYTES=262144
ITER234_ROW_CEILING_SECONDS=2400

validate_shard_config() {
  local index="$1" count="$2"
  [[ "$index" =~ ^(0|[1-9][0-9]{0,2})$ ]] || return 1
  [[ "$count" =~ ^[1-9][0-9]{0,2}$ ]] || return 1
  (( 10#$count >= 1 && 10#$count <= 256 && 10#$index < 10#$count ))
}

SHARD_INDEX_RAW="${TELOS_ITER234_SHARD_INDEX-0}"
SHARD_COUNT_RAW="${TELOS_ITER234_SHARD_COUNT-1}"
if ! validate_shard_config "$SHARD_INDEX_RAW" "$SHARD_COUNT_RAW"; then
  echo "invalid shard config: index=$SHARD_INDEX_RAW count=$SHARD_COUNT_RAW" >&2
  exit 2
fi
SHARD_INDEX=$((10#$SHARD_INDEX_RAW))
SHARD_COUNT=$((10#$SHARD_COUNT_RAW))
mkdir -p "$OUTDIR"

python3 scripts/validate_iter234_execution_safety.py || exit 2

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

if ! row_output="$(python3 - "$EVAL_SET" "$TESTDIR" "$FROZEN_EVAL_SET_SHA256" <<'PY'
import hashlib
import json
import re
import sys
from pathlib import Path

eval_path, test_dir, frozen = Path(sys.argv[1]), Path(sys.argv[2]), sys.argv[3]
raw = eval_path.read_bytes()
if hashlib.sha256(raw).hexdigest() != frozen:
    raise SystemExit("frozen benchmark sha changed")
data = json.loads(raw)
items = [dict(r, label="certified_yet_wrong") for r in data["positives"]]
items += [dict(r, label="certified_correct") for r in data["negatives"]]
if len(items) != 67:
    raise SystemExit("benchmark is not the frozen 67 rows")

summary = json.loads((test_dir / "tests_summary.json").read_text())
if summary.get("schema_version") != "telos.iter234.tests_summary.v1":
    raise SystemExit("tests summary schema mismatch")
have = {
    (r["author"], r["run"], r["instance_id"])
    for r in summary["manifest"] if r["status"] == "test"
}

for ordinal, item in enumerate(items):
    iid, run = item["instance_id"], item["run"]
    if not re.fullmatch(r"[A-Za-z0-9_.-]+__[A-Za-z0-9_.-]+", iid):
        raise SystemExit(f"unsafe instance id: {iid!r}")
    authors = [a for a in ("openai", "anthropic", "google") if (a, run, iid) in have]
    row_stem = f"{run}__{iid.replace('/', '__')}"
    image = "swebench/sweb.eval.x86_64." + re.sub("__", "_1776_", iid.lower()) + ":latest"
    print("\t".join([
        str(ordinal), row_stem, iid, image,
        str(item["model_patch_path"]), ",".join(authors) or "-",
    ]))
PY
)"; then
  echo "iter234 preflight failed closed" >&2
  exit 2
fi

ORDS=(); STEMS=(); IIDS=(); IMAGES=(); PATCHES=(); AUTHORS=()
while IFS=$'\t' read -r o s i img p a; do
  [ -n "$o" ] || continue
  if (( o % SHARD_COUNT == SHARD_INDEX )); then
    ORDS+=("$o"); STEMS+=("$s"); IIDS+=("$i"); IMAGES+=("$img"); PATCHES+=("$p"); AUTHORS+=("$a")
  fi
done <<< "$row_output"
echo "=== iter234 shard $SHARD_INDEX/$SHARD_COUNT selected ${#STEMS[@]} of 67 rows ==="

row_complete() {
  local stem="$1" authors="$2"
  local file="$OUTDIR/$stem.tests.log"
  [ -f "$file" ] || return 1
  [ "$(grep -E -c '^IMAGE_ID=sha256:[0-9a-f]{64}$' "$file" 2>/dev/null)" -eq 1 ] || return 1
  [ "$(grep -F -x -c "APPLY_OK candidate" "$file" 2>/dev/null)" -eq 1 ] || return 1
  [ "$(grep -F -x -c "APPLY_OK gold" "$file" 2>/dev/null)" -eq 1 ] || return 1
  ! grep -E -q '^(APPLY_FAIL|SETUP_FAIL)' "$file" || return 1
  [ "$authors" = "-" ] && return 0
  local author
  for author in ${authors//,/ }; do
    # Both arms must be present for every author with a test, or the row cannot be scored.
    [ "$(grep -E -c "^EXIT candidate ${author}=[0-9]+$" "$file" 2>/dev/null)" -eq 1 ] || return 1
    [ "$(grep -E -c "^EXIT gold ${author}=[0-9]+$" "$file" 2>/dev/null)" -eq 1 ] || return 1
  done
}

failures=0
for idx in "${!STEMS[@]}"; do
  stem="${STEMS[$idx]}"; image="${IMAGES[$idx]}"; patch="${PATCHES[$idx]}"; authors="${AUTHORS[$idx]}"
  log="$OUTDIR/$stem.tests.log"
  echo "=== $stem ($authors) ==="
  if [ "$authors" = "-" ]; then
    printf 'NO_TESTS\n' > "$log"
    continue
  fi

  gold="experiments/${stem%%__*}/proof/raw/solutions/${IIDS[$idx]//\//__}.gold.patch"
  if [ ! -f "$gold" ]; then
    echo "$stem GOLD_PATCH_MISSING $gold" >&2
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

  MOUNTS=(-v "$PWD/$patch:/telos/candidate.patch:ro" -v "$PWD/$gold:/telos/gold.patch:ro")
  for author in ${authors//,/ }; do
    MOUNTS+=(-v "$PWD/$TESTDIR/${author}__${stem}.test.py:/telos/test_${author}.py:ro")
  done

  row_rc=0
  timeout --signal=TERM --kill-after=60s "${ITER234_ROW_CEILING_SECONDS}s" \
    docker run --rm "${DOCKER_SAFETY_ARGS[@]}" \
    -e TELOS_AUTHORS="$authors" \
    -e TELOS_IMAGE_ID="$image_id" \
    -e TELOS_APPLY_TIMEOUT_SECONDS="$ITER234_APPLY_TIMEOUT_SECONDS" \
    -e TELOS_TEST_TIMEOUT_SECONDS="$ITER234_TEST_TIMEOUT_SECONDS" \
    -e TELOS_KILL_GRACE_SECONDS="$ITER234_KILL_GRACE_SECONDS" \
    -e TELOS_OUTPUT_LIMIT_BYTES="$ITER234_OUTPUT_LIMIT_BYTES" \
    "${MOUNTS[@]}" \
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
  local author
  for author in ${TELOS_AUTHORS//,/ }; do
    echo ">>>>> ${arm} ${author} Start"
    timeout --signal=TERM --kill-after="${TELOS_KILL_GRACE_SECONDS}s" \
      "${TELOS_TEST_TIMEOUT_SECONDS}s" python "/telos/test_${author}.py" 2>&1 | head -c "$TELOS_OUTPUT_LIMIT_BYTES"
    local rc="${PIPESTATUS[0]}"
    if [ "$rc" -eq 124 ] || [ "$rc" -eq 137 ]; then
      echo "RESULT=('"'"'TIMEOUT'"'"', ${TELOS_TEST_TIMEOUT_SECONDS})"
    fi
    echo "EXIT ${arm} ${author}=${rc}"
    echo ">>>>> ${arm} ${author} End"
  done
}
run_arm candidate /telos/candidate.patch || exit $?
run_arm gold /telos/gold.patch || exit $?
exit 0
' > "$log" 2>&1 || row_rc=$?

  if [ "$row_rc" -eq 125 ]; then
    echo "$stem CONTAINER_FLAGS_REJECTED" >&2; head -3 "$log" >&2; exit 2
  fi
  if ! row_complete "$stem" "$authors"; then
    echo "$stem INCOMPLETE_EVIDENCE" >&2
  fi
  docker rmi "$image" >/dev/null 2>&1 || true
done

for idx in "${!STEMS[@]}"; do
  if ! row_complete "${STEMS[$idx]}" "${AUTHORS[$idx]}"; then
    echo "${STEMS[$idx]} FINAL_EVIDENCE_MISSING_OR_INCOMPLETE" >&2
    failures=$((failures + 1))
  fi
done

if [ "$failures" -ne 0 ]; then
  echo "iter234 execution failed closed: $failures evidence error(s)" >&2
  exit 1
fi
echo "=== iter234 complete for shard $SHARD_INDEX/$SHARD_COUNT: ${#STEMS[@]} rows ==="
