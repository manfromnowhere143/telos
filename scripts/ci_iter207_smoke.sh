#!/usr/bin/env bash
# No-science gate for the iter207 local-log-driver infrastructure correction.
set -uo pipefail

SOURCE_EXP="experiments/iter203_iter202_safety_recovery"
EXP="experiments/iter207_claim_integrity_and_admission_recovery"
SPECS="$SOURCE_EXP/proof/raw/specs"
RUNTIME_MANIFEST="$EXP/proof/raw/runtime_manifest.json"
SMOKEDIR="$EXP/proof/raw/smoke"
SMOKE_LIMIT_BYTES=65536

unset OPENAI_API_KEY ANTHROPIC_API_KEY
unset PYTHONHOME PYTHONINSPECT PYTHONPATH PYTHONSTARTUP PYTHONUSERBASE

if [ "${GITHUB_RUN_ATTEMPT-}" != "1" ]; then
  echo "iter207 smoke accepts canonical workflow attempt 1 only" >&2
  exit 2
fi
python3 -I -S scripts/build_iter203_safety_recovery.py --check || exit 2
python3 -I -S scripts/build_iter203_runtime_manifest.py --check || exit 2
python3 -I -S scripts/build_iter207_runtime_manifest.py --check || exit 2

python3 -I -S scripts/prepare_iter207_output_directory.py \
  --path "$SMOKEDIR" --new || exit 2
HOST_RECEIPT="$SMOKEDIR/observed-runtime-host.json"
python3 -I -S scripts/capture_iter207_runtime_host.py --write "$HOST_RECEIPT" || exit 2

if ! plan="$(python3 -I -S scripts/collect_iter207_execution.py source-lines \
  --spec-index "$SPECS/index.json" \
  --runtime-manifest "$RUNTIME_MANIFEST")"; then
  echo "iter207 smoke cannot derive the frozen source plan" >&2
  exit 2
fi
mapfile -t plan_lines <<< "$plan"
if [ "${#plan_lines[@]}" -ne 50 ]; then
  echo "iter207 smoke requires exactly 50 source-plan rows" >&2
  exit 2
fi
IFS=$'\t' read -r iid tag manifest_digest expected_image_id image_ref behavior \
  <<< "${plan_lines[0]}"
if [ "$image_ref" != "${tag%:*}@${manifest_digest}" ]; then
  echo "iter207 smoke ordinal-0 image lock differs" >&2
  exit 2
fi

if ! docker pull "$image_ref" >/dev/null 2>&1; then
  echo "iter207 smoke image pull failed" >&2
  exit 2
fi
image_id="$(docker image inspect --format '{{.Id}}' "$image_ref" 2>/dev/null)"
repo_digests="$(docker image inspect --format '{{json .RepoDigests}}' "$image_ref" 2>/dev/null)"
if [ "$image_id" != "$expected_image_id" ] || ! python3 - "$repo_digests" "$image_ref" <<'PY'
import json
import sys
values = json.loads(sys.argv[1])
raise SystemExit(0 if isinstance(values, list) and sys.argv[2] in values else 1)
PY
then
  echo "iter207 smoke image provenance differs" >&2
  docker rmi "$image_ref" >/dev/null 2>&1 || true
  exit 2
fi

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
SMOKE_ARGS=(
  run --rm
  "${DOCKER_SAFETY_ARGS[@]}"
  --entrypoint bash
  "$image_ref"
  --noprofile --norc -c 'printf "%s\n" TELOS_ITER207_LOG_DRIVER_SMOKE_OK'
)
argv_digest="$(python3 -I -S - docker "${SMOKE_ARGS[@]}" <<'PY'
import hashlib
import sys
digest = hashlib.sha256()
for value in sys.argv[1:]:
    digest.update(value.encode())
    digest.update(b"\0")
print(digest.hexdigest())
PY
)" || exit 2

stdout_work="$SMOKEDIR/smoke.stdout.work"
stderr_work="$SMOKEDIR/smoke.stderr.work"
combined_work="$SMOKEDIR/smoke.combined.work"
smoke_rc=0
(
  ulimit -f "$((SMOKE_LIMIT_BYTES / 1024))"
  docker "${SMOKE_ARGS[@]}" > "$stdout_work" 2> "$stderr_work"
) || smoke_rc=$?
streams_exact=0
python3 -I -S - "$stdout_work" "$stderr_work" "$combined_work" <<'PY' && streams_exact=1
from pathlib import Path
import sys
stdout = Path(sys.argv[1]).read_bytes()
stderr = Path(sys.argv[2]).read_bytes()
combined = (
    b"TELOS_ITER207_SEPARATE_STREAMS_V1\n"
    + b"STDOUT_BYTES=" + str(len(stdout)).encode() + b"\n"
    + b"STDERR_BYTES=" + str(len(stderr)).encode() + b"\n"
    + b">>>>> STDOUT\n" + stdout
    + b">>>>> STDERR\n" + stderr
)
Path(sys.argv[3]).write_bytes(combined)
raise SystemExit(0 if stdout == b"TELOS_ITER207_LOG_DRIVER_SMOKE_OK\n" and stderr == b"" else 1)
PY
diagnostic="$SMOKEDIR/smoke.diagnostic.log"
diagnostic_metadata="$SMOKEDIR/smoke.diagnostic.receipt.json"
diagnostic_rc=0
python3 -I -S scripts/publish_iter207_runtime_diagnostic.py \
  --source "$combined_work" \
  --destination "$diagnostic" \
  --metadata-destination "$diagnostic_metadata" \
  --limit "$SMOKE_LIMIT_BYTES" \
  --phase "global_no_science_log_driver_smoke" \
  --row-id "$iid" \
  --image-ref "$image_ref" \
  --image-id "$image_id" \
  --shard-index -1 \
  --exit-code "$smoke_rc" \
  --argv-sha256 "$argv_digest" \
  --runtime-manifest "$RUNTIME_MANIFEST" \
  --runtime-host-receipt "$HOST_RECEIPT" || diagnostic_rc=$?

python3 -I -S - \
  "$SMOKEDIR/smoke.receipt.json" "$HOST_RECEIPT" "$diagnostic" \
  "$diagnostic_metadata" "$RUNTIME_MANIFEST" "$iid" "$image_ref" "$image_id" \
  "$argv_digest" "$smoke_rc" "$streams_exact" "$diagnostic_rc" \
  "$stdout_work" "$stderr_work" <<'PY'
import hashlib
import json
import os
from pathlib import Path
import sys

(
    destination_text,
    host_text,
    diagnostic_text,
    diagnostic_metadata_text,
    runtime_text,
    instance_id,
    image_ref,
    image_id,
    argv_sha256,
    exit_code,
    streams_exact,
    diagnostic_exit,
    stdout_text,
    stderr_text,
) = sys.argv[1:]

def load(path):
    return json.loads(Path(path).read_bytes())

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

github = {
    "repository": os.environ["GITHUB_REPOSITORY"],
    "run_attempt": os.environ["GITHUB_RUN_ATTEMPT"],
    "run_id": os.environ["GITHUB_RUN_ID"],
    "sha": os.environ["GITHUB_SHA"],
    "workflow_ref": os.environ["GITHUB_WORKFLOW_REF"],
}
stdout = Path(stdout_text).read_bytes()
stderr = Path(stderr_text).read_bytes()
passed = int(exit_code) == 0 and streams_exact == "1" and diagnostic_exit == "0"
document = {
    "argument_vector_sha256": argv_sha256,
    "command": [
        "bash", "--noprofile", "--norc", "-c",
        'printf "%s\\n" TELOS_ITER207_LOG_DRIVER_SMOKE_OK',
    ],
    "diagnostic": {
        "bytes": Path(diagnostic_text).stat().st_size,
        "path": Path(diagnostic_text).name,
        "receipt_sha256": sha(diagnostic_metadata_text),
        "sha256": sha(diagnostic_text),
    },
    "docker_safety_args": [
        "--network", "none", "--cap-drop", "ALL",
        "--security-opt", "no-new-privileges=true", "--pids-limit", "1024",
        "--memory", "10g", "--cpus", "4", "--log-driver", "local",
        "--log-opt", "max-size=3m", "--log-opt", "max-file=1",
        "--log-opt", "compress=false",
    ],
    "exit_code": int(exit_code),
    "github": github,
    "image_id": image_id,
    "image_ref": image_ref,
    "ordinal": 0,
    "output_exact": streams_exact == "1",
    "row_id": instance_id,
    "runtime_host": load(host_text),
    "runtime_manifest_sha256": sha(runtime_text),
    "schema_version": "telos.iter207.no_science_smoke_receipt.v1",
    "status": "pass" if passed else "infrastructure_null",
    "streams": {
        "stderr": {
            "bytes": len(stderr),
            "sha256": hashlib.sha256(stderr).hexdigest(),
        },
        "stdout": {
            "bytes": len(stdout),
            "sha256": hashlib.sha256(stdout).hexdigest(),
        },
    },
}
payload = (json.dumps(document, indent=2, sort_keys=True, allow_nan=False) + "\n").encode()
destination = Path(destination_text)
descriptor = os.open(destination, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
with os.fdopen(descriptor, "wb") as stream:
    stream.write(payload)
    stream.flush()
    os.fsync(stream.fileno())
Path(stdout_text).unlink()
Path(stderr_text).unlink()
raise SystemExit(0 if passed else 1)
PY
smoke_result=$?
docker rmi "$image_ref" >/dev/null 2>&1 || true
if [ "$smoke_result" -ne 0 ]; then
  echo "iter207 no-science smoke failed closed" >&2
  exit 1
fi
echo "iter207 no-science smoke passed"
