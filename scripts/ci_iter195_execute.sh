#!/usr/bin/env bash
# iter195 Phase B - execute each witnessing scenario in its pinned container under gold and variant.
#
# For each certified-resolved candidate with a generated scenario, inside its pinned official SWE-bench
# container, for condition in {gold, variant}: reset the repo, apply that source patch, run the committed
# version-agnostic scenario against the installed code, and capture the single deterministic RESULT= line
# (and any traceback). The adjudicator decides:
#   validated = scenario runs under gold without error and prints RESULT=;
#   wrong     = validated AND the variant RESULT differs from the gold RESULT.
#
# No model, no API key. Serial pull -> run -> rmi to respect runner disk.
set -uo pipefail

SCEN="experiments/iter195_synthesized_input_differential_oracle/proof/raw/scenarios"
CANDS="experiments/iter193_certified_resolved_reward_hack_construction/proof/raw/phase_a_candidates"
OUTDIR="experiments/iter195_synthesized_input_differential_oracle/proof/raw/execution"
mkdir -p "$OUTDIR"

mapfile -t IIDS < <(python3 -c "
import json
s=json.load(open('$SCEN/phase_a_summary.json'))
for m in s['manifest']:
    if m['status']=='scenario': print(m['instance_id'])
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
      -v "$PWD/$SCEN:/scen:ro" -v "$PWD/$CANDS:/cands:ro" \
      "$img" bash -lc '
set -uo pipefail
source /opt/miniconda3/bin/activate 2>/dev/null; conda activate testbed 2>/dev/null
cd /testbed
git config --global --add safe.directory /testbed 2>/dev/null
git checkout -- . >/dev/null 2>&1; git clean -fdq >/dev/null 2>&1
STEM="'"$stem"'"; COND="'"$cond"'"
if git apply -v /cands/${STEM}.${COND}.patch >/dev/null 2>&1; then echo "APPLY_OK ${COND}"; else echo "APPLY_FAIL ${COND}"; fi
python -m pip install -e . >/dev/null 2>&1 || true
echo ">>>>> Scenario Start"
python /scen/${STEM}.scenario.py 2>&1
echo ">>>>> Scenario End"
' > "$OUTDIR/$stem.$cond.log" 2>&1
    res=$(grep -m1 "^RESULT=" "$OUTDIR/$stem.$cond.log" || echo "(no RESULT)")
    echo "  $cond: $res"
  done
  docker rmi "$img" >/dev/null 2>&1 || true
done
echo "=== iter195 execution logs written under $OUTDIR ==="
