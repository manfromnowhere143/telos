# Local Readiness

Commands run on 2026-07-08.

## CodeClash Setup

```bash
/Users/danielwahnich/.local/bin/uv python install 3.11
rm -rf .venv
/Users/danielwahnich/.local/bin/uv sync --python 3.11 --extra dev
```

Result:

```text
Installed Python 3.11.15
Installed 110 packages
```

## CodeClash Unit Smoke

```bash
timeout 12 /Users/danielwahnich/.local/bin/uv run pytest tests/arenas/test_dummy.py -q
```

Result:

```text
9 passed in 0.70s
```

## CodeClash Tournament Attempt

```bash
rm -rf /tmp/telos-codeclash-dummy-smoke
/Users/danielwahnich/.local/bin/uv run codeclash run configs/test/dummy.yaml -o /tmp/telos-codeclash-dummy-smoke
```

Observed partial log:

```text
2026-07-08 13:03:57 [Dummy] DEBUG Checking if container codeclash/dummy exists
```

The command was interrupted after it produced no progress beyond the Docker image check.

## Docker Finding

Static Docker client commands can run through the Docker binary inside `/Applications/Docker.app`:

```text
Docker version 28.2.2, build e6534b4
```

Engine calls timed out:

```bash
timeout 8 /Applications/Docker.app/Contents/Resources/bin/docker info --format '{{.ServerVersion}}'
timeout 8 /Applications/Docker.app/Contents/Resources/bin/docker --context desktop-linux ps
```

Both exited with timeout status `124`. Restarting Docker Desktop may interrupt existing user
containers, so it is not performed silently in this gate.
