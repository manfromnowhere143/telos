#!/usr/bin/env bash
# iter193 Phase B - decide certified-resolved and wrongness by execution on native-x86 CI.
#
# For each Phase A candidate, inside its pinned official SWE-bench container:
#   1. apply the test patch, then the VARIANT patch; run FAIL_TO_PASS + PASS_TO_PASS.
#      -> "certified" iff every F2P and every P2P test passes (the official harness would mark resolved).
#   2. run the instance's full uncurated test file(s) under VARIANT and under GOLD.
#      -> "wrong" iff some test T outside (F2P u P2P) passes under gold and fails under variant.
#
# No model, no API key, no network beyond pulling the pinned public image. Serial pull -> run -> rmi to
# respect runner disk. Writes one JSON result the Phase B adjudicator re-derives bars from.
set -uo pipefail

STAGE="experiments/iter193_certified_resolved_reward_hack_construction/proof/raw/phase_a_candidates"
OUTDIR="experiments/iter193_certified_resolved_reward_hack_construction/proof/raw/phase_b_execution"
OUT="$OUTDIR/ci_execution_results.json"
mkdir -p "$OUTDIR"

SUMMARY="$STAGE/phase_a_summary.json"
if [ ! -f "$SUMMARY" ]; then
  echo "missing $SUMMARY (run Phase A first)"; exit 1
fi

# instance ids with a staged candidate
mapfile -t IIDS < <(python3 -c "
import json
s=json.load(open('$SUMMARY'))
for m in s['manifest']:
    if m['status']=='candidate': print(m['instance_id'])
")

echo "[" > "$OUT"
first=1
for iid in "${IIDS[@]}"; do
  [ -z "$iid" ] && continue
  stem="${iid//\//__}"
  # Official SWE-bench image tags lowercase the instance id and replace '__' with '_1776_'.
  img="swebench/sweb.eval.x86_64.$(echo "$iid" | tr '[:upper:]' '[:lower:]' | sed 's/__/_1776_/'):latest"
  echo "=== $iid ($img) ==="

  # Test ids for this instance, written to files the container reads (avoids shell-quoting hazards).
  python3 -c "
import json
s=json.load(open('$SUMMARY'))
m=next(x for x in s['manifest'] if x['instance_id']=='$iid')
open('$OUTDIR/$stem.f2p.txt','w').write('\n'.join(m['fail_to_pass']))
"
  # PASS_TO_PASS from the pinned snapshot (source of truth), plus the test files to sweep.
  python3 -c "
import json
snap=json.load(open('$STAGE/../swebench_verified_rows_snapshot.json')) if False else None
rows=json.load(open('experiments/iter154_reward_hack_benchmark_expansion_pilot/proof/raw/swebench_verified_rows_snapshot.json'))['rows']
r=next(x for x in rows if x['instance_id']=='$iid')
p2p=json.loads(r['PASS_TO_PASS']); f2p=json.loads(r['FAIL_TO_PASS'])
open('$OUTDIR/$stem.p2p.txt','w').write('\n'.join(p2p))
graded=set(p2p)|set(f2p)
files=sorted({t.split('::')[0] for t in graded})
open('$OUTDIR/$stem.testfiles.txt','w').write('\n'.join(files))
open('$OUTDIR/$stem.graded.txt','w').write('\n'.join(sorted(graded)))
"

  if ! docker pull "$img" >/dev/null 2>&1; then
    echo "$iid PULL_FAIL"
    row="{\"instance_id\":\"$iid\",\"pull\":false}"
  else
    run=$(docker run --rm \
      -v "$PWD/$STAGE:/host" -v "$PWD/$OUTDIR:/ids" \
      "$img" bash -lc '
set -uo pipefail
source /opt/miniconda3/etc/profile.d/conda.sh 2>/dev/null; conda activate testbed 2>/dev/null
cd /testbed
STEM="'"$stem"'"
run_ids() { python -m pytest -p no:cacheprovider -q "$@" 2>&1 | tail -3; }

# ---- certified check: apply test patch + VARIANT, run graded set ----
git checkout -- . >/dev/null 2>&1
git apply /host/${STEM}.test.patch >/dev/null 2>&1 && echo TEST_PATCH_OK || echo TEST_PATCH_FAIL
git apply /host/${STEM}.variant.patch >/dev/null 2>&1 && echo VARIANT_OK || echo VARIANT_FAIL
echo GRADED_START
mapfile -t G < /ids/${STEM}.graded.txt
python -m pytest -p no:cacheprovider -q "${G[@]}" 2>&1 | tail -4
echo GRADED_END

# ---- wrongness: run full test files under VARIANT, capture per-test outcomes ----
echo VARIANT_FULL_START
mapfile -t TF < /ids/${STEM}.testfiles.txt
python -m pytest -p no:cacheprovider -rA -q "${TF[@]}" 2>&1 | grep -E "^(PASSED|FAILED|ERROR) " | sed "s/^/V /"
echo VARIANT_FULL_END

# ---- same test files under GOLD ----
git checkout -- . >/dev/null 2>&1
git apply /host/${STEM}.test.patch >/dev/null 2>&1
git apply /host/${STEM}.gold.patch >/dev/null 2>&1 && echo GOLD_OK || echo GOLD_FAIL
echo GOLD_FULL_START
python -m pytest -p no:cacheprovider -rA -q "${TF[@]}" 2>&1 | grep -E "^(PASSED|FAILED|ERROR) " | sed "s/^/G /"
echo GOLD_FULL_END
' 2>&1)
    # Persist the raw transcript; the adjudicator parses it deterministically.
    echo "$run" > "$OUTDIR/$stem.transcript.txt"
    graded_tail=$(echo "$run" | sed -n '/GRADED_START/,/GRADED_END/p' | tr '\n' ' ' | sed 's/"/'"'"'/g')
    echo "  graded: $graded_tail"
    row="{\"instance_id\":\"$iid\",\"pull\":true,\"transcript\":\"$stem.transcript.txt\"}"
    docker rmi "$img" >/dev/null 2>&1 || true
  fi
  [ $first -eq 0 ] && echo "," >> "$OUT"
  echo "$row" >> "$OUT"
  first=0
done
echo "]" >> "$OUT"
echo "=== phase B transcripts written under $OUTDIR ==="
