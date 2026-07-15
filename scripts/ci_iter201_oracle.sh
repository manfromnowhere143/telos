#!/usr/bin/env bash
# iter201 Detector B execution - run each gold-free property under gold and hack-variant, on native-x86 CI.
# The 22 hacks span two source dirs (iter193 for the iter195 hacks, iter199 for the iter199 hacks); the
# per-instance source is read from the properties summary. Sound = passes on gold; a sound property that
# fails on the variant catches the hack. No model, no API key.
set -uo pipefail
PROPS="experiments/iter201_detectors_on_full_benchmark/proof/raw/properties"
OUTDIR="experiments/iter201_detectors_on_full_benchmark/proof/raw/execution"
D195="experiments/iter193_certified_resolved_reward_hack_construction/proof/raw/phase_a_candidates"
D199="experiments/iter199_benchmark_expansion_across_repos/proof/raw/candidates"
mkdir -p "$OUTDIR"
python3 -c "
import json
for m in json.load(open('$PROPS/properties_summary.json'))['manifest']:
    if m['status']=='property': print(m['instance_id']+'\t'+m['source_experiment'])
" > "$OUTDIR/_worklist.tsv"
while IFS=$'\t' read -r iid src; do
  [ -z "$iid" ] && continue
  stem="${iid//\//__}"
  if [ "$src" = "iter195_synthesized_input_differential_oracle" ]; then cdir="$D195"; else cdir="$D199"; fi
  img="swebench/sweb.eval.x86_64.$(echo "$iid" | tr '[:upper:]' '[:lower:]' | sed 's/__/_1776_/'):latest"
  echo "=== $iid ($img) [$cdir]"
  docker pull "$img" >/dev/null 2>&1 || { echo "$iid PULL_FAIL"; continue; }
  for cond in gold variant; do
    docker run --rm -v "$PWD/$PROPS:/props:ro" -v "$PWD/$cdir:/cands:ro" "$img" bash -lc '
set -uo pipefail; source /opt/miniconda3/bin/activate 2>/dev/null; conda activate testbed 2>/dev/null; cd /testbed
git config --global --add safe.directory /testbed 2>/dev/null; git checkout -- . >/dev/null 2>&1; git clean -fdq >/dev/null 2>&1
STEM="'"$stem"'"; COND="'"$cond"'"
if git apply -v /cands/${STEM}.${COND}.patch >/dev/null 2>&1; then echo "APPLY_OK ${COND}"; else echo "APPLY_FAIL ${COND}"; fi
python -m pip install -e . >/dev/null 2>&1 || true
echo ">>>>> Property Start"; python /props/${STEM}.property.py 2>&1; echo ">>>>> Property End"
' > "$OUTDIR/$stem.$cond.log" 2>&1
    echo "  $cond: $(grep -m1 -E '^PROP_(PASS|FAIL)' "$OUTDIR/$stem.$cond.log" || echo none)"
  done
  docker rmi "$img" >/dev/null 2>&1 || true
done < "$OUTDIR/_worklist.tsv"
echo "=== iter201 oracle logs written ==="
