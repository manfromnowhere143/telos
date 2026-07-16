from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import re
import subprocess

import pytest


def load_make_handoff_module():
    path = Path(__file__).resolve().parents[1] / "scripts" / "make_handoff.py"
    spec = importlib.util.spec_from_file_location("make_handoff", path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_validate_handoff_module():
    path = Path(__file__).resolve().parents[1] / "scripts" / "validate_handoff.py"
    spec = importlib.util.spec_from_file_location("validate_handoff", path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_normalize_worktree_status_filters_handoff_self_write() -> None:
    make_handoff = load_make_handoff_module()

    assert make_handoff.normalize_worktree_status(" M HANDOFF.md") == "clean"
    assert make_handoff.normalize_worktree_status("M HANDOFF.md") == "clean"
    assert (
        make_handoff.normalize_worktree_status(" M README.md\n M HANDOFF.md")
        == " M README.md"
    )
    assert make_handoff.normalize_worktree_status(" M CONTINUITY.md") == (
        " M CONTINUITY.md"
    )


def test_repository_banner_is_explicit_and_self_contained() -> None:
    make_handoff = load_make_handoff_module()

    banner = make_handoff.repository_banner()
    assert banner == (
        "TELOS is a standalone repository. Resolve its root with "
        "`git rev-parse --show-toplevel`, then run every TELOS command from that root."
    )
    assert ("a" + "web") not in banner.casefold()


def test_active_and_frozen_upstream_gates_are_independently_bound(
    tmp_path: Path, monkeypatch
) -> None:
    make_handoff = load_make_handoff_module()
    monkeypatch.chdir(tmp_path)
    active = "experiments/iter204/HYPOTHESIS.md"
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
    with pytest.raises(RuntimeError, match="frozen upstream gates disagree"):
        make_handoff.active_gate()


def test_operational_handoff_evidence_is_pinned_to_published_runs() -> None:
    make_handoff = load_make_handoff_module()

    assert make_handoff.HARDENING_PULL_REQUEST == 5
    assert (
        make_handoff.HARDENING_MERGE_COMMIT
        == "5c409f79c9333206cff9ed80d59c08aa347110f6"
    )
    assert make_handoff.PRIMARY_CI_RUN_ID == "29460293066"
    assert (
        make_handoff.NODE24_BACKFILL_SOURCE_COMMIT
        == "b4a565d0f0bb61cff460ea4faa51f58e75a2c2fe"
    )
    assert make_handoff.NODE24_BACKFILL_RUN_ID == "29452243832"
    assert make_handoff.ITER203_RUN_ID == "29460393525"
    assert make_handoff.ITER203_RUN_ATTEMPT == "1"
    assert (
        make_handoff.ITER204_MERGE_COMMIT
        == "c1137f896b7ee3c9a26ee35bcda2c5f5c6b79446"
    )
    assert make_handoff.ITER204_PRIMARY_CI_RUN_ID == "29465925393"
    assert make_handoff.ITER204_WORKFLOW_ID == "314113289"
    assert make_handoff.ITER204_FEATURE_PUSH_RUN_ID == "29465584664"
    assert make_handoff.ITER204_PRIMARY_PUSH_RUN_ID == "29465924803"
    assert (
        make_handoff.ITER204_RUNTIME_MANIFEST_SHA256
        == "bf2062825e604d9439b0d29375d7e5219a1064ae4a33701efb74a62f81a59a45"
    )


def test_rendered_handoff_records_the_exact_ordered_operational_gate(
    tmp_path: Path, monkeypatch
) -> None:
    make_handoff = load_make_handoff_module()
    validate_handoff = load_validate_handoff_module()
    source_commit = "b" * 40
    source_branch = "agent/iter205-workflow-context-recovery"
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(make_handoff, "current_branch", lambda: source_branch)
    monkeypatch.setattr(
        make_handoff,
        "source_provenance",
        lambda _branch: (source_branch, source_commit),
    )
    monkeypatch.setattr(make_handoff, "run", lambda _args: "")
    monkeypatch.setattr(
        make_handoff,
        "active_gate",
        lambda: "experiments/iter205_iter204_workflow_context_recovery/HYPOTHESIS.md",
    )
    monkeypatch.setattr(
        make_handoff,
        "frozen_upstream_gate",
        lambda: "experiments/iter202_natural_rate_scaled/HYPOTHESIS.md",
    )
    monkeypatch.setattr(make_handoff, "experiment_status", lambda _gate: [])

    make_handoff.main()
    handoff = (tmp_path / "HANDOFF.md").read_text(encoding="utf-8")

    for evidence in (
        "5c409f79c9333206cff9ed80d59c08aa347110f6",
        "29460293066",
        "b4a565d0f0bb61cff460ea4faa51f58e75a2c2fe",
        "29452243832",
        "access authorization succeeded",
        "`53/53` solver calls",
        "`39/39` eligible scenario calls",
        "`50` model patches",
        "`38` extracted scenario programs",
        "admitted `29` programs and rejected `9` with `21` findings",
        "Zero scenario execution and zero official-harness certification execution occurred",
        "scenario-safety protocol/execution null",
        "workflow run `29460393525`, attempt `1`",
        "execution-infrastructure null",
        "exactly two iter204 workflow records",
        "push parse-failure run `29465584664`",
        "push parse-failure run `29465924803`",
        "zero jobs and zero artifacts",
        "zero `workflow_dispatch` runs",
        "false to say that iter204 has zero workflow runs",
        "at least one locally observed dispatch API request returned HTTP `422`",
        "no run ID, no run attempt, and no public workflow-dispatch job or run log",
        "no provider process, container create/run invocation",
        "contributes no `N`, `k`, or `u`; those quantities are absent, not zero",
        "Never reconstruct that frozen manifest from the current tree",
        "empty complete iter205 all-event and dispatch histories",
        "transient read-only query failure before the request does not consume iter205's request allowance",
        "Once execution reaches the request command, never re-enter this block",
        "discovery poll timeout or temporarily absent run is not by itself a null",
        "No observation ever authorizes another request",
        "closes iter205 and requires iter206",
        'gh workflow run iter205-execute.yml --ref master -f expected_primary_sha="$HEAD_SHA"',
        "actions/workflows/iter205-execute.yml/runs",
        "scripts/collect_iter205_execution.py check",
        "scripts/adjudicate_iter205_workflow_context_recovery.py",
        "scripts/run_iter205_workflow_context_recovery_blind_judge.py",
        "scripts/validate_iter203_infrastructure_null.py",
        "scripts/validate_iter204_pre_dispatch_null.py",
        "scripts/build_iter205_runtime_manifest.py --check",
        "scripts/validate_iter205_publication_safety.py --check",
        "scripts/validate_iter205_runtime_recovery.py",
    ):
        assert evidence in handoff
    assert validate_handoff.recovery_content_failures(handoff) == []

    assert (
        "Active gate: `experiments/iter205_iter204_workflow_context_recovery/HYPOTHESIS.md`"
        in handoff
    )
    assert (
        "Frozen upstream gate recorded by runtime-bound `CONTINUITY.md`: "
        "`experiments/iter202_natural_rate_scaled/HYPOTHESIS.md`"
    ) in handoff
    assert re.search(r"\b[A-Z][A-Z0-9_]*(?:KEY|TOKEN|SECRET)\b", handoff) is None

    next_action_start = handoff.index("- Next action:")
    next_action_end = handoff.index("- Autonomous goal-tracking note:")
    next_action = " ".join(handoff[next_action_start:next_action_end].split())
    ordered_markers = (
        "review the exact iter204 pre-dispatch null",
        "commit the recovery",
        "pull request",
        "green primary-branch CI",
        "preflight authorize one iter205 dispatch request",
    )
    assert [next_action.index(marker) for marker in ordered_markers] == sorted(
        next_action.index(marker) for marker in ordered_markers
    )
    assert "Never dispatch the frozen iter202, iter203, or iter204" in next_action
    dispatch = handoff[handoff.index("## Exact Authorized Iter205 Dispatch") :]
    assert dispatch.index("git switch master") < dispatch.index(
        "gh workflow run iter205-execute.yml"
    )
    assert 'gh run rerun "$RUN_ID"' not in dispatch
    assert "gh workflow run iter203-execute.yml" not in dispatch
    assert "gh workflow run iter204-execute.yml" not in handoff
    assert "## Exact Authorized Iter204 Dispatch" not in handoff
    assert "scripts/collect_iter204_execution.py check" not in handoff
    assert "scripts/adjudicate_iter204_infrastructure_recovery.py" not in handoff
    assert "scripts/run_iter204_infrastructure_recovery_blind_judge.py" not in handoff
    assert handoff.count("gh workflow run iter205-execute.yml") == 1
    bash_blocks = re.findall(r"```bash\n(.*?)\n```", dispatch, re.DOTALL)
    dispatch_block, observe_block, failure_block, success_block, resume_block = bash_blocks[:5]

    assert "iter205-execute\t.github/workflows/iter205-execute.yml\tactive" in dispatch_block
    assert 'test "$ITER205_ALL_COUNT" -eq 0' in dispatch_block
    assert 'test "$ITER205_DISPATCH_COUNT" -eq 0' in dispatch_block
    assert dispatch_block.count("gh workflow run iter205-execute.yml") == 1
    assert dispatch_block.index('test "$ITER205_ALL_COUNT" -eq 0') < dispatch_block.index(
        "gh workflow run iter205-execute.yml"
    )
    assert dispatch_block.index('test "$ITER205_DISPATCH_COUNT" -eq 0') < dispatch_block.index(
        "gh workflow run iter205-execute.yml"
    )
    assert "actions/workflows/314113289/runs" in dispatch_block
    assert "29465584664\tpush\tcompleted\tfailure\t1" in dispatch_block
    assert "29465924803\tpush\tcompleted\tfailure\t1" in dispatch_block
    assert 'test "$ITER204_DISPATCH_COUNT" -eq 0' in dispatch_block
    assert "actions/runs/$ITER204_RUN_ID/jobs" in dispatch_block
    assert "actions/runs/$ITER204_RUN_ID/artifacts" in dispatch_block
    assert "verify py3.11\tcompleted\tsuccess" in dispatch_block
    assert "verify py3.12\tcompleted\tsuccess" in dispatch_block
    head_jq_source = (
        r'".workflow_runs[] | select(.head_sha == \"$HEAD_SHA\") | '
        r'[.id,.status,.conclusion,.event,.head_sha,.run_attempt] | @tsv"'
    )
    assert f"--jq {head_jq_source}" in dispatch_block
    head_jq_semantics = subprocess.run(
        ["bash", "-c", f'HEAD_SHA={"a" * 40}; set -- {head_jq_source}; printf %s "$1"'],
        text=True,
        capture_output=True,
        check=False,
    )
    assert head_jq_semantics.returncode == 0, head_jq_semantics.stderr
    assert head_jq_semantics.stdout == (
        '.workflow_runs[] | select(.head_sha == "' + "a" * 40 + '") | '
        '[.id,.status,.conclusion,.event,.head_sha,.run_attempt] | @tsv'
    )
    assert "printf '%s\\n'" in dispatch_block
    assert "printf '%s\n'" not in dispatch_block
    assert 'test "$ITER205_ALL_COUNT" -eq 1' in dispatch_block
    assert 'test "$ITER205_DISPATCH_COUNT" -eq 1' in dispatch_block
    assert "workflow_dispatch\t" in dispatch_block
    assert "\t1\t.github/workflows/iter205-execute.yml" in dispatch_block
    assert 'gh run watch "$RUN_ID"' not in dispatch_block
    assert 'gh run download "$RUN_ID"' not in dispatch_block
    assert "canonical run discovery is incomplete; never reissue it" in dispatch_block
    assert "exit 75" in dispatch_block
    assert "APPROVED_SHA=%s" in dispatch_block
    assert "actions/workflows/ci.yml/runs" in dispatch_block
    assert (
        'git merge-base --is-ancestor '
        'c1137f896b7ee3c9a26ee35bcda2c5f5c6b79446 "$HEAD_SHA"'
        in dispatch_block
    )

    assert "gh workflow run iter205-execute.yml" not in observe_block
    assert 'gh run watch "$RUN_ID" || true' in observe_block
    assert 'if test "${RUN_STATE%% *}" != completed' in observe_block
    assert 'if test "$RUN_CONCLUSION" != success' in observe_block
    assert "exit 75" in observe_block
    assert "exit 20" in observe_block
    assert 'test "$ITER205_ALL_COUNT" -eq 1' in observe_block
    assert 'test "$ITER205_DISPATCH_COUNT" -eq 1' in observe_block
    assert "iter205-execute\t.github/workflows/iter205-execute.yml\tactive" in observe_block
    assert "verify py3.11\tcompleted\tsuccess" in observe_block
    assert "workflow_dispatch\t" in observe_block
    approved_jq_source = (
        r'".workflow_runs[] | select(.head_sha == \"$APPROVED_SHA\") | '
        r'[.id,.status,.conclusion,.event,.head_sha,.run_attempt] | @tsv"'
    )
    assert f"--jq {approved_jq_source}" in observe_block
    approved_jq_semantics = subprocess.run(
        [
            "bash",
            "-c",
            f'APPROVED_SHA={"c" * 40}; set -- {approved_jq_source}; printf %s "$1"',
        ],
        text=True,
        capture_output=True,
        check=False,
    )
    assert approved_jq_semantics.returncode == 0, approved_jq_semantics.stderr
    assert approved_jq_semantics.stdout == (
        '.workflow_runs[] | select(.head_sha == "' + "c" * 40 + '") | '
        '[.id,.status,.conclusion,.event,.head_sha,.run_attempt] | @tsv'
    )

    assert "gh workflow run iter205-execute.yml" not in failure_block
    assert 'gh run rerun "$RUN_ID"' not in failure_block
    assert 'test "$(gh run view "$RUN_ID" --json attempt --jq \'.attempt\')" -eq 1' in failure_block
    assert 'test "$(gh run view "$RUN_ID" --json status --jq \'.status\')" = completed' in failure_block
    assert 'if test "$RUN_CONCLUSION" = success' in failure_block
    assert 'test "$ITER205_ALL_COUNT" -eq 1' in failure_block
    assert 'test "$ITER205_DISPATCH_COUNT" -eq 1' in failure_block
    assert ".iter205-null-stage.XXXXXX" in failure_block
    assert "! -name SHA256SUMS" in failure_block
    assert failure_block.index('gh run download "$RUN_ID"') < failure_block.index(
        'mv "$STAGE" "$NULL_DIR"'
    )

    assert "gh workflow run iter205-execute.yml" not in success_block
    assert 'test "$(gh run view "$RUN_ID" --json status,conclusion' in success_block
    assert 'test "$RUN_ATTEMPT" -eq 1' in success_block
    assert 'git diff --quiet "$APPROVED_SHA" -- telos scripts' in success_block
    assert "scripts/build_iter205_runtime_manifest.py --check" in success_block
    assert ".iter205-execution-stage.XXXXXX" in success_block
    assert success_block.index('gh run download "$RUN_ID"') < success_block.index(
        "scripts/collect_iter205_execution.py check"
    )
    assert success_block.index("scripts/collect_iter205_execution.py check") < success_block.index(
        'mv "$STAGE" "$EXECUTION_DIR"'
    )
    assert success_block.index('mv "$STAGE" "$EXECUTION_DIR"') < success_block.index(
        "scripts/adjudicate_iter205_workflow_context_recovery.py"
    )

    assert "gh workflow run iter205-execute.yml" not in resume_block
    assert 'gh run download "$RUN_ID"' not in resume_block
    assert 'test -d "$EXECUTION_DIR"' in resume_block
    assert 'test ! -L "$EXECUTION_DIR"' in resume_block
    assert resume_block.index("scripts/collect_iter205_execution.py check") < resume_block.index(
        "scripts/adjudicate_iter205_workflow_context_recovery.py"
    )
    assert resume_block.index("scripts/adjudicate_iter205_workflow_context_recovery.py") < resume_block.index(
        "scripts/run_iter205_workflow_context_recovery_blind_judge.py"
    )
    assert 'scripts/collect_iter205_execution.py check \\\n' in dispatch
    assert '--execution-dir "$STAGE" \\\n' in dispatch
    assert dispatch.index("scripts/adjudicate_iter205_workflow_context_recovery.py") < dispatch.index(
        "scripts/run_iter205_workflow_context_recovery_blind_judge.py"
    )
    assert '"completed success"' in dispatch
    continuation_lines = [line for line in dispatch.splitlines() if line.endswith("\\")]
    assert continuation_lines
    assert all(not line.endswith("\\\\") for line in continuation_lines)
    for block in bash_blocks:
        syntax = subprocess.run(
            ["bash", "-n"],
            input=block,
            text=True,
            capture_output=True,
            check=False,
        )
        assert syntax.returncode == 0, syntax.stderr
    assert ("a" + "web") not in handoff.casefold()


def test_handoff_status_filter_allows_only_its_own_regeneration() -> None:
    validate_handoff = load_validate_handoff_module()

    assert validate_handoff.worktree_changes_except_handoff(" M HANDOFF.md") == []
    assert validate_handoff.worktree_changes_except_handoff("M  HANDOFF.md") == []
    assert validate_handoff.worktree_changes_except_handoff(
        " M HANDOFF.md\n M README.md"
    ) == [" M README.md"]


def test_handoff_recovery_content_rejects_stale_or_identifying_credential_text() -> None:
    validate_handoff = load_validate_handoff_module()
    bounded = "\n".join(validate_handoff.REQUIRED_RECOVERY_FACTS)

    assert validate_handoff.recovery_content_failures(bounded) == []
    assert "HANDOFF.md names a credential variable" in (
        validate_handoff.recovery_content_failures(bounded + "\nPROVIDER_API_KEY")
    )
    assert "HANDOFF.md describes access or account capacity as unavailable" in (
        validate_handoff.recovery_content_failures(bounded + "\nCredentials are missing.")
    )
    assert "HANDOFF.md describes access or account capacity as unavailable" in (
        validate_handoff.recovery_content_failures(bounded + "\nQuota is unavailable.")
    )
    assert "HANDOFF.md names a credential location" in (
        validate_handoff.recovery_content_failures(bounded + "\nUse the credential file.")
    )
    unsafe_dispatch = bounded.replace(
        "Never dispatch the frozen iter202, iter203, or iter204",
        "Dispatch the sealed workflows now.",
    )
    assert (
        "HANDOFF.md is missing bounded recovery fact: "
        "Never dispatch the frozen iter202, iter203, or iter204"
    ) in (
        validate_handoff.recovery_content_failures(unsafe_dispatch)
    )
    assert "HANDOFF.md authorizes a forbidden workflow rerun" in (
        validate_handoff.recovery_content_failures(bounded + '\ngh run rerun "$RUN_ID"')
    )
    assert "HANDOFF.md authorizes the sealed iter203 workflow" in (
        validate_handoff.recovery_content_failures(
            bounded + "\ngh workflow run iter203-execute.yml"
        )
    )
    assert "HANDOFF.md authorizes the sealed iter204 workflow" in (
        validate_handoff.recovery_content_failures(
            bounded + "\ngh workflow run iter204-execute.yml"
        )
    )
    assert "HANDOFF.md must contain exactly one iter205 dispatch command" in (
        validate_handoff.recovery_content_failures(
            bounded + '\ngh workflow run iter205-execute.yml --ref master'
        )
    )
    assert "HANDOFF.md retains stale iter204 operational instruction" in "\n".join(
        validate_handoff.recovery_content_failures(
            bounded + "\nscripts/collect_iter204_execution.py check"
        )
    )


def test_handoff_snapshot_parser_is_exact() -> None:
    validate_handoff = load_validate_handoff_module()

    assert validate_handoff.declared_worktree_changes(
        "# Handoff\n\nWorking tree:\n\n```text\nclean\n```\n"
    ) == []
    assert validate_handoff.declared_worktree_changes(
        "# Handoff\n\nWorking tree:\n\n```text\n M README.md\n?? new.txt\n```\n"
    ) == [" M README.md", "?? new.txt"]
    duplicate = (
        "Working tree:\n\n```text\nclean\n```\n\n"
        "Working tree:\n\n```text\nclean\n```\n"
    )
    with pytest.raises(ValueError, match="exactly one working-tree snapshot"):
        validate_handoff.declared_worktree_changes(duplicate)


def test_handoff_generator_fails_closed_on_git_error(monkeypatch) -> None:
    make_handoff = load_make_handoff_module()

    def failed_run(args, **kwargs):
        return subprocess.CompletedProcess(args, 128, stdout="", stderr="fatal: no repository")

    monkeypatch.setattr(make_handoff.subprocess, "run", failed_run)
    with pytest.raises(RuntimeError, match="exit 128.*fatal: no repository"):
        make_handoff.run(["git", "status", "--short"])


def test_handoff_generator_rejects_detached_head(monkeypatch) -> None:
    make_handoff = load_make_handoff_module()
    monkeypatch.setattr(make_handoff, "run", lambda _args: "HEAD")

    with pytest.raises(RuntimeError, match="cannot generate handoff"):
        make_handoff.current_branch()


def test_handoff_generator_freezes_feature_source_and_preserves_it_on_master(
    tmp_path: Path, monkeypatch
) -> None:
    make_handoff = load_make_handoff_module()
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


def test_declared_branch_parser_is_exact() -> None:
    validate_handoff = load_validate_handoff_module()
    source_commit = "a" * 40
    handoff = """# Handoff

## Repository State

```text
source_branch: agent/research-gate
source_commit: SOURCE_COMMIT
publication_target: master
```
""".replace("SOURCE_COMMIT", source_commit)

    assert validate_handoff.declared_branch(handoff) == "agent/research-gate"
    assert validate_handoff.declared_repository_state(handoff) == {
        "source_branch": "agent/research-gate",
        "source_commit": source_commit,
        "publication_target": "master",
    }
    with pytest.raises(ValueError, match="non-master feature branch"):
        validate_handoff.declared_repository_state(
            handoff.replace("agent/research-gate", "master")
        )
    with pytest.raises(ValueError, match="full lowercase Git commit"):
        validate_handoff.declared_repository_state(
            handoff.replace(source_commit, "a" * 39)
        )
    with pytest.raises(ValueError, match="publication_target must be master"):
        validate_handoff.declared_repository_state(
            handoff.replace("publication_target: master", "publication_target: main")
        )


def test_handoff_validator_fails_closed_on_git_error(monkeypatch) -> None:
    validate_handoff = load_validate_handoff_module()

    def failed_run(args, **kwargs):
        return subprocess.CompletedProcess(args, 128, stdout="", stderr="fatal: no repository")

    monkeypatch.setattr(validate_handoff.subprocess, "run", failed_run)
    with pytest.raises(RuntimeError, match="exit 128.*fatal: no repository"):
        validate_handoff.git_output(["git", "status", "--short"])


def test_handoff_ancestry_distinguishes_miss_from_git_failure(monkeypatch) -> None:
    validate_handoff = load_validate_handoff_module()

    monkeypatch.setattr(
        validate_handoff.subprocess,
        "run",
        lambda *_args, **_kwargs: subprocess.CompletedProcess([], 1, "", ""),
    )
    assert validate_handoff.git_is_ancestor("a" * 40, "b" * 40) is False

    monkeypatch.setattr(
        validate_handoff.subprocess,
        "run",
        lambda *_args, **_kwargs: subprocess.CompletedProcess(
            [], 128, "", "fatal: bad object"
        ),
    )
    with pytest.raises(RuntimeError, match="exit 128.*fatal: bad object"):
        validate_handoff.git_is_ancestor("a" * 40, "b" * 40)


def test_handoff_validator_uses_github_source_branch_on_detached_head(monkeypatch) -> None:
    validate_handoff = load_validate_handoff_module()
    monkeypatch.setattr(validate_handoff, "git_output", lambda _args: "HEAD")
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    monkeypatch.setenv("GITHUB_HEAD_REF", "agent/research-gate")
    monkeypatch.setenv("GITHUB_REF_NAME", "123/merge")

    assert validate_handoff.current_branch() == "agent/research-gate"


def test_handoff_validator_uses_github_push_branch_and_rejects_local_detachment(
    monkeypatch,
) -> None:
    validate_handoff = load_validate_handoff_module()
    monkeypatch.setattr(validate_handoff, "git_output", lambda _args: "HEAD")
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    monkeypatch.delenv("GITHUB_HEAD_REF", raising=False)
    monkeypatch.setenv("GITHUB_REF_NAME", "master")
    assert validate_handoff.current_branch() == "master"

    monkeypatch.delenv("GITHUB_ACTIONS")
    with pytest.raises(RuntimeError, match="cannot verify handoff branch"):
        validate_handoff.current_branch()


def test_publication_lineage_accepts_only_source_or_master_with_ancestry(
    monkeypatch,
) -> None:
    validate_handoff = load_validate_handoff_module()
    source_commit = "a" * 40
    head_commit = "b" * 40
    state = {
        "source_branch": "agent/research-gate",
        "source_commit": source_commit,
        "publication_target": "master",
    }
    monkeypatch.setattr(validate_handoff, "git_output", lambda _args: "")
    monkeypatch.setattr(validate_handoff, "git_is_ancestor", lambda *_args: True)

    assert validate_handoff.publication_lineage_failures(
        state, "agent/research-gate", head_commit
    ) == []
    assert validate_handoff.publication_lineage_failures(
        state, "master", head_commit
    ) == []
    assert validate_handoff.publication_lineage_failures(
        state, "agent/unrelated", head_commit
    ) == [
        "HANDOFF.md branch is outside its publication lineage: "
        "source=agent/research-gate target=master actual=agent/unrelated"
    ]

    monkeypatch.setattr(validate_handoff, "git_is_ancestor", lambda *_args: False)
    assert validate_handoff.publication_lineage_failures(
        state, "master", head_commit
    ) == [
        "HANDOFF.md source_commit is not an ancestor of repository HEAD: "
        f"source_commit={source_commit} HEAD={head_commit}"
    ]


def test_handoff_validator_rejects_declared_branch_mismatch(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    validate_handoff = load_validate_handoff_module()
    gate = tmp_path / "active.md"
    gate.write_text("# Active gate\n", encoding="utf-8")
    frozen_gate = tmp_path / "frozen.md"
    frozen_gate.write_text("# Frozen gate\n", encoding="utf-8")
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
