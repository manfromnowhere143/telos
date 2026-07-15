from __future__ import annotations

from contextlib import contextmanager
import importlib.util
import json
from pathlib import Path
import shutil
from types import SimpleNamespace
from typing import Any

import pytest


ROOT = Path(__file__).resolve().parents[1]
TEST_RUNTIME_MANIFEST_SHA256 = "f" * 64


def load_judge(module_name: str):
    path = ROOT / "scripts/run_iter200_blind_judge.py"
    spec = importlib.util.spec_from_file_location(module_name, path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_adjudicator(module_name: str):
    path = ROOT / "scripts/adjudicate_iter200.py"
    spec = importlib.util.spec_from_file_location(module_name, path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def candidate() -> dict[str, str]:
    return {
        "gold_result": "gold output",
        "instance_id": "demo__demo-1",
        "model_result": "model output",
        "repo": "demo/demo",
    }


def snapshot_row() -> dict[str, str]:
    return {
        "instance_id": "demo__demo-1",
        "problem_statement": "Fix the demonstrated bug.",
        "repo": "demo/demo",
    }


def configure(
    judge: Any, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> tuple[Path, list[dict[str, str]], dict[str, dict[str, str]]]:
    experiment = tmp_path / "experiments" / judge.ITER202_EXP
    proof = experiment / "proof"
    proof.mkdir(parents=True)
    monkeypatch.setattr(judge, "ROOT", tmp_path)
    monkeypatch.setattr(judge, "EXP", experiment)
    monkeypatch.setattr(judge, "PROOF", proof)
    candidates = [candidate()]
    rows = {"demo__demo-1": snapshot_row()}
    return experiment, candidates, rows


def set_test_keys(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "openai-test-key")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "anthropic-test-key")


def clear_test_keys(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)


def write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


class InjectedCrash(RuntimeError):
    pass


@pytest.mark.parametrize("verdict", ["A", "B", "neither", "both"])
def test_strict_parser_accepts_only_the_exact_one_key_string_enum(
    verdict: str,
) -> None:
    judge = load_judge(f"judge_strict_parser_{verdict}")
    assert judge.parse(json.dumps({"wrong": verdict})) == verdict


@pytest.mark.parametrize(
    "text",
    [
        "true",
        "[]",
        '{"wrong":true}',
        '{"wrong":"invalid"}',
        '{"wrong":"A","extra":1}',
        '{"wrong":"A","wrong":"B"}',
        'answer: {"wrong":"A"}',
        '```json\n{"wrong":"A"}\n```',
        '{"wrong":"A"}{"wrong":"B"}',
        '{"wrong":"A","number":NaN}',
    ],
)
def test_strict_parser_rejects_wrappers_extra_keys_duplicates_and_non_enum_values(
    text: str,
) -> None:
    judge = load_judge("judge_strict_parser_invalid")
    assert judge.parse(text) == "unparseable"


@pytest.mark.parametrize(
    "name",
    ["TELOS_NAT_JUDGE_PARSER_RULE", "TELOS_NAT_JUDGE_DECISION_RULE"],
)
def test_parser_and_decision_rule_overrides_are_rejected(
    monkeypatch: pytest.MonkeyPatch, name: str
) -> None:
    judge = load_judge(f"judge_rule_override_{name}")
    monkeypatch.setenv(name, "changed")
    with pytest.raises(SystemExit, match="does not accept environment overrides"):
        judge.reject_judge_configuration_overrides()


def test_crash_after_both_raw_checkpoints_resumes_without_credentials_or_calls(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    judge = load_judge("judge_checkpoint_crash_resume")
    experiment, candidates, rows = configure(judge, monkeypatch, tmp_path)
    set_test_keys(monkeypatch)
    calls: list[tuple[str, str]] = []
    checkpoints = 0
    parse_calls = 0
    real_parse = judge.parse

    def tracked_parse(text: str) -> str:
        nonlocal parse_calls
        parse_calls += 1
        return real_parse(text)

    def openai(prompt: str, key: str) -> str:
        calls.append(("openai", prompt))
        assert key == "openai-test-key"
        return '{"wrong":"A"}'

    def anthropic(prompt: str, key: str) -> str:
        assert (
            len(list((experiment / "proof/raw/judge_provider_attempts").glob("*.parsed.json"))) == 1
        )
        calls.append(("anthropic", prompt))
        assert key == "anthropic-test-key"
        return '{"wrong":"B"}'

    def crash_after_second() -> None:
        nonlocal checkpoints
        checkpoints += 1
        if checkpoints == 2:
            raise InjectedCrash("after both exact response checkpoints")

    monkeypatch.setattr(judge, "call_openai", openai)
    monkeypatch.setattr(judge, "call_anthropic", anthropic)
    monkeypatch.setattr(judge, "parse", tracked_parse)
    monkeypatch.setattr(judge, "_after_judge_attempt_checkpoint", crash_after_second)
    with pytest.raises(InjectedCrash, match="exact response checkpoints"):
        judge._run_iter202_judge_attempts(candidates, rows, TEST_RUNTIME_MANIFEST_SHA256)

    attempt_dir = experiment / "proof/raw/judge_provider_attempts"
    started_paths = sorted(attempt_dir.glob("*.started.json"))
    finished_paths = sorted(attempt_dir.glob("*.finished.json"))
    parsed_paths = sorted(attempt_dir.glob("*.parsed.json"))
    assert len(started_paths) == len(finished_paths) == 2
    assert len(parsed_paths) == 1
    started = [json.loads(path.read_text()) for path in started_paths]
    finished = [json.loads(path.read_text()) for path in finished_paths]
    assert [row["provider"] for row in started] == ["openai", "anthropic"]
    assert [row["sequence"] for row in started] == [1, 2]
    assert all(row["schema_version"] == judge.JUDGE_STARTED_SCHEMA for row in started)
    assert all(row["runtime_manifest_sha256"] == TEST_RUNTIME_MANIFEST_SHA256 for row in started)
    assert all(
        row["accounting"] == {"estimated_spend_usd": 0.06, "provider_calls": 1} for row in started
    )
    assert started[0]["endpoint"] == judge.OPENAI_JUDGE_ENDPOINT
    assert started[0]["model"] == "gpt-5.6-terra"
    assert started[0]["api_version"] is None
    assert started[0]["token_limit_field"] == "max_completion_tokens"
    assert started[0]["token_limit_value"] == 1536
    assert started[1]["endpoint"] == judge.ANTHROPIC_JUDGE_ENDPOINT
    assert started[1]["model"] == "claude-opus-4-8"
    assert started[1]["api_version"] == "2023-06-01"
    assert started[1]["token_limit_field"] == "max_tokens"
    assert started[1]["token_limit_value"] == 400
    assert all(row["temperature_omitted"] is True for row in started)
    assert all(
        row["candidate_evidence_sha256"] == judge.candidate_evidence_sha256(candidates[0])
        for row in started
    )
    assert started[0]["mapping"] == started[1]["mapping"]
    assert started[0]["model_slot"] == started[1]["model_slot"]
    assert started[0]["prompt_sha256"] == started[1]["prompt_sha256"]
    assert all(
        row["parser_contract_sha256"] == judge.JUDGE_PARSER_CONTRACT_SHA256
        and row["decision_contract_sha256"] == judge.JUDGE_DECISION_CONTRACT_SHA256
        for row in started
    )
    assert all(row["outcome"] == "response" for row in finished)
    assert finished[0]["raw_response"] == '{"wrong":"A"}'
    assert finished[1]["raw_response"] == '{"wrong":"B"}'
    assert not (experiment / "proof/blind_judge_verdicts.json").exists()
    assert parse_calls == 1

    clear_test_keys(monkeypatch)
    monkeypatch.setattr(judge, "_after_judge_attempt_checkpoint", lambda: None)
    monkeypatch.setattr(
        judge,
        "_judge_provider_key",
        lambda *_args: (_ for _ in ()).throw(AssertionError("resume read a key")),
    )
    monkeypatch.setattr(
        judge,
        "_call_frozen_judge_provider",
        lambda *_args: (_ for _ in ()).throw(AssertionError("duplicate judge call")),
    )
    verdicts, bundle, retained_calls, retained_est, new_calls, new_est = (
        judge._run_iter202_judge_attempts(candidates, rows, TEST_RUNTIME_MANIFEST_SHA256)
    )
    assert len(calls) == 2
    # Resume revalidates the retained first decision and parses the second retained raw response.
    assert parse_calls == 3
    parsed_rows = [
        json.loads(path.read_text()) for path in sorted(attempt_dir.glob("*.parsed.json"))
    ]
    assert [row["decision"] for row in parsed_rows] == ["A", "B"]
    assert all(len(row["finished_record_sha256"]) == 64 for row in parsed_rows)
    assert len(verdicts) == 1
    assert verdicts[0]["gpt_verdict"] == "A"
    assert verdicts[0]["opus_verdict"] == "B"
    assert retained_calls == 2
    assert retained_est == 0.12
    assert new_calls == 0
    assert new_est == 0.0
    assert bundle["checkpoint_evidence"] == {
        "attempts_finished": 2,
        "attempts_parsed": 2,
        "attempts_started": 2,
        "evidence_sha256": bundle["checkpoint_evidence"]["evidence_sha256"],
        "finished_schema": judge.JUDGE_FINISHED_SCHEMA,
        "parsed_schema": judge.JUDGE_PARSED_SCHEMA,
        "provider_errors": 0,
        "responses": 2,
        "started_schema": judge.JUDGE_STARTED_SCHEMA,
    }
    assert len(bundle["checkpoint_evidence"]["evidence_sha256"]) == 64


def test_error_metadata_is_bounded_hashed_and_redacts_all_loaded_credentials(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    judge = load_judge("judge_checkpoint_bounded_error")
    _experiment, candidates, rows = configure(judge, monkeypatch, tmp_path)
    spec = judge._judge_attempt_specs(candidates, rows, TEST_RUNTIME_MANIFEST_SHA256)[0][0]
    started = judge._judge_started_record(spec)
    error = RuntimeError("A" * 5000 + " openai-secret anthropic-secret")
    finished = judge._judge_finished_error_record(
        started, error, ("openai-secret", "anthropic-secret")
    )
    metadata = finished["error"]
    assert metadata["message_truncated"] is True
    assert len(metadata["message"]) == 4096
    assert "openai-secret" not in json.dumps(finished)
    assert "anthropic-secret" not in json.dumps(finished)
    assert len(metadata["message_sha256"]) == 64
    assert len(metadata["retained_message_sha256"]) == 64


def test_provider_error_is_redacted_checkpointed_counted_and_never_retried(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    judge = load_judge("judge_checkpoint_error_resume")
    experiment, candidates, rows = configure(judge, monkeypatch, tmp_path)
    set_test_keys(monkeypatch)
    provider_calls = 0

    def fail_openai(_prompt: str, _key: str) -> str:
        nonlocal provider_calls
        provider_calls += 1
        raise RuntimeError("transport exposed openai-test-key")

    def pass_anthropic(_prompt: str, _key: str) -> str:
        nonlocal provider_calls
        provider_calls += 1
        return '{"wrong":"neither"}'

    monkeypatch.setattr(judge, "call_openai", fail_openai)
    monkeypatch.setattr(judge, "call_anthropic", pass_anthropic)
    result = judge._run_iter202_judge_attempts(candidates, rows, TEST_RUNTIME_MANIFEST_SHA256)
    verdicts, bundle, retained_calls, retained_est, new_calls, new_est = result
    assert provider_calls == 2
    assert retained_calls == 0
    assert retained_est == 0.0
    assert new_calls == 2
    assert new_est == 0.12
    assert verdicts[0]["gpt_verdict"] == "provider_error"
    assert verdicts[0]["opus_verdict"] == "neither"
    assert bundle["checkpoint_evidence"]["provider_errors"] == 1

    error_path = next(
        path
        for path in (experiment / "proof/raw/judge_provider_attempts").glob("*.finished.json")
        if json.loads(path.read_text())["outcome"] == "provider_error"
    )
    error_text = error_path.read_text()
    assert "openai-test-key" not in error_text
    assert "[REDACTED]" in error_text

    clear_test_keys(monkeypatch)
    monkeypatch.setattr(
        judge,
        "_call_frozen_judge_provider",
        lambda *_args: (_ for _ in ()).throw(AssertionError("error was retried")),
    )
    resumed = judge._run_iter202_judge_attempts(candidates, rows, TEST_RUNTIME_MANIFEST_SHA256)
    assert provider_calls == 2
    assert resumed[2:6] == (2, 0.12, 0, 0.0)
    assert resumed[0] == verdicts


def test_malformed_response_is_immutably_parsed_as_missing_and_not_retried(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    judge = load_judge("judge_checkpoint_malformed_response")
    experiment, candidates, rows = configure(judge, monkeypatch, tmp_path)
    set_test_keys(monkeypatch)
    provider_calls = 0

    def openai(*_args: Any) -> str:
        nonlocal provider_calls
        provider_calls += 1
        return 'prose before {"wrong":"A"}'

    def anthropic(*_args: Any) -> str:
        nonlocal provider_calls
        provider_calls += 1
        return '{"wrong":"B"}'

    monkeypatch.setattr(judge, "call_openai", openai)
    monkeypatch.setattr(judge, "call_anthropic", anthropic)
    verdicts, bundle, retained_calls, retained_est, new_calls, new_est = (
        judge._run_iter202_judge_attempts(candidates, rows, TEST_RUNTIME_MANIFEST_SHA256)
    )
    assert provider_calls == 2
    assert (retained_calls, retained_est, new_calls, new_est) == (0, 0.0, 2, 0.12)
    assert verdicts[0]["gpt_verdict"] == "unparseable"
    assert verdicts[0]["judge_outcome_complete"] is False
    assert bundle["checkpoint_evidence"]["responses"] == 2
    parsed = [
        json.loads(path.read_text())
        for path in sorted((experiment / "proof/raw/judge_provider_attempts").glob("*.parsed.json"))
    ]
    assert [row["decision"] for row in parsed] == ["unparseable", "B"]

    clear_test_keys(monkeypatch)
    monkeypatch.setattr(
        judge,
        "_call_frozen_judge_provider",
        lambda *_args: (_ for _ in ()).throw(AssertionError("malformed output was retried")),
    )
    resumed = judge._run_iter202_judge_attempts(candidates, rows, TEST_RUNTIME_MANIFEST_SHA256)
    assert provider_calls == 2
    assert resumed[0] == verdicts


def test_partial_resume_needs_only_the_unfinished_provider_credential(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    judge = load_judge("judge_checkpoint_partial_resume")
    _experiment, candidates, rows = configure(judge, monkeypatch, tmp_path)
    set_test_keys(monkeypatch)
    calls: list[str] = []
    monkeypatch.setattr(
        judge,
        "call_openai",
        lambda *_args: calls.append("openai") or '{"wrong":"A"}',
    )
    monkeypatch.setattr(
        judge,
        "_after_judge_attempt_checkpoint",
        lambda: (_ for _ in ()).throw(InjectedCrash("after openai checkpoint")),
    )
    with pytest.raises(InjectedCrash, match="openai checkpoint"):
        judge._run_iter202_judge_attempts(candidates, rows, TEST_RUNTIME_MANIFEST_SHA256)

    monkeypatch.delenv("OPENAI_API_KEY")
    monkeypatch.setattr(judge, "_after_judge_attempt_checkpoint", lambda: None)
    monkeypatch.setattr(
        judge,
        "call_openai",
        lambda *_args: (_ for _ in ()).throw(AssertionError("openai was repeated")),
    )
    monkeypatch.setattr(
        judge,
        "call_anthropic",
        lambda *_args: calls.append("anthropic") or '{"wrong":"B"}',
    )
    resumed = judge._run_iter202_judge_attempts(candidates, rows, TEST_RUNTIME_MANIFEST_SHA256)
    assert calls == ["openai", "anthropic"]
    assert resumed[2:6] == (1, 0.06, 1, 0.06)
    assert resumed[0][0]["gpt_verdict"] == "A"
    assert resumed[0][0]["opus_verdict"] == "B"


def test_inflight_interrupt_leaves_charged_orphan_and_resume_fails_closed(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    judge = load_judge("judge_checkpoint_orphan")
    experiment, candidates, rows = configure(judge, monkeypatch, tmp_path)
    set_test_keys(monkeypatch)
    provider_calls = 0

    def interrupt(*_args: Any) -> str:
        nonlocal provider_calls
        provider_calls += 1
        raise KeyboardInterrupt

    monkeypatch.setattr(judge, "call_openai", interrupt)
    with pytest.raises(KeyboardInterrupt):
        judge._run_iter202_judge_attempts(candidates, rows, TEST_RUNTIME_MANIFEST_SHA256)

    attempt_dir = experiment / "proof/raw/judge_provider_attempts"
    started_path = next(attempt_dir.glob("*.started.json"))
    assert json.loads(started_path.read_text())["accounting"] == {
        "estimated_spend_usd": 0.06,
        "provider_calls": 1,
    }
    assert not list(attempt_dir.glob("*.finished.json"))

    clear_test_keys(monkeypatch)
    monkeypatch.setattr(
        judge,
        "_judge_provider_key",
        lambda *_args: (_ for _ in ()).throw(AssertionError("orphan read a key")),
    )
    with pytest.raises(judge.JudgeCheckpointError, match="refusing automatic retry"):
        judge._run_iter202_judge_attempts(candidates, rows, TEST_RUNTIME_MANIFEST_SHA256)
    assert provider_calls == 1


@pytest.mark.parametrize("damage", ["malformed", "duplicate", "parsed", "duplicate_parsed", "gap"])
def test_corrupt_duplicate_or_nonprefix_checkpoint_fails_before_credentials(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, damage: str
) -> None:
    judge = load_judge(f"judge_checkpoint_damage_{damage}")
    experiment, candidates, rows = configure(judge, monkeypatch, tmp_path)
    set_test_keys(monkeypatch)
    monkeypatch.setattr(judge, "call_openai", lambda *_args: '{"wrong":"A"}')
    monkeypatch.setattr(judge, "call_anthropic", lambda *_args: '{"wrong":"B"}')
    judge._run_iter202_judge_attempts(candidates, rows, TEST_RUNTIME_MANIFEST_SHA256)
    attempt_dir = experiment / "proof/raw/judge_provider_attempts"
    if damage == "malformed":
        next(attempt_dir.glob("*.finished.json")).write_text('{"broken":\n')
    elif damage == "duplicate":
        started = next(attempt_dir.glob("*.started.json"))
        shutil.copyfile(started, attempt_dir / ("duplicate-" + started.name))
    elif damage == "parsed":
        parsed = next(attempt_dir.glob("*.parsed.json"))
        document = json.loads(parsed.read_text())
        document["decision"] = "neither"
        parsed.write_text(json.dumps(document, indent=2, sort_keys=True) + "\n")
    elif damage == "duplicate_parsed":
        parsed = next(attempt_dir.glob("*.parsed.json"))
        shutil.copyfile(parsed, attempt_dir / ("duplicate-" + parsed.name))
    else:
        first_started = sorted(attempt_dir.glob("*.started.json"))[0]
        first_finished = sorted(attempt_dir.glob("*.finished.json"))[0]
        first_parsed = sorted(attempt_dir.glob("*.parsed.json"))[0]
        first_started.unlink()
        first_finished.unlink()
        first_parsed.unlink()

    clear_test_keys(monkeypatch)
    monkeypatch.setattr(
        judge,
        "_judge_provider_key",
        lambda *_args: (_ for _ in ()).throw(AssertionError("damage read a key")),
    )
    with pytest.raises(judge.JudgeCheckpointError):
        judge._run_iter202_judge_attempts(candidates, rows, TEST_RUNTIME_MANIFEST_SHA256)


@pytest.mark.parametrize("drift", ["prompt", "config", "runtime_manifest"])
def test_prompt_or_frozen_config_drift_fails_before_credentials(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, drift: str
) -> None:
    judge = load_judge(f"judge_checkpoint_drift_{drift}")
    _experiment, candidates, rows = configure(judge, monkeypatch, tmp_path)
    set_test_keys(monkeypatch)
    monkeypatch.setattr(judge, "call_openai", lambda *_args: '{"wrong":"A"}')
    monkeypatch.setattr(judge, "call_anthropic", lambda *_args: '{"wrong":"B"}')
    judge._run_iter202_judge_attempts(candidates, rows, TEST_RUNTIME_MANIFEST_SHA256)
    if drift == "prompt":
        rows["demo__demo-1"]["problem_statement"] = "A changed prompt."
    elif drift == "config":
        monkeypatch.setattr(judge, "OPENAI_JUDGE_MODEL", "changed-model")
    runtime_manifest_sha256 = (
        "e" * 64 if drift == "runtime_manifest" else TEST_RUNTIME_MANIFEST_SHA256
    )

    clear_test_keys(monkeypatch)
    monkeypatch.setattr(
        judge,
        "_judge_provider_key",
        lambda *_args: (_ for _ in ()).throw(AssertionError("drift read a key")),
    )
    with pytest.raises(judge.JudgeCheckpointError, match="non-frozen work"):
        judge._run_iter202_judge_attempts(candidates, rows, runtime_manifest_sha256)


def test_stale_verdict_output_fails_before_credentials(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    judge = load_judge("judge_checkpoint_stale_output")
    experiment, candidates, rows = configure(judge, monkeypatch, tmp_path)
    set_test_keys(monkeypatch)
    monkeypatch.setattr(judge, "call_openai", lambda *_args: '{"wrong":"A"}')
    monkeypatch.setattr(judge, "call_anthropic", lambda *_args: '{"wrong":"B"}')
    verdicts, bundle, *_ = judge._run_iter202_judge_attempts(
        candidates, rows, TEST_RUNTIME_MANIFEST_SHA256
    )
    assert verdicts
    bundle["verdicts"][0]["gpt_verdict"] = "neither"
    verdict_path = experiment / "proof/blind_judge_verdicts.json"
    verdict_path.write_text(json.dumps(bundle, indent=2, sort_keys=True) + "\n")

    clear_test_keys(monkeypatch)
    monkeypatch.setattr(
        judge,
        "_judge_provider_key",
        lambda *_args: (_ for _ in ()).throw(AssertionError("stale output read a key")),
    )
    with pytest.raises(judge.JudgeCheckpointError, match="stale or unbound"):
        judge._run_iter202_judge_attempts(candidates, rows, TEST_RUNTIME_MANIFEST_SHA256)


def test_existing_immutable_record_cannot_be_overwritten(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    judge = load_judge("judge_checkpoint_no_overwrite")
    experiment, candidates, rows = configure(judge, monkeypatch, tmp_path)
    specs, _ = judge._judge_attempt_specs(candidates, rows, TEST_RUNTIME_MANIFEST_SHA256)
    started = judge._judge_started_record(specs[0])
    stage = experiment / "proof/raw"
    judge._checkpoint_judge_started(stage, started)
    with pytest.raises(judge.JudgeCheckpointError, match="refusing to overwrite"):
        judge._checkpoint_judge_started(stage, started)


@pytest.mark.parametrize("component", ["stage", "attempts"])
def test_judge_rejects_preexisting_checkpoint_symlink_before_credentials(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    component: str,
) -> None:
    judge = load_judge(f"judge_symlink_{component}")
    experiment, candidates, rows = configure(judge, monkeypatch, tmp_path)
    stage = experiment / "proof/raw"
    attacker = tmp_path / "attacker-judge"
    attacker.mkdir()
    if component == "stage":
        stage.symlink_to(attacker, target_is_directory=True)
    else:
        stage.mkdir(parents=True)
        (stage / judge.JUDGE_ATTEMPT_DIRNAME).symlink_to(
            attacker, target_is_directory=True
        )
    key_reads: list[str] = []
    provider_calls: list[str] = []
    monkeypatch.setattr(
        judge,
        "_judge_provider_key",
        lambda _provider: key_reads.append("key") or "key",
    )
    monkeypatch.setattr(
        judge,
        "_call_frozen_judge_provider",
        lambda *_args: provider_calls.append("call") or '{"wrong":"A"}',
    )

    with pytest.raises(judge.JudgeCheckpointError):
        judge._run_iter202_judge_attempts(
            candidates, rows, TEST_RUNTIME_MANIFEST_SHA256
        )

    assert key_reads == []
    assert provider_calls == []
    assert list(attacker.iterdir()) == []


def test_judge_parent_swap_fails_before_credentials_without_external_write(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    judge = load_judge("judge_parent_swap")
    experiment, candidates, rows = configure(judge, monkeypatch, tmp_path)
    raw = experiment / "proof/raw"
    parked = experiment / "proof/raw-retained"
    attacker = tmp_path / "attacker-judge-swap"
    attacker.mkdir()
    key_reads: list[str] = []
    provider_calls: list[str] = []

    def swap_parent() -> None:
        raw.rename(parked)
        raw.symlink_to(attacker, target_is_directory=True)

    monkeypatch.setattr(judge, "_after_secure_judge_preflight", swap_parent)
    monkeypatch.setattr(
        judge,
        "_judge_provider_key",
        lambda _provider: key_reads.append("key") or "key",
    )
    monkeypatch.setattr(
        judge,
        "_call_frozen_judge_provider",
        lambda *_args: provider_calls.append("call") or '{"wrong":"A"}',
    )

    with pytest.raises(
        judge.JudgeCheckpointError, match="binding|symlink|traverse|verified"
    ):
        judge._run_iter202_judge_attempts(
            candidates, rows, TEST_RUNTIME_MANIFEST_SHA256
        )

    assert key_reads == []
    assert provider_calls == []
    assert list(attacker.iterdir()) == []
    assert (parked / judge.JUDGE_ATTEMPT_DIRNAME).is_dir()


def test_zero_divergence_bundle_is_checkpoint_derived_and_resumable_without_keys(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    judge = load_judge("judge_checkpoint_zero_divergence")
    experiment, _candidates, _rows = configure(judge, monkeypatch, tmp_path)
    clear_test_keys(monkeypatch)
    monkeypatch.setattr(
        judge,
        "_judge_provider_key",
        lambda *_args: (_ for _ in ()).throw(AssertionError("zero work read a key")),
    )
    verdicts, bundle, retained_calls, retained_est, new_calls, new_est = (
        judge._run_iter202_judge_attempts([], {}, TEST_RUNTIME_MANIFEST_SHA256)
    )
    assert verdicts == []
    assert (retained_calls, retained_est, new_calls, new_est) == (0, 0, 0, 0.0)
    assert bundle["checkpoint_evidence"]["attempts_started"] == 0
    assert bundle["checkpoint_evidence"]["attempts_finished"] == 0
    assert bundle["checkpoint_evidence"]["attempts_parsed"] == 0
    assert bundle["checkpoint_evidence"]["evidence_sha256"] == (
        "37517e5f3dc66819f61f5a7bb8ace1921282415f10551d2defa5c3eb0985b570"
    )
    judge._materialize_judge_derived_output(
        experiment / "proof/blind_judge_verdicts.json",
        judge._canonical_judge_json_bytes(bundle),
    )
    empty_audit = {
        "experiment_id": judge.ITER202_EXP,
        "funnel": {
            "blind_confirmed_natural_hacks": 0,
            "certified_and_diverging": 0,
            "diverging_with_complete_judges": 0,
        },
        "judge_accounting": {
            "estimated_spend_usd_total": 0.0,
            "provider_calls_total": 0,
        },
        "judge_checkpoint": bundle["checkpoint_evidence"],
        "natural_hacks": [],
        "schema_version": "telos.iter200.audit_report.v4",
    }
    judge._materialize_judge_derived_output(
        experiment / "proof/audit_report.json",
        judge._canonical_judge_json_bytes(empty_audit),
    )
    resumed = judge._run_iter202_judge_attempts([], {}, TEST_RUNTIME_MANIFEST_SHA256)
    assert resumed[:2] == ([], bundle)


@pytest.mark.parametrize("reason", ["manifest missing", "manifest stale"])
def test_paid_judge_entrypoint_rejects_invalid_runtime_before_locks_or_credentials(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, reason: str
) -> None:
    judge = load_judge(f"judge_runtime_gate_{reason.replace(' ', '_')}")
    configure(judge, monkeypatch, tmp_path)
    for name in judge.FORBIDDEN_JUDGE_OVERRIDE_ENV:
        monkeypatch.delenv(name, raising=False)
    touched: list[str] = []

    def reject_runtime() -> str:
        touched.append("runtime")
        raise judge.RuntimeFreezeError(reason)

    monkeypatch.setattr(judge, "require_valid_runtime_freeze", reject_runtime)
    monkeypatch.setattr(
        judge,
        "_load_iter202_runtime_module",
        lambda *_args: (_ for _ in ()).throw(AssertionError("runtime gate acquired a lock")),
    )
    monkeypatch.setattr(
        judge,
        "_judge_provider_key",
        lambda *_args: (_ for _ in ()).throw(AssertionError("runtime gate read a credential")),
    )
    monkeypatch.setattr(
        judge,
        "_call_frozen_judge_provider",
        lambda *_args: (_ for _ in ()).throw(AssertionError("runtime gate called a provider")),
    )
    with pytest.raises(judge.JudgeCheckpointError, match="invalid runtime freeze"):
        judge.main()
    assert touched == ["runtime"]


@pytest.mark.parametrize(
    "selector",
    ["nested/iter202_natural_rate_scaled", "../iter202_natural_rate_scaled"],
)
def test_paid_judge_rejects_noncanonical_iter202_selector_before_freeze_or_credentials(
    monkeypatch: pytest.MonkeyPatch, selector: str
) -> None:
    monkeypatch.setenv("TELOS_NAT_EXP", selector)
    judge = load_judge(f"judge_noncanonical_{selector.replace('/', '_')}")
    for name in judge.FORBIDDEN_JUDGE_OVERRIDE_ENV:
        monkeypatch.delenv(name, raising=False)
    touched: list[str] = []

    monkeypatch.setattr(
        judge,
        "require_valid_runtime_freeze",
        lambda: touched.append("freeze") or TEST_RUNTIME_MANIFEST_SHA256,
    )
    monkeypatch.setattr(
        judge,
        "_load_iter202_runtime_module",
        lambda *_args: touched.append("module"),
    )
    monkeypatch.setattr(
        judge,
        "_judge_provider_key",
        lambda *_args: touched.append("key") or "test-key",
    )
    monkeypatch.setattr(
        judge,
        "_keys",
        lambda: touched.append("legacy-keys") or ("openai-key", "anthropic-key"),
    )
    monkeypatch.setattr(
        judge,
        "_call_frozen_judge_provider",
        lambda *_args: touched.append("provider") or "response",
    )
    monkeypatch.setattr(
        judge,
        "call_openai",
        lambda *_args: touched.append("openai") or "response",
    )
    monkeypatch.setattr(
        judge,
        "call_anthropic",
        lambda *_args: touched.append("anthropic") or "response",
    )

    with pytest.raises(
        judge.JudgeCheckpointError, match="canonical experiment paths"
    ):
        judge.main()

    assert touched == []


def test_paid_judge_entrypoint_uses_solver_scenario_judge_lock_order(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    judge = load_judge("judge_canonical_lock_order")
    experiment, _candidates, _rows = configure(judge, monkeypatch, tmp_path)
    for name in judge.FORBIDDEN_JUDGE_OVERRIDE_ENV:
        monkeypatch.delenv(name, raising=False)
    events: list[str] = []

    @contextmanager
    def stage_lock(stage: Path):
        events.append(f"enter:{stage.name}")
        try:
            yield
        finally:
            events.append(f"exit:{stage.name}")

    @contextmanager
    def judge_lock(stage: Any):
        assert stage.path == experiment / "proof/raw"
        events.append("enter:judge")
        try:
            yield
        finally:
            events.append("exit:judge")

    class FakeCheckpointError(ValueError):
        pass

    @contextmanager
    def secure_stage(
        path: Path, *, create: bool, enforce_trusted_root: bool = False
    ):
        yield SimpleNamespace(name=path.name, path=path, create=create)

    lock_module = SimpleNamespace(
        CheckpointError=FakeCheckpointError,
        _exclusive_stage_lock=stage_lock,
        _open_secure_stage=secure_stage,
    )

    def runtime_gate() -> str:
        events.append("runtime")
        return TEST_RUNTIME_MANIFEST_SHA256

    monkeypatch.setattr(judge, "require_valid_runtime_freeze", runtime_gate)
    monkeypatch.setattr(judge, "_load_iter202_runtime_module", lambda *_args: lock_module)
    monkeypatch.setattr(judge, "_open_secure_judge_stage", secure_stage)
    monkeypatch.setattr(judge, "_exclusive_judge_lock", judge_lock)
    monkeypatch.setattr(
        judge,
        "_main_locked",
        lambda digest, **_kwargs: events.append(f"run:{digest}") or 0,
    )
    assert judge.main() == 0
    assert events == [
        "runtime",
        "enter:solutions",
        "enter:scenarios",
        "enter:judge",
        f"run:{TEST_RUNTIME_MANIFEST_SHA256}",
        "exit:judge",
        "exit:scenarios",
        "exit:solutions",
    ]


def _configure_precredential_reconstruction_fixture(
    judge: Any, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> dict[str, Any]:
    experiment, candidates, rows = configure(judge, monkeypatch, tmp_path)
    proof = experiment / "proof"
    snapshot = tmp_path / "snapshot.json"
    write_json(snapshot, {"rows": list(rows.values())})
    monkeypatch.setattr(judge, "SNAPSHOT", snapshot)
    write_json(
        proof / "raw/solve_targets.json",
        {
            "count": 1,
            "schema_version": "telos.iter202.solve_targets.v1",
            "targets": [{"instance_id": "demo__demo-1", "repo": "demo/demo"}],
        },
    )

    per_document = {
        "candidates": [
            {
                "certified_resolved": True,
                "execution_complete": True,
                "instance_id": "demo__demo-1",
                "status": "candidate_natural_hack",
            }
        ],
        "schema_version": "telos.iter200.per_candidate.v3",
    }
    divergence_document = {
        "candidates": candidates,
        "count": 1,
        "schema_version": "telos.iter200.divergence_candidates.v2",
    }
    write_json(proof / "iter200_per_candidate.json", per_document)
    write_json(proof / "divergence_candidates.json", divergence_document)

    solve_summary = {
        "estimated_spend_usd": 0.05,
        "manifest": [{"instance_id": "demo__demo-1", "status": "solution"}],
        "provider_calls": 1,
        "schema_version": "telos.iter200.solve_summary.v1",
        "solutions": 1,
        "targets": 1,
    }
    scenario_summary = {
        "differing_solutions": 1,
        "estimated_spend_usd": 0.05,
        "manifest": [{"instance_id": "demo__demo-1", "status": "scenario"}],
        "provider_calls": 1,
        "scenarios": 1,
        "schema_version": "telos.iter200.scenarios_summary.v1",
    }
    solutions = proof / "raw/solutions"
    scenarios = proof / "raw/scenarios"
    write_json(solutions / "solve_summary.json", solve_summary)
    write_json(scenarios / "scenarios_summary.json", scenario_summary)
    model_payload = b"model-patch\n"
    scenario_payload = b"print('RESULT=model')\n"
    (solutions / "demo__demo-1.model.patch").write_bytes(model_payload)
    (solutions / "demo__demo-1.gold.patch").write_bytes(b"gold-patch\n")
    (scenarios / "demo__demo-1.scenario.py").write_bytes(scenario_payload)
    write_json(solutions / "provider_attempts/0001.started.json", {})
    write_json(scenarios / "provider_attempts/0001.started.json", {})

    checkpoint = SimpleNamespace(
        ATTEMPT_DIRNAME="provider_attempts",
        adv=SimpleNamespace(MODEL="gpt-5.6-terra"),
    )
    scenario_module = SimpleNamespace(
        FROZEN_MODEL="gpt-5.6-terra",
        checkpoint=checkpoint,
        scen=SimpleNamespace(MODEL="gpt-5.6-terra"),
    )

    def reconstruct_solver(
        runtime_manifest_sha256: str, _solution_stage: Any
    ) -> dict[str, Any]:
        assert runtime_manifest_sha256 == TEST_RUNTIME_MANIFEST_SHA256
        if (solutions / "demo__demo-1.model.patch").read_bytes() != model_payload:
            raise ValueError("solver artifact mutation")
        return solve_summary

    def scenario_work(
        _summary: dict[str, Any], runtime_manifest_sha256: str, _solution_stage: Any
    ):
        assert runtime_manifest_sha256 == TEST_RUNTIME_MANIFEST_SHA256
        return ([{"instance_id": "demo__demo-1"}], [], 1)

    def reconstruct_scenarios(*_args: Any) -> dict[str, Any]:
        if (scenarios / "demo__demo-1.scenario.py").read_bytes() != scenario_payload:
            raise ValueError("scenario artifact mutation")
        return scenario_summary

    scenario_module._reconstruct_solver_state_locked = reconstruct_solver
    scenario_module._scenario_work_from_solver_summary = scenario_work
    scenario_module._require_exact_scenario_state = reconstruct_scenarios

    adjudicator_module = SimpleNamespace(
        build_adjudication_documents=lambda **_kwargs: (
            per_document,
            divergence_document,
        )
    )

    @contextmanager
    def no_op_lock(_stage: Path):
        yield

    class FakeCheckpointError(ValueError):
        pass

    lock_module = SimpleNamespace(
        CheckpointError=FakeCheckpointError,
        _exclusive_stage_lock=no_op_lock,
    )

    def load_module(relative: str, module_name: str) -> Any:
        if module_name == "iter202_judge_lock_protocol":
            return lock_module
        if relative == "scripts/run_iter200_scenarios.py":
            return scenario_module
        if relative == "scripts/adjudicate_iter200.py":
            return adjudicator_module
        raise AssertionError((relative, module_name))

    monkeypatch.setattr(judge, "require_valid_runtime_freeze", lambda: TEST_RUNTIME_MANIFEST_SHA256)
    monkeypatch.setattr(judge, "_load_iter202_runtime_module", load_module)
    return {
        "adjudicator_module": adjudicator_module,
        "divergence": proof / "divergence_candidates.json",
        "per": proof / "iter200_per_candidate.json",
        "scenario_artifact": scenarios / "demo__demo-1.scenario.py",
        "scenario_checkpoint": scenarios / "provider_attempts/0001.started.json",
        "scenario_summary": scenarios / "scenarios_summary.json",
        "solve_artifact": solutions / "demo__demo-1.model.patch",
        "solve_checkpoint": solutions / "provider_attempts/0001.started.json",
        "solve_summary": solutions / "solve_summary.json",
    }


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        ("solve_accounting", "solve summary does not exactly match"),
        ("scenario_accounting", "scenarios summary does not exactly match"),
        ("per_candidate", "per-candidate adjudication does not exactly match"),
        ("divergence", "divergence candidates does not exactly match"),
        ("solve_artifact", "solver artifact mutation"),
        ("scenario_artifact", "scenario artifact mutation"),
        ("checkpoint_nonfinite", "non-finite JSON constant"),
        ("aggregate_receipt", "exact-eight execution receipt is invalid"),
    ],
)
def test_upstream_or_derived_mutation_blocks_before_any_judge_credential(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    mutation: str,
    message: str,
) -> None:
    judge = load_judge(f"judge_precredential_mutation_{mutation}")
    paths = _configure_precredential_reconstruction_fixture(judge, monkeypatch, tmp_path)
    if mutation == "solve_accounting":
        document = json.loads(paths["solve_summary"].read_text())
        document["provider_calls"] = 0
        write_json(paths["solve_summary"], document)
    elif mutation == "scenario_accounting":
        document = json.loads(paths["scenario_summary"].read_text())
        document["provider_calls"] = 0
        write_json(paths["scenario_summary"], document)
    elif mutation == "per_candidate":
        document = json.loads(paths["per"].read_text())
        document["candidates"][0]["status"] = "certified_no_observed_divergence"
        write_json(paths["per"], document)
    elif mutation == "divergence":
        document = json.loads(paths["divergence"].read_text())
        document["candidates"][0]["model_result"] = "mutated"
        write_json(paths["divergence"], document)
    elif mutation == "solve_artifact":
        paths["solve_artifact"].write_text("mutated\n")
    elif mutation == "scenario_artifact":
        paths["scenario_artifact"].write_text("mutated\n")
    elif mutation == "checkpoint_nonfinite":
        paths["solve_checkpoint"].write_text('{"usage":NaN}\n')
    elif mutation == "aggregate_receipt":
        def invalid_bundle(**_kwargs: Any):
            raise ValueError("exact-eight execution receipt is invalid")

        paths["adjudicator_module"].build_adjudication_documents = invalid_bundle
    else:  # pragma: no cover - parameter list is exhaustive
        raise AssertionError(mutation)

    credential_reads: list[str] = []

    def credential(*_args: Any) -> str:
        credential_reads.append("credential")
        raise AssertionError("preflight read a credential")

    monkeypatch.setattr(judge, "_judge_provider_key", credential)
    monkeypatch.setattr(judge, "_keys", credential)
    monkeypatch.setattr(judge, "_call_frozen_judge_provider", credential)
    with pytest.raises(judge.JudgeCheckpointError, match=message):
        judge.main()
    assert credential_reads == []


def test_iter200_pure_adjudication_rebuild_is_byte_exact_and_provider_free() -> None:
    adjudicator = load_adjudicator("adjudicator_pure_byte_rebuild")
    per_document, divergence_document = adjudicator.build_adjudication_documents()
    assert (adjudicator.PROOF / "iter200_per_candidate.json").read_bytes() == (
        adjudicator.canonical_json_bytes(per_document)
    )
    assert (adjudicator.PROOF / "divergence_candidates.json").read_bytes() == (
        adjudicator.canonical_json_bytes(divergence_document)
    )


@pytest.mark.parametrize("raw", ['{"a":1,"a":2}\n', '{"value":NaN}\n'])
def test_adjudication_strict_json_rejects_duplicate_and_nonfinite_inputs(
    tmp_path: Path, raw: str
) -> None:
    adjudicator = load_adjudicator("adjudicator_strict_json")
    path = tmp_path / "input.json"
    path.write_text(raw)
    with pytest.raises(adjudicator.AdjudicationEvidenceError):
        adjudicator.load_json_strict(path)


def test_adjudication_rejects_nonindexed_execution_logs(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    adjudicator = load_adjudicator("adjudicator_unindexed_log")
    experiment = tmp_path / adjudicator.ITER200_EXP
    proof = experiment / "proof"
    raw = proof / "raw"
    shutil.copytree(adjudicator.SPECS, raw / "specs")
    shutil.copytree(adjudicator.LOGS, raw / "execution")
    shutil.copytree(adjudicator.SOLUTIONS, raw / "solutions")
    shutil.copytree(adjudicator.SCENARIOS, raw / "scenarios")
    (raw / "execution/unindexed.variant.log").write_text("unexpected\n")
    monkeypatch.setattr(adjudicator, "EXP", experiment)
    monkeypatch.setattr(adjudicator, "PROOF", proof)
    monkeypatch.setattr(adjudicator, "SPECS", raw / "specs")
    monkeypatch.setattr(adjudicator, "LOGS", raw / "execution")
    monkeypatch.setattr(adjudicator, "SOLUTIONS", raw / "solutions")
    monkeypatch.setattr(adjudicator, "SCENARIOS", raw / "scenarios")
    with pytest.raises(adjudicator.AdjudicationEvidenceError, match="non-indexed logs"):
        adjudicator.build_adjudication_documents()


def test_iter202_adjudicator_gates_then_locks_and_atomically_materializes_pair(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    adjudicator = load_adjudicator("adjudicator_runtime_lock_atomic")
    experiment = tmp_path / adjudicator.ITER202_EXP
    proof = experiment / "proof"
    solutions = proof / "raw/solutions"
    scenarios = proof / "raw/scenarios"
    solutions.mkdir(parents=True)
    scenarios.mkdir(parents=True)
    monkeypatch.setattr(adjudicator, "EXP", experiment)
    monkeypatch.setattr(adjudicator, "PROOF", proof)
    monkeypatch.setattr(adjudicator, "SOLUTIONS", solutions)
    monkeypatch.setattr(adjudicator, "SCENARIOS", scenarios)
    events: list[str] = []

    def gate() -> str:
        events.append("runtime")
        return TEST_RUNTIME_MANIFEST_SHA256

    @contextmanager
    def lock(stage: Path):
        events.append(f"enter:{stage.name}")
        try:
            yield
        finally:
            events.append(f"exit:{stage.name}")

    per_document = {
        "candidates": [],
        "schema_version": "telos.iter200.per_candidate.v3",
    }
    divergence_document = {
        "candidates": [],
        "count": 0,
        "schema_version": "telos.iter200.divergence_candidates.v2",
    }

    def build_documents():
        events.append("build")
        return per_document, divergence_document

    def atomic(path: Path, payload: bytes) -> None:
        assert payload in {
            adjudicator.canonical_json_bytes(per_document),
            adjudicator.canonical_json_bytes(divergence_document),
        }
        events.append(f"atomic:{path.name}")

    monkeypatch.setattr(adjudicator, "require_valid_runtime_freeze", gate)
    monkeypatch.setattr(adjudicator, "_exclusive_stage_lock", lock)
    monkeypatch.setattr(adjudicator, "build_adjudication_documents", build_documents)
    monkeypatch.setattr(adjudicator, "_atomic_replace_bytes", atomic)
    assert adjudicator.main() == 0
    assert events == [
        "runtime",
        "enter:solutions",
        "enter:scenarios",
        "build",
        "atomic:iter200_per_candidate.json",
        "atomic:divergence_candidates.json",
        "exit:scenarios",
        "exit:solutions",
    ]


def test_iter202_invalid_aggregate_blocks_adjudicator_before_any_derived_write(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    adjudicator = load_adjudicator("adjudicator_invalid_exact_eight_bundle")
    experiment = tmp_path / adjudicator.ITER202_EXP
    proof = experiment / "proof"
    solutions = proof / "raw/solutions"
    scenarios = proof / "raw/scenarios"
    solutions.mkdir(parents=True)
    scenarios.mkdir(parents=True)
    monkeypatch.setattr(adjudicator, "EXP", experiment)
    monkeypatch.setattr(adjudicator, "PROOF", proof)
    monkeypatch.setattr(adjudicator, "SPECS", proof / "raw/specs")
    monkeypatch.setattr(adjudicator, "LOGS", proof / "raw/execution")
    monkeypatch.setattr(adjudicator, "SOLUTIONS", solutions)
    monkeypatch.setattr(adjudicator, "SCENARIOS", scenarios)
    monkeypatch.setattr(
        adjudicator, "require_valid_runtime_freeze", lambda: TEST_RUNTIME_MANIFEST_SHA256
    )

    @contextmanager
    def lock(_stage: Path):
        yield

    monkeypatch.setattr(adjudicator, "_exclusive_stage_lock", lock)
    monkeypatch.setattr(adjudicator, "load_json_strict", lambda _path: {})
    monkeypatch.setattr(adjudicator, "validate_spec_index", lambda *_args, **_kwargs: [])

    def invalid_bundle(**_kwargs: Any) -> None:
        raise adjudicator.ExecutionCollectionError("missing shard 7")

    monkeypatch.setattr(adjudicator, "check_execution_bundle_with_logs", invalid_bundle)
    writes: list[Path] = []
    monkeypatch.setattr(
        adjudicator,
        "_atomic_replace_bytes",
        lambda path, _payload: writes.append(path),
    )
    with pytest.raises(adjudicator.AdjudicationEvidenceError, match="missing shard 7"):
        adjudicator.main()
    assert writes == []
    assert not (proof / "iter200_per_candidate.json").exists()
    assert not (proof / "divergence_candidates.json").exists()


def test_iter202_incomplete_certification_framing_fails_instead_of_becoming_missingness(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    adjudicator = load_adjudicator("adjudicator_incomplete_iter202_framing")
    experiment = tmp_path / adjudicator.ITER202_EXP
    proof = experiment / "proof"
    logs = proof / "raw/execution"
    logs.mkdir(parents=True)
    iid = "demo__demo-1"
    (logs / f"{iid}.variant.log").write_text("disk variant bytes\n")
    (logs / f"{iid}.gold.log").write_text("disk gold bytes\n")
    monkeypatch.setattr(adjudicator, "EXP", experiment)
    monkeypatch.setattr(adjudicator, "PROOF", proof)
    monkeypatch.setattr(adjudicator, "SPECS", proof / "raw/specs")
    monkeypatch.setattr(adjudicator, "LOGS", logs)
    monkeypatch.setattr(adjudicator, "SOLUTIONS", proof / "raw/solutions")
    monkeypatch.setattr(adjudicator, "SCENARIOS", proof / "raw/scenarios")
    monkeypatch.setattr(
        adjudicator,
        "check_execution_bundle_with_logs",
        lambda **_kwargs: (
            {},
            {
                f"{iid}.variant.log": b"receipt-bound partial certification output\n",
                f"{iid}.gold.log": b"receipt-bound partial gold output\n",
            },
        ),
    )
    monkeypatch.setattr(
        adjudicator,
        "load_json_strict",
        lambda path: (
            {"fail_to_pass": ["test_demo"], "pass_to_pass": []}
            if path.name.endswith(".spec.json")
            else {}
        ),
    )
    monkeypatch.setattr(
        adjudicator,
        "validate_spec_index",
        lambda *_args, **_kwargs: [
            {
                "_validated_fail_to_pass": ["test_demo"],
                "_validated_pass_to_pass": [],
                "instance_id": iid,
                "repo": "demo/demo",
            }
        ],
    )
    with pytest.raises(
        adjudicator.AdjudicationEvidenceError,
        match="certification framing is incomplete",
    ):
        adjudicator.build_adjudication_documents()


def test_iter202_zero_solution_null_builds_empty_derived_documents(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    adjudicator = load_adjudicator("adjudicator_zero_solution_iter202")
    experiment = tmp_path / adjudicator.ITER202_EXP
    proof = experiment / "proof"
    monkeypatch.setattr(adjudicator, "EXP", experiment)
    monkeypatch.setattr(adjudicator, "PROOF", proof)
    monkeypatch.setattr(adjudicator, "SPECS", proof / "raw/specs")
    monkeypatch.setattr(adjudicator, "LOGS", proof / "raw/execution")
    monkeypatch.setattr(adjudicator, "SOLUTIONS", proof / "raw/solutions")
    monkeypatch.setattr(adjudicator, "SCENARIOS", proof / "raw/scenarios")
    monkeypatch.setattr(adjudicator, "load_json_strict", lambda _path: {})
    monkeypatch.setattr(
        adjudicator, "validate_spec_index", lambda *_args, **_kwargs: []
    )
    monkeypatch.setattr(
        adjudicator,
        "check_execution_bundle_with_logs",
        lambda **_kwargs: ({"logs": []}, {}),
    )

    per_document, candidates_document = adjudicator.build_adjudication_documents()
    assert per_document == {
        "schema_version": "telos.iter200.per_candidate.v3",
        "candidates": [],
    }
    assert candidates_document == {
        "schema_version": "telos.iter200.divergence_candidates.v2",
        "count": 0,
        "candidates": [],
    }


def test_iter202_adjudication_never_reopens_spec_after_validated_snapshot(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    adjudicator = load_adjudicator("adjudicator_spec_snapshot_iter202")
    experiment = tmp_path / adjudicator.ITER202_EXP
    proof = experiment / "proof"
    iid = "demo__demo-1"
    monkeypatch.setattr(adjudicator, "EXP", experiment)
    monkeypatch.setattr(adjudicator, "PROOF", proof)
    monkeypatch.setattr(adjudicator, "SPECS", proof / "raw/specs")
    monkeypatch.setattr(adjudicator, "LOGS", proof / "raw/execution")
    monkeypatch.setattr(adjudicator, "SOLUTIONS", proof / "raw/solutions")
    monkeypatch.setattr(adjudicator, "SCENARIOS", proof / "raw/scenarios")
    loaded_names: list[str] = []

    def load_only_index(path: Path) -> dict[str, Any]:
        loaded_names.append(path.name)
        if path.name != "index.json":
            raise AssertionError("mutable spec was reopened after validation")
        return {}

    monkeypatch.setattr(adjudicator, "load_json_strict", load_only_index)
    monkeypatch.setattr(
        adjudicator,
        "validate_spec_index",
        lambda *_args, **_kwargs: [
            {
                "_validated_fail_to_pass": ["test_frozen"],
                "_validated_pass_to_pass": [],
                "identical_to_gold": True,
                "instance_id": iid,
                "repo": "demo/demo",
                "scenario_available": False,
            }
        ],
    )
    monkeypatch.setattr(
        adjudicator,
        "check_execution_bundle_with_logs",
        lambda **_kwargs: (
            {},
            {
                f"{iid}.gold.log": b"gold snapshot\n",
                f"{iid}.variant.log": b"variant snapshot\n",
            },
        ),
    )
    monkeypatch.setattr(
        adjudicator,
        "certification_evidence",
        lambda _text, *, allow_legacy=False: ("frozen", True, True),
    )
    monkeypatch.setattr(
        adjudicator,
        "PARSER_BY_REPO",
        {"demo/demo": lambda _body: {"test_frozen": adjudicator.TestStatus.PASSED}},
    )
    monkeypatch.setattr(
        adjudicator,
        "image_provenance",
        lambda _text, *, allow_legacy=False: ("image", "digest"),
    )
    monkeypatch.setattr(
        adjudicator,
        "scenario_result",
        lambda _text, _kind, *, allow_legacy=False: (None, False),
    )

    per_document, _ = adjudicator.build_adjudication_documents()
    assert loaded_names == ["index.json"]
    assert per_document["candidates"][0]["certified_resolved"] is True
