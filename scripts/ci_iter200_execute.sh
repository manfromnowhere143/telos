#!/usr/bin/env bash
# iter200 Phase B - certify the neutral-solve MODEL patch and witness gold-vs-model, on native-x86 CI.
# Per instance: variant condition applies the MODEL patch, installs, runs the eval_script (certification)
# and the scenario (model RESULT); gold condition applies the gold patch and runs the scenario (gold
# RESULT). Confirmed-divergence is decided by the adjudicator; wrongness is adjudicated by a blind judge.
set -uo pipefail
SPECS="experiments/iter200_natural_certified_yet_wrong_rate/proof/raw/specs"
SCEN="experiments/iter200_natural_certified_yet_wrong_rate/proof/raw/scenarios"
SOLS="experiments/iter200_natural_certified_yet_wrong_rate/proof/raw/solutions"
OUTDIR="experiments/iter200_natural_certified_yet_wrong_rate/proof/raw/execution"
mkdir -p "$OUTDIR"
mapfile -t IIDS < <(python3 -c "import json;[print(s['instance_id']) for s in json.load(open('$SPECS/index.json'))['specs']]")
for iid in "${IIDS[@]}"; do
  [ -z "$iid" ] && continue
  stem="${iid//\//__}"
  img="swebench/sweb.eval.x86_64.$(echo "$iid" | tr '[:upper:]' '[:lower:]' | sed 's/__/_1776_/'):latest"
  echo "=== $iid ($img) ==="
  docker pull "$img" >/dev/null 2>&1 || { echo "$iid PULL_FAIL"; continue; }
  docker run --rm -v "$PWD/$SPECS:/specs:ro" -v "$PWD/$SCEN:/scen:ro" -v "$PWD/$SOLS:/sols:ro" "$img" bash -lc '
set -uo pipefail; source /opt/miniconda3/bin/activate 2>/dev/null; conda activate testbed 2>/dev/null; cd /testbed
git config --global --add safe.directory /testbed 2>/dev/null; git checkout -- . >/dev/null 2>&1; git clean -fdq >/dev/null 2>&1
STEM="'"$stem"'"
if git apply -v /sols/${STEM}.model.patch >/dev/null 2>&1; then echo "APPLY_OK variant"; else echo "APPLY_FAIL variant"; fi
python -m pip install -e . >/dev/null 2>&1 || true
echo ">>>>> Cert Start"; bash /specs/${STEM}.eval_script.sh 2>&1; echo ">>>>> Cert End"
echo ">>>>> Scenario Start"; python /scen/${STEM}.scenario.py 2>&1; echo ">>>>> Scenario End"
' > "$OUTDIR/$stem.variant.log" 2>&1
  docker run --rm -v "$PWD/$SCEN:/scen:ro" -v "$PWD/$SOLS:/sols:ro" "$img" bash -lc '
set -uo pipefail; source /opt/miniconda3/bin/activate 2>/dev/null; conda activate testbed 2>/dev/null; cd /testbed
git config --global --add safe.directory /testbed 2>/dev/null; git checkout -- . >/dev/null 2>&1; git clean -fdq >/dev/null 2>&1
STEM="'"$stem"'"
if git apply -v /sols/${STEM}.gold.patch >/dev/null 2>&1; then echo "APPLY_OK gold"; else echo "APPLY_FAIL gold"; fi
python -m pip install -e . >/dev/null 2>&1 || true
echo ">>>>> Scenario Start"; python /scen/${STEM}.scenario.py 2>&1; echo ">>>>> Scenario End"
' > "$OUTDIR/$stem.gold.log" 2>&1
  echo "  variant: $(grep -m1 '^RESULT=' "$OUTDIR/$stem.variant.log" || echo none)"
  echo "  gold: $(grep -m1 '^RESULT=' "$OUTDIR/$stem.gold.log" || echo none)"
  docker rmi "$img" >/dev/null 2>&1 || true
done
echo "=== iter200 execution logs written ==="
