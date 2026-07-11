#!/usr/bin/env bash
# Iter134 - run the SWE-bench Docker batch on a native-x86 runner (no emulation).
# Serial pull -> run -> remove image, to respect runner disk. Writes a results JSON.
set -uo pipefail

DIR="experiments/iter134_x86_ci_docker_batch/fixtures"
OUT="experiments/iter134_x86_ci_docker_batch/proof/ci_batch_results.json"
mkdir -p "$(dirname "$OUT")"

echo "[" > "$OUT"
first=1
while read -r iid tag tfile tname; do
  [ -z "$iid" ] && continue
  img="swebench/sweb.eval.x86_64.${tag}:latest"
  echo "=== $iid ($img) ==="
  if ! docker pull "$img" >/dev/null 2>&1; then
    echo "$iid PULL_FAIL"
    row="{\"instance_id\":\"$iid\",\"pull\":false,\"base\":\"\",\"gold\":\"\"}"
  else
    run=$(docker run --rm -v "$PWD/$DIR:/host" "$img" bash -c "
source /opt/miniconda3/etc/profile.d/conda.sh; conda activate testbed; cd /testbed
git checkout -- . >/dev/null 2>&1; git apply /host/${iid}.test.patch >/dev/null 2>&1
echo BASE_START; python bin/test ${tfile} -k ${tname} 2>&1 | grep -E 'tests finished|\[OK\]|exceptions'; echo BASE_END
git checkout -- . >/dev/null 2>&1; git apply /host/${iid}.gold.patch >/dev/null 2>&1; git apply /host/${iid}.test.patch >/dev/null 2>&1
echo GOLD_START; python bin/test ${tfile} -k ${tname} 2>&1 | grep -E 'tests finished|\[OK\]|exceptions'; echo GOLD_END
" 2>&1)
    base=$(echo "$run" | sed -n '/BASE_START/,/BASE_END/p' | grep -E 'tests finished|\[OK\]|exceptions' | tr '\n' ' ')
    gold=$(echo "$run" | sed -n '/GOLD_START/,/GOLD_END/p' | grep -E 'tests finished|\[OK\]|exceptions' | tr '\n' ' ')
    echo "  base: $base"; echo "  gold: $gold"
    row="{\"instance_id\":\"$iid\",\"pull\":true,\"base\":\"$(echo "$base" | sed 's/"/'"'"'/g')\",\"gold\":\"$(echo "$gold" | sed 's/"/'"'"'/g')\"}"
    docker rmi "$img" >/dev/null 2>&1 || true
  fi
  [ $first -eq 0 ] && echo "," >> "$OUT"
  echo "$row" >> "$OUT"
  first=0
done < "$DIR/manifest.txt"
echo "]" >> "$OUT"
echo "=== results written to $OUT ==="
cat "$OUT"
