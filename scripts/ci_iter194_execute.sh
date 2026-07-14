#!/usr/bin/env bash
# iter194 Phase B (revised runner) - decide certified-resolved and wrongness with the repo-correct
# command, on native-x86 CI. Replaces iter193's bare-pytest harness, which could not run django
# (no pytest in testbed) or astropy (collection gap).
#
# For each iter193 candidate, inside its pinned official SWE-bench container, for condition in {gold,
# variant}: reset the repo, apply that source patch, then run the instance's committed official
# eval_script (which applies the test patch and runs the whole test module with the repo-correct command:
# runtests.py for django, pytest -rA for the others). The full per-test output between the harness markers
# is captured for both conditions. The adjudicator decides:
#   certified  = variant passes every FAIL_TO_PASS and PASS_TO_PASS test;
#   wrong      = a test outside (F2P u P2P) that gold passes and the variant fails.
#
# No model, no API key. Serial pull -> run -> rmi to respect runner disk.
set -uo pipefail

SPECS="experiments/iter194_certified_resolved_oracle_and_runner_fix/proof/raw/specs"
CANDS="experiments/iter193_certified_resolved_reward_hack_construction/proof/raw/phase_a_candidates"
OUTDIR="experiments/iter194_certified_resolved_oracle_and_runner_fix/proof/raw/execution"
mkdir -p "$OUTDIR"

mapfile -t IIDS < <(python3 -c "
import json
idx=json.load(open('$SPECS/index.json'))
for s in idx['specs']: print(s['instance_id'])
")

for iid in "${IIDS[@]}"; do
  [ -z "$iid" ] && continue
  stem="${iid//\//__}"
  img="swebench/sweb.eval.x86_64.$(echo "$iid" | tr '[:upper:]' '[:lower:]' | sed 's/__/_1776_/'):latest"
  echo "=== $iid ($img) ==="

  if ! docker pull "$img" >/dev/null 2>&1; then
    echo "$iid PULL_FAIL"
    continue
  fi

  # Run gold then variant. Each: reset repo, apply that source patch, run the official eval_script,
  # capture the section between the harness output markers.
  for cond in gold variant; do
    docker run --rm \
      -v "$PWD/$SPECS:/specs:ro" -v "$PWD/$CANDS:/cands:ro" \
      "$img" bash -lc '
set -uo pipefail
source /opt/miniconda3/bin/activate 2>/dev/null; conda activate testbed 2>/dev/null
cd /testbed
git config --global --add safe.directory /testbed 2>/dev/null
git checkout -- . >/dev/null 2>&1; git clean -fdq >/dev/null 2>&1
STEM="'"$stem"'"; COND="'"$cond"'"
if git apply -v /cands/${STEM}.${COND}.patch >/dev/null 2>&1; then echo "APPLY_OK ${COND}"; else echo "APPLY_FAIL ${COND}"; fi
bash /specs/${STEM}.eval_script.sh 2>&1
' > "$OUTDIR/$stem.$cond.log" 2>&1
    marker_ok=$(grep -c "Start Test Output" "$OUTDIR/$stem.$cond.log" || true)
    echo "  $cond: apply=$(grep -o "APPLY_OK\|APPLY_FAIL" "$OUTDIR/$stem.$cond.log" | head -1) markers=$marker_ok bytes=$(wc -c < "$OUTDIR/$stem.$cond.log")"
  done

  docker rmi "$img" >/dev/null 2>&1 || true
done
echo "=== iter194 execution logs written under $OUTDIR ==="
