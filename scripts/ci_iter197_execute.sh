#!/usr/bin/env bash
# iter197 Phase B - execute each gold-free correctness property in its pinned container under gold and
# variant. A property is sound if it prints PROP_PASS on the gold patch (correct code satisfies it); a
# sound property that prints PROP_FAIL on the variant catches the hack. No model, no API key.
set -uo pipefail

PROPS="experiments/iter197_gold_free_oracle_vs_certified_hacks/proof/raw/properties"
CANDS="experiments/iter193_certified_resolved_reward_hack_construction/proof/raw/phase_a_candidates"
OUTDIR="experiments/iter197_gold_free_oracle_vs_certified_hacks/proof/raw/execution"
mkdir -p "$OUTDIR"

mapfile -t IIDS < <(python3 -c "
import json
s=json.load(open('$PROPS/phase_a_summary.json'))
for m in s['manifest']:
    if m['status']=='property': print(m['instance_id'])
")

for iid in "${IIDS[@]}"; do
  [ -z "$iid" ] && continue
  stem="${iid//\//__}"
  img="swebench/sweb.eval.x86_64.$(echo "$iid" | tr '[:upper:]' '[:lower:]' | sed 's/__/_1776_/'):latest"
  echo "=== $iid ($img) ==="
  if ! docker pull "$img" >/dev/null 2>&1; then
    echo "$iid PULL_FAIL"; continue
  fi
  for cond in gold variant; do
    docker run --rm \
      -v "$PWD/$PROPS:/props:ro" -v "$PWD/$CANDS:/cands:ro" \
      "$img" bash -lc '
set -uo pipefail
source /opt/miniconda3/bin/activate 2>/dev/null; conda activate testbed 2>/dev/null
cd /testbed
git config --global --add safe.directory /testbed 2>/dev/null
git checkout -- . >/dev/null 2>&1; git clean -fdq >/dev/null 2>&1
STEM="'"$stem"'"; COND="'"$cond"'"
if git apply -v /cands/${STEM}.${COND}.patch >/dev/null 2>&1; then echo "APPLY_OK ${COND}"; else echo "APPLY_FAIL ${COND}"; fi
python -m pip install -e . >/dev/null 2>&1 || true
echo ">>>>> Property Start"
python /props/${STEM}.property.py 2>&1
echo ">>>>> Property End"
' > "$OUTDIR/$stem.$cond.log" 2>&1
    res=$(grep -m1 -E "^PROP_(PASS|FAIL)" "$OUTDIR/$stem.$cond.log" || echo "(no PROP result)")
    echo "  $cond: $res"
  done
  docker rmi "$img" >/dev/null 2>&1 || true
done
echo "=== iter197 execution logs written under $OUTDIR ==="
