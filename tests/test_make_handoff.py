from __future__ import annotations

import ast
import importlib.util
import json
from pathlib import Path
import re
import subprocess

import pytest


def load_module(name: str):
    path = Path(__file__).resolve().parents[1] / "scripts" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_normalize_worktree_status_filters_only_handoff_self_write() -> None:
    make_handoff = load_module("make_handoff")

    assert make_handoff.normalize_worktree_status(" M HANDOFF.md") == "clean"
    assert make_handoff.normalize_worktree_status("M  HANDOFF.md") == "clean"
    assert (
        make_handoff.normalize_worktree_status(" M README.md\n M HANDOFF.md")
        == " M README.md"
    )
    assert make_handoff.normalize_worktree_status("?? new.txt") == "?? new.txt"


def test_repository_banner_is_explicit_and_self_contained() -> None:
    make_handoff = load_module("make_handoff")

    assert make_handoff.repository_banner() == (
        "TELOS is a standalone repository. Resolve its root with "
        "`git rev-parse --show-toplevel`, then run every TELOS command from that root."
    )
    assert ("a" + "web") not in make_handoff.repository_banner().casefold()


def test_active_and_frozen_gates_are_independently_bound(
    tmp_path: Path, monkeypatch
) -> None:
    make_handoff = load_module("make_handoff")
    monkeypatch.chdir(tmp_path)
    active = "experiments/iter206/HYPOTHESIS.md"
    frozen = "experiments/iter202/HYPOTHESIS.md"
    for gate in (active, frozen):
        path = tmp_path / gate
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("# Gate\n", encoding="utf-8")
    (tmp_path / "CONTINUITY.md").write_text(
        f"Current gate:\n\n- `{frozen}`\n", encoding="utf-8"
    )
    contract = tmp_path / "mission" / "loop.json"
    contract.parent.mkdir()
    contract.write_text(
        json.dumps({"active_gate": active, "frozen_upstream_gate": frozen}),
        encoding="utf-8",
    )

    assert make_handoff.frozen_upstream_gate() == frozen
    assert make_handoff.active_gate() == active
    contract.write_text(
        json.dumps({"active_gate": active, "frozen_upstream_gate": active}),
        encoding="utf-8",
    )
    with pytest.raises(RuntimeError, match="frozen gates disagree"):
        make_handoff.active_gate()


def test_iter205_and_iter206_operational_anchors_are_exact() -> None:
    make_handoff = load_module("make_handoff")

    assert make_handoff.ITER204_WORKFLOW_ID == "314113289"
    assert make_handoff.ITER204_FEATURE_PUSH_RUN_ID == "29465584664"
    assert make_handoff.ITER204_PRIMARY_PUSH_RUN_ID == "29465924803"
    assert make_handoff.ITER205_PULL_REQUEST == "7"
    assert make_handoff.ITER205_FEATURE_COMMIT == (
        "a336b4909329d392f6db5f6098792e07a17f28cb"
    )
    assert make_handoff.ITER205_MERGE_COMMIT == (
        "4f7dd39bb171fd89c1bb7da3f265aa00aa6df63f"
    )
    assert make_handoff.ITER205_PRIMARY_CI_RUN_ID == "29468769187"
    assert make_handoff.ITER205_WORKFLOW_ID == "314141096"
    assert make_handoff.ITER205_FEATURE_PUSH_RUN_ID == "29468669956"
    assert make_handoff.ITER205_PRIMARY_PUSH_RUN_ID == "29468768706"
    assert make_handoff.ITER206_BRANCH == "agent/iter206-iter205-admission-recovery"


def test_iter206_workflow_authorization_v2_binds_exact_release_ci_pair() -> None:
    root = Path(__file__).resolve().parents[1]
    workflow = (root / ".github/workflows/iter206-execute.yml").read_text(
        encoding="utf-8"
    )
    prefix = workflow.split("concurrency:", 1)[0]
    inputs = re.findall(r"^      ([a-z0-9_]+):\n        description:", prefix, re.MULTILINE)
    assert inputs == [
        "expected_primary_sha",
        "expected_workflow_id",
        "expected_iter204_release_run_id",
        "expected_iter204_primary_run_id",
    ]

    lines = workflow.splitlines()
    start = next(i for i, line in enumerate(lines) if line == "          import base64")
    end = next(i for i, line in enumerate(lines[start:], start) if line == "          PY")
    source = "\n".join(line[10:] for line in lines[start:end]) + "\n"
    module = ast.parse(source)

    authorization = next(
        node.value
        for node in ast.walk(module)
        if isinstance(node, ast.Assign)
        and any(isinstance(target, ast.Name) and target.id == "authorization" for target in node.targets)
    )
    assert isinstance(authorization, ast.Dict)
    authorization_fields = {
        ast.literal_eval(key): value
        for key, value in zip(authorization.keys, authorization.values, strict=True)
    }
    assert set(authorization_fields) == {
        "approved_commit_sha",
        "current_run_attempt",
        "current_run_id",
        "iter204_admission_history_sha256",
        "iter204_dispatch_count",
        "iter204_primary_run_id",
        "iter204_release_run_id",
        "iter204_workflow_id",
        "iter205_all_event_count",
        "iter205_dispatch_count",
        "iter205_workflow_id",
        "iter206_workflow_id",
        "merge_first_parent",
        "merge_second_parent",
        "primary_ci_event",
        "primary_ci_head_branch",
        "primary_ci_run_attempt",
        "primary_ci_run_id",
        "primary_ci_workflow_path",
        "release_ci_head_sha",
        "release_ci_runs",
        "required_checks",
        "schema_version",
    }
    assert ast.literal_eval(authorization_fields["schema_version"]) == (
        "telos.iter206.primary_ci_authorization.v2"
    )

    release_function = next(
        node
        for node in module.body
        if isinstance(node, ast.FunctionDef) and node.name == "exact_release_ci_run"
    )
    run_keys = {
        "conclusion",
        "event",
        "head_branch",
        "head_repository",
        "head_sha",
        "id",
        "path",
        "required_jobs",
        "run_attempt",
        "status",
    }
    job_keys = {
        "conclusion",
        "head_sha",
        "id",
        "name",
        "run_attempt",
        "status",
    }
    dict_key_sets = []
    for node in ast.walk(release_function):
        if isinstance(node, ast.Dict) and all(
            isinstance(key, ast.Constant) and isinstance(key.value, str)
            for key in node.keys
        ):
            dict_key_sets.append({key.value for key in node.keys})
    assert run_keys in dict_key_sets
    assert job_keys in dict_key_sets
    assert {"full_name"} in dict_key_sets
    assert 'head_repository = row.get("head_repository")' in source
    assert 'head_repository.get("full_name") != repository' in source
    assert 'len({job["id"] for job in required_jobs}) != 2' in source
    assert 'selected_checks[0]["id"] == selected_checks[1]["id"]' in source

    release_assignment = next(
        node.value
        for node in module.body
        if isinstance(node, ast.Assign)
        and any(
            isinstance(target, ast.Name) and target.id == "release_ci_runs"
            for target in node.targets
        )
    )
    assert isinstance(release_assignment, ast.List)
    assert [ast.literal_eval(call.args[0]) for call in release_assignment.elts] == [
        "push",
        "pull_request",
    ]

    old = (root / ".github/workflows/iter205-execute.yml").read_text(encoding="utf-8")
    old_tail = "  smoke:\n" + old.split("  smoke:\n", 1)[1]
    new_tail = "  smoke:\n" + workflow.split("  smoke:\n", 1)[1]
    normalized = (
        new_tail.replace(
            "iter206_iter205_admission_history_recovery",
            "iter205_iter204_workflow_context_recovery",
        )
        .replace("ITER206", "ITER205")
        .replace("iter206", "iter205")
    )
    assert normalized == old_tail


def test_rendered_handoff_is_exact_six_fail_closed_and_single_dispatch(
    tmp_path: Path, monkeypatch
) -> None:
    make_handoff = load_module("make_handoff")
    validate_handoff = load_module("validate_handoff")
    source_commit = "b" * 40
    source_branch = "agent/iter206-iter205-admission-recovery"
    active = "experiments/iter206_iter205_admission_history_recovery/HYPOTHESIS.md"
    frozen = "experiments/iter202_natural_rate_scaled/HYPOTHESIS.md"
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(make_handoff, "current_branch", lambda: source_branch)
    monkeypatch.setattr(
        make_handoff,
        "source_provenance",
        lambda _branch: (source_branch, source_commit),
    )
    monkeypatch.setattr(make_handoff, "run", lambda _args: "")
    monkeypatch.setattr(make_handoff, "active_gate", lambda: active)
    monkeypatch.setattr(make_handoff, "frozen_upstream_gate", lambda: frozen)
    monkeypatch.setattr(make_handoff, "experiment_status", lambda _gate: [])

    make_handoff.main()
    handoff = (tmp_path / "HANDOFF.md").read_text(encoding="utf-8")

    assert validate_handoff.recovery_content_failures(handoff) == []
    assert make_handoff.repository_banner() in handoff
    assert f"Active gate: `{active}`" in handoff
    assert (
        "Frozen upstream gate recorded by runtime-bound `CONTINUITY.md`: "
        f"`{frozen}`"
    ) in handoff
    assert "two-row closure snapshot" in handoff
    assert "four-row iter205 admission baseline" in handoff
    assert "No iter205 dispatch request was issued" in handoff
    assert "pre-dispatch admission-history null" in handoff
    assert "no dispatch API response or rejection exists" in handoff
    assert "`1/24` confirmed lower, `7/24` worst-case missing upper" in handoff
    assert "`1/18` complete-case" in handoff
    assert (
        "No credential, credit, billing, quota, or authentication deficit is the "
        "iter205/iter206 blocker"
    ) in handoff
    assert "## Iter206 Local Seal and Exact Pickup Boundary" in handoff
    assert "source commit A" in handoff
    assert "publication-safety receipt and then the runtime manifest" in handoff
    assert "seal commit B" in handoff
    assert "push A and B together" in handoff
    assert "Never regenerate it after that point" in handoff
    assert "Push branch `agent/iter206-iter205-admission-recovery` exactly once" in handoff
    assert "Merge exactly once with a two-parent merge commit" in handoff
    assert ("a" + "web") not in handoff.casefold()
    assert re.search(r"\b[A-Z][A-Z0-9_]*(?:KEY|TOKEN|SECRET)\b", handoff) is None

    assert handoff.count("gh workflow run iter206-execute.yml") == 1
    assert "gh workflow run iter205-execute.yml" not in handoff
    assert "gh workflow run iter204-execute.yml" not in handoff
    assert 'gh run rerun "$RUN_ID"' not in handoff
    assert "scripts/collect_iter205_execution.py check" not in handoff

    dispatch_text = handoff[handoff.index("## Exact Authorized Iter206 Dispatch") :]
    bash_blocks = re.findall(r"```bash\n(.*?)\n```", dispatch_text, re.DOTALL)
    assert len(bash_blocks) == 6
    dispatch, observe, failure, success, resume, verification = bash_blocks

    assert dispatch.count("gh workflow run iter206-execute.yml") == 1
    for required_input in validate_handoff.ITER206_INPUTS:
        assert dispatch.count(required_input) == 1
    assert 'test "$ITER205_ALL_COUNT" -eq 0' in dispatch
    assert 'test "$ITER205_DISPATCH_COUNT" -eq 0' in dispatch
    assert 'test "$ITER206_ALL_COUNT" -eq 0' in dispatch
    assert 'test "$ITER206_DISPATCH_COUNT" -eq 0' in dispatch
    assert "actions/workflows/314113289/runs" in dispatch
    assert "1\t29465584664\t314113289" in dispatch
    assert "2\t29465924803\t314113289" in dispatch
    assert "3\t29468669956\t314113289" in dispatch
    assert "4\t29468768706\t314113289" in dispatch
    assert "agent/iter206-iter205-admission-recovery" in dispatch
    assert "actions/runs/$ITER204_RUN_ID/attempts/1/jobs" in dispatch
    assert "actions/runs/$ITER204_RUN_ID/artifacts" in dispatch
    assert "grep -E 'HTTP[^0-9]*404'" in dispatch
    assert "verify py3.11\tsuccess" in dispatch
    assert "verify py3.12\tsuccess" in dispatch
    assert dispatch.count("verify_release_ci()") == 1
    assert dispatch.count('RELEASE_PUSH_CI_RUN_ID="$(verify_release_ci push)"') == 1
    assert (
        dispatch.count(
            'RELEASE_PULL_REQUEST_CI_RUN_ID="$(verify_release_ci pull_request)"'
        )
        == 1
    )
    assert '-f head_sha="$SECOND_PARENT"' in dispatch
    assert ".head_repository.full_name] | @tsv" in dispatch
    assert "completed\tmanfromnowhere143/telos" in dispatch
    assert "verify py3.11\tsuccess\t" in dispatch
    assert "verify py3.12\tsuccess\t" in dispatch
    assert "[.total_count, (.workflow_runs | length)] | @tsv" in dispatch
    assert "[.total_count, (.jobs | length)] | @tsv" in dispatch
    assert ".status,.html_url] | @tsv" in dispatch
    assert (
        'test "$html_url" = "https://github.com/$REPO/actions/runs/$run_id/job/$job_id"'
        in dispatch
    )
    assert "repos/$REPO/commits/$HEAD_SHA/check-runs" in dispatch
    assert "PRIMARY_CHECK_HISTORY_COMPLETE" in dispatch
    assert 'PRIMARY_PY311_CHECK_ID="$(verify_primary_check \'verify py3.11\')"' in dispatch
    assert 'PRIMARY_PY312_CHECK_ID="$(verify_primary_check \'verify py3.12\')"' in dispatch
    assert "github-actions" in dispatch
    assert 'test "$RELEASE_PUSH_CI_RUN_ID" != "$RELEASE_PULL_REQUEST_CI_RUN_ID"' in dispatch
    assert 'test "$FIRST_PARENT" = "4f7dd39bb171fd89c1bb7da3f265aa00aa6df63f"' in dispatch
    assert dispatch.index("scripts/validate_iter205_pre_dispatch_null.py") < dispatch.index(
        "gh workflow run iter206-execute.yml"
    )
    assert dispatch.index('test "$ITER204_HISTORY" = "$EXPECTED_ITER204_HISTORY"') < dispatch.index(
        "gh workflow run iter206-execute.yml"
    )
    assert dispatch.index('RELEASE_PUSH_CI_RUN_ID="$(verify_release_ci push)"') < dispatch.index(
        "gh workflow run iter206-execute.yml"
    )
    assert dispatch.index(
        'RELEASE_PULL_REQUEST_CI_RUN_ID="$(verify_release_ci pull_request)"'
    ) < dispatch.index("gh workflow run iter206-execute.yml")
    assert dispatch.index("verify py3.12") < dispatch.index(
        "gh workflow run iter206-execute.yml"
    )
    assert 'gh run watch "$RUN_ID"' not in dispatch
    assert 'gh run download "$RUN_ID"' not in dispatch
    assert "run discovery is incomplete; never reissue it" in dispatch
    assert "\t.github/workflows/iter206-execute.yml\t1\t1" in dispatch

    assert "gh workflow run iter206-execute.yml" not in observe
    assert 'gh run watch "$RUN_ID" || true' in observe
    assert 'test "$ITER206_ALL_COUNT" -eq 1' in observe
    assert 'test "$ITER206_DISPATCH_COUNT" -eq 1' in observe
    assert 'if test "${RUN_STATE%% *}" != completed' in observe
    assert "repeat only this read-only observation block" in observe
    assert "exit 75" in observe
    assert "exit 20" in observe

    assert "gh workflow run iter206-execute.yml" not in failure
    assert 'gh run rerun "$RUN_ID"' not in failure
    assert ".iter206-null-stage.XXXXXX" in failure
    assert "! -name SHA256SUMS" in failure
    assert failure.index('gh run download "$RUN_ID"') < failure.index(
        'mv "$STAGE" "$NULL_DIR"'
    )

    assert "gh workflow run iter206-execute.yml" not in success
    assert ".iter206-execution-stage.XXXXXX" in success
    assert success.index('gh run download "$RUN_ID"') < success.index(
        "scripts/collect_iter206_execution.py check"
    )
    assert success.index("scripts/collect_iter206_execution.py check") < success.index(
        'mv "$STAGE" "$EXECUTION_DIR"'
    )
    assert success.index('mv "$STAGE" "$EXECUTION_DIR"') < success.index(
        "scripts/adjudicate_iter206_admission_history_recovery.py"
    )

    assert 'gh run download "$RUN_ID"' not in resume
    assert 'test -d "$EXECUTION_DIR"' in resume
    assert resume.index("scripts/collect_iter206_execution.py check") < resume.index(
        "scripts/adjudicate_iter206_admission_history_recovery.py"
    )
    assert resume.index("scripts/adjudicate_iter206_admission_history_recovery.py") < resume.index(
        "scripts/run_iter206_admission_history_recovery_blind_judge.py"
    )
    assert "scripts/validate_iter205_pre_dispatch_null.py" in verification
    assert "scripts/build_iter206_runtime_manifest.py --check" in verification
    assert "scripts/validate_handoff.py" in verification
    assert "python3 scripts/make_handoff.py" not in verification

    continuation_lines = [line for line in dispatch_text.splitlines() if line.endswith("\\")]
    assert continuation_lines
    assert all(not line.endswith("\\\\") for line in continuation_lines)
    for block in bash_blocks:
        syntax = subprocess.run(
            ["bash", "-n"], input=block, text=True, capture_output=True, check=False
        )
        assert syntax.returncode == 0, syntax.stderr


def test_handoff_recovery_guard_rejects_retry_stale_and_credential_text() -> None:
    make_handoff = load_module("make_handoff")
    validate_handoff = load_module("validate_handoff")
    bounded = make_handoff.render_handoff(
        generated="2026-07-16T00:00:00Z",
        source_branch="agent/iter206-iter205-admission-recovery",
        source_commit="a" * 40,
        worktree="clean",
        experiments="- bounded fixture",
        gate="experiments/iter206_iter205_admission_history_recovery/HYPOTHESIS.md",
        upstream_gate="experiments/iter202_natural_rate_scaled/HYPOTHESIS.md",
    )

    assert validate_handoff.recovery_content_failures(bounded) == []
    assert "HANDOFF.md names a credential variable" in (
        validate_handoff.recovery_content_failures(bounded + "\nPROVIDER_API_KEY")
    )
    assert "HANDOFF.md describes account or execution capacity as unavailable" in (
        validate_handoff.recovery_content_failures(bounded + "\nCredits are missing.")
    )
    assert "HANDOFF.md names a credential location" in (
        validate_handoff.recovery_content_failures(bounded + "\nUse the credential file.")
    )
    assert "HANDOFF.md authorizes a forbidden workflow rerun" in (
        validate_handoff.recovery_content_failures(bounded + '\ngh run rerun "$RUN_ID"')
    )
    assert "HANDOFF.md authorizes the sealed iter205 workflow" in (
        validate_handoff.recovery_content_failures(
            bounded + "\ngh workflow run iter205-execute.yml"
        )
    )
    assert "HANDOFF.md must contain exactly one iter206 dispatch command" in (
        validate_handoff.recovery_content_failures(
            bounded + "\ngh workflow run iter206-execute.yml"
        )
    )
    assert "HANDOFF.md must bind exactly one iter206 dispatch input" in "\n".join(
        validate_handoff.recovery_content_failures(
            bounded + '\n-f expected_primary_sha="$HEAD_SHA"'
        )
    )
    assert "HANDOFF.md retains stale iter205 operational instruction" in "\n".join(
        validate_handoff.recovery_content_failures(
            bounded + "\nscripts/collect_iter205_execution.py check"
        )
    )


def test_handoff_status_parsers_are_exact() -> None:
    validate_handoff = load_module("validate_handoff")

    assert validate_handoff.worktree_changes_except_handoff(" M HANDOFF.md") == []
    assert validate_handoff.worktree_changes_except_handoff(
        " M HANDOFF.md\n M README.md"
    ) == [" M README.md"]
    assert validate_handoff.declared_worktree_changes(
        "Working tree:\n\n```text\nclean\n```\n"
    ) == []
    assert validate_handoff.declared_worktree_changes(
        "Working tree:\n\n```text\n M README.md\n?? new.txt\n```\n"
    ) == [" M README.md", "?? new.txt"]
    with pytest.raises(ValueError, match="exactly one working-tree snapshot"):
        validate_handoff.declared_worktree_changes(
            "Working tree:\n\n```text\nclean\n```\n" * 2
        )


def test_handoff_generator_and_validator_fail_closed_on_git_errors(monkeypatch) -> None:
    make_handoff = load_module("make_handoff")
    validate_handoff = load_module("validate_handoff")

    def failed_run(args, **kwargs):
        return subprocess.CompletedProcess(args, 128, stdout="", stderr="fatal: no repository")

    monkeypatch.setattr(make_handoff.subprocess, "run", failed_run)
    with pytest.raises(RuntimeError, match="exit 128.*fatal: no repository"):
        make_handoff.run(["git", "status", "--short"])
    monkeypatch.setattr(validate_handoff.subprocess, "run", failed_run)
    with pytest.raises(RuntimeError, match="exit 128.*fatal: no repository"):
        validate_handoff.git_output(["git", "status", "--short"])


def test_source_provenance_freezes_feature_and_preserves_it_on_master(
    tmp_path: Path, monkeypatch
) -> None:
    make_handoff = load_module("make_handoff")
    source_commit = "a" * 40
    monkeypatch.setattr(make_handoff, "current_commit", lambda: source_commit)
    assert make_handoff.source_provenance("agent/research-gate") == (
        "agent/research-gate",
        source_commit,
    )
    monkeypatch.chdir(tmp_path)
    (tmp_path / "HANDOFF.md").write_text(
        "source_branch: agent/research-gate\n"
        f"source_commit: {source_commit}\n"
        "publication_target: master\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(
        make_handoff.subprocess,
        "run",
        lambda *_args, **_kwargs: subprocess.CompletedProcess([], 0, "", ""),
    )
    assert make_handoff.source_provenance("master") == (
        "agent/research-gate",
        source_commit,
    )
    monkeypatch.setattr(
        make_handoff.subprocess,
        "run",
        lambda *_args, **_kwargs: subprocess.CompletedProcess([], 1, "", ""),
    )
    with pytest.raises(RuntimeError, match="not an ancestor"):
        make_handoff.source_provenance("master")


def test_declared_repository_state_and_publication_lineage_are_exact(monkeypatch) -> None:
    validate_handoff = load_module("validate_handoff")
    source_commit = "a" * 40
    handoff = f"""## Repository State

```text
source_branch: agent/research-gate
source_commit: {source_commit}
publication_target: master
```
"""
    state = validate_handoff.declared_repository_state(handoff)
    assert state == {
        "source_branch": "agent/research-gate",
        "source_commit": source_commit,
        "publication_target": "master",
    }
    with pytest.raises(ValueError, match="non-master feature branch"):
        validate_handoff.declared_repository_state(
            handoff.replace("agent/research-gate", "master")
        )
    monkeypatch.setattr(validate_handoff, "git_output", lambda _args: "")
    monkeypatch.setattr(validate_handoff, "git_is_ancestor", lambda *_args: True)
    assert validate_handoff.publication_lineage_failures(
        state, "agent/research-gate", "b" * 40
    ) == []
    assert validate_handoff.publication_lineage_failures(
        state, "master", "b" * 40
    ) == []
    assert "actual=agent/unrelated" in validate_handoff.publication_lineage_failures(
        state, "agent/unrelated", "b" * 40
    )[0]


def test_validator_main_rejects_publication_lineage_mismatch(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    validate_handoff = load_module("validate_handoff")
    (tmp_path / "active.md").write_text("# Active\n", encoding="utf-8")
    (tmp_path / "frozen.md").write_text("# Frozen\n", encoding="utf-8")
    continuity = tmp_path / "CONTINUITY.md"
    continuity.write_text("Current gate:\n\n- `frozen.md`\n", encoding="utf-8")
    contract = tmp_path / "mission" / "loop.json"
    contract.parent.mkdir()
    contract.write_text(
        json.dumps({"active_gate": "active.md", "frozen_upstream_gate": "frozen.md"}),
        encoding="utf-8",
    )
    facts = "\n".join(validate_handoff.REQUIRED_RECOVERY_FACTS)
    handoff = tmp_path / "HANDOFF.md"
    handoff.write_text(
        f"""# Handoff

{validate_handoff.REPOSITORY_DECLARATION}

## Repository State

```text
source_branch: declared-branch
source_commit: {"a" * 40}
publication_target: master
```

Working tree:

```text
clean
```

Active gate: `active.md`
Frozen upstream gate recorded by runtime-bound `CONTINUITY.md`: `frozen.md`

{facts}
""",
        encoding="utf-8",
    )
    monkeypatch.setattr(validate_handoff, "ROOT", tmp_path)
    monkeypatch.setattr(validate_handoff, "HANDOFF", handoff)
    monkeypatch.setattr(validate_handoff, "CONTINUITY", continuity)
    monkeypatch.setattr(validate_handoff, "MISSION_CONTRACT", contract)
    monkeypatch.setattr(validate_handoff, "current_branch", lambda: "actual-branch")
    monkeypatch.setattr(validate_handoff, "current_commit", lambda: "b" * 40)
    monkeypatch.setattr(validate_handoff, "git_is_ancestor", lambda *_args: True)
    monkeypatch.setattr(validate_handoff, "git_output", lambda _args: "")

    assert validate_handoff.main() == 1
    assert "source=declared-branch target=master actual=actual-branch" in (
        capsys.readouterr().out
    )
