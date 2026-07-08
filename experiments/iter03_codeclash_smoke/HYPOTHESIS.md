# Iteration 03 - CodeClash Smoke Receipt

Status: pre-registered, result pending.

## Purpose

Run the first real public CodeClash smoke and convert its artifacts into a Telos receipt.

This is still not a model benchmark. The agents are dummy/no-LLM agents. The gate tests whether
Telos can prove a public agent-workflow run from logs, result parsing, and diff-scope evidence.

## Hypothesis

The frozen public slice from `iter02` can produce a valid Telos receipt if the execution
environment can run Docker containers or an explicitly pre-registered isolated sandbox.

## Frozen Slice

- Slice: `codeclash_dummy_swebench_receipt_slice`
- CodeClash commit: `381cdfa05a35e8acd35853b9fc7e13005121b127`
- CodeClash config: `configs/test/dummy.yaml`
- Supporting receipt row: `astropy__astropy-12907`

## Primary Command

From a clean CodeClash checkout at the pinned commit:

```bash
uv run codeclash run configs/test/dummy.yaml -o /tmp/telos-codeclash-dummy-smoke
```

## GitHub Execution Surface

If local Docker remains blocked, run the manual workflow:

```text
.github/workflows/codeclash-smoke.yml
```

The workflow uses Ubuntu Docker, installs `uv`, checks out the pinned CodeClash commit, runs the
CodeClash dummy-arena unit smoke, runs the no-LLM dummy tournament, writes a structured summary,
and uploads the logs as `codeclash-dummy-smoke`.

## Bars

The gate passes only if all hold:

- CodeClash run exits 0.
- Tournament, game, and combined logs are preserved.
- Round results can be parsed into a structured artifact.
- A Telos receipt validates with `python3 scripts/validate_receipts.py`.
- Receipt evidence includes `artifact`, `test`, `diff_scope`, and `adversarial_review`.
- No provider API key is used.
- No model score, CodeClash leaderboard score, or SWE-bench result is claimed.

## Falsifiers

Publish a null or blocked result if:

- Docker engine or sandbox execution cannot run the public config.
- The run requires hidden credentials.
- The run produces logs but no parseable round result.
- The receipt can pass without artifact or diff-scope evidence.
- Any cloud/sandbox spend is used without being recorded in the result.

## Escalation Rule

Local Docker is the first path. If local Docker remains unavailable, an isolated sandbox is allowed
only for this no-LLM smoke and only if the result records the sandbox, command, logs, and cost.

No GPU run is authorized by this gate.
