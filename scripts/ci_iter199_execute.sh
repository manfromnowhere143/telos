#!/usr/bin/env bash
# iter199 Phase B - certify AND witness each adversary variant in one native-x86 CI job.
#
# For each candidate with a spec and a scenario, inside its pinned official SWE-bench container:
#   - variant condition: apply the variant, install, run the official eval_script (certification: does the
#     variant pass every FAIL_TO_PASS and PASS_TO_PASS test?), then run the witnessing scenario (variant
#     RESULT= line);
#   - gold condition: apply the gold patch, install, run the witnessing scenario (gold RESULT= line).
# The adjudicator decides: certified = variant passes all graded tests; witnessed = gold and variant
# RESULT lines differ and the gold run is clean; confirmed = certified AND witnessed.
#
# No model, no API key. Serial pull -> run -> rmi to respect runner disk.
set -uo pipefail

SPECS="experiments/iter199_benchmark_expansion_across_repos/proof/raw/specs"
SCEN="experiments/iter199_benchmark_expansion_across_repos/proof/raw/scenarios"
CANDS="experiments/iter199_benchmark_expansion_across_repos/proof/raw/candidates"
OUTDIR="experiments/iter199_benchmark_expansion_across_repos/proof/raw/execution"
mkdir -p "$OUTDIR"

mapfile -t IIDS < <(python3 -c "
import json,os
idx=json.load(open('$SPECS/index.json'))
scen=set()
p='$SCEN/scenarios_summary.json'
if os.path.exists(p):
    for m in json.load(open(p))['manifest']:
        if m['status']=='scenario': scen.add(m['instance_id'])
for s in idx['specs']:
    if s['instance_id'] in scen: print(s['instance_id'])
")

for iid in "${IIDS[@]}"; do
  [ -z "$iid" ] && continue
  stem="${iid//\//__}"
  img="swebench/sweb.eval.x86_64.$(echo "$iid" | tr '[:upper:]' '[:lower:]' | sed 's/__/_1776_/'):latest"
  echo "=== $iid ($img) ==="
  if ! docker pull "$img" >/dev/null 2>&1; then
    echo "$iid PULL_FAIL"; continue
  fi

  # Variant: certification (eval_script) + witness scenario, one install.
  docker run --rm -v "$PWD/$SPECS:/specs:ro" -v "$PWD/$SCEN:/scen:ro" -v "$PWD/$CANDS:/cands:ro" \
    "$img" bash -lc '
set -uo pipefail
source /opt/miniconda3/bin/activate 2>/dev/null; conda activate testbed 2>/dev/null
cd /testbed
git config --global --add safe.directory /testbed 2>/dev/null
git checkout -- . >/dev/null 2>&1; git clean -fdq >/dev/null 2>&1
STEM="'"$stem"'"
if git apply -v /cands/${STEM}.variant.patch >/dev/null 2>&1; then echo "APPLY_OK variant"; else echo "APPLY_FAIL variant"; fi
python -m pip install -e . >/dev/null 2>&1 || true
echo ">>>>> Cert Start"
bash /specs/${STEM}.eval_script.sh 2>&1
echo ">>>>> Cert End"
echo ">>>>> Scenario Start"
python /scen/${STEM}.scenario.py 2>&1
echo ">>>>> Scenario End"
' > "$OUTDIR/$stem.variant.log" 2>&1

  # Gold: witness scenario only.
  docker run --rm -v "$PWD/$SCEN:/scen:ro" -v "$PWD/$CANDS:/cands:ro" \
    "$img" bash -lc '
set -uo pipefail
source /opt/miniconda3/bin/activate 2>/dev/null; conda activate testbed 2>/dev/null
cd /testbed
git config --global --add safe.directory /testbed 2>/dev/null
git checkout -- . >/dev/null 2>&1; git clean -fdq >/dev/null 2>&1
STEM="'"$stem"'"
if git apply -v /cands/${STEM}.gold.patch >/dev/null 2>&1; then echo "APPLY_OK gold"; else echo "APPLY_FAIL gold"; fi
python -m pip install -e . >/dev/null 2>&1 || true
echo ">>>>> Scenario Start"
python /scen/${STEM}.scenario.py 2>&1
echo ">>>>> Scenario End"
' > "$OUTDIR/$stem.gold.log" 2>&1

  vres=$(grep -m1 "^RESULT=" "$OUTDIR/$stem.variant.log" || echo "(none)")
  gres=$(grep -m1 "^RESULT=" "$OUTDIR/$stem.gold.log" || echo "(none)")
  echo "  variant: $vres"; echo "  gold: $gres"
  docker rmi "$img" >/dev/null 2>&1 || true
done
echo "=== iter199 execution logs written under $OUTDIR ==="
