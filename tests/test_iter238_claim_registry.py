"""Adversarial known-good and known-bad tests for iter238 claim coverage."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import replace
import hashlib
import json
from pathlib import Path
import shutil
import subprocess

import pytest

from scripts import build_current_claim_registry as builder
from scripts import validate_claim_registry as guard
from telos.json_compare import compare_json


ROOT = Path(__file__).resolve().parents[1]


def _write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _copy_surfaces(target: Path) -> None:
    for relative in guard.declared_surface_paths(ROOT):
        destination = target / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / relative, destination)


def _clone_current_evidence_context(target: Path) -> None:
    subprocess.run(
        [
            "git",
            "clone",
            "--shared",
            "--no-checkout",
            "-q",
            str(ROOT),
            str(target),
        ],
        check=True,
    )
    subprocess.run(
        ["git", "-C", target, "checkout", "-q", "HEAD"],
        check=True,
    )
    manifest = builder.DEPENDENCY_MANIFEST.relative_to(ROOT).as_posix()
    paths = {
        *guard.declared_surface_paths(ROOT),
        *builder.internal_dependency_paths(),
        manifest,
        guard.SEAL_REGISTRY_PATH.as_posix(),
    }
    for relative in sorted(paths):
        destination = target / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / relative, destination)


def _candidate(tmp_path: Path) -> dict[str, object]:
    surface_root = tmp_path / "candidate-surfaces"
    _copy_surfaces(surface_root)
    return guard.bootstrap_registry(
        surface_root,
        internal_claims=builder.build_internal_claims(),
    )


def _authorize(registry: dict[str, object]) -> str:
    gate = registry["active_gate"]
    assert isinstance(gate, str)
    digest = guard.binding_authorization_sha256(
        ROOT,
        registry=registry,
        active_gate=gate,
    )
    guard.AUTHORIZED_BINDING_INVENTORY_SHA256[gate] = digest
    return digest


def _validate_candidate(
    tmp_path: Path,
    registry: dict[str, object],
    *,
    authorize: dict[str, object] | None = None,
    check_internal: bool = False,
) -> tuple[list[str], dict[str, object]]:
    _authorize(registry if authorize is None else authorize)
    path = tmp_path / "candidate_registry.json"
    _write_json(path, registry)
    return guard.validate(
        root=ROOT,
        registry_relative=path,
        check_internal=check_internal,
        check_source_digests=True,
        check_seals=True,
        check_report=False,
    )


def _mutated_candidate(
    tmp_path: Path,
    mutation: object,
) -> tuple[list[str], dict[str, object]]:
    original = _candidate(tmp_path)
    mutated = deepcopy(original)
    assert callable(mutation)
    mutation(mutated)
    return _validate_candidate(tmp_path, mutated, authorize=original)


def _bindings_for_text(
    tmp_path: Path,
    text: str,
    *,
    relative: str = "README.md",
) -> list[guard.AtomBinding]:
    path = tmp_path / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"# Fixture\n\n{text}\n", encoding="utf-8")
    result: list[guard.AtomBinding] = []
    for segment in guard.extract_segments(tmp_path, relative):
        for ordinal, atom in enumerate(segment.atoms):
            result.append(
                guard.AtomBinding(
                    binding_id=(
                        f"{relative}:{segment.anchor_sha256[:20]}:"
                        f"{segment.segment_ordinal}:{ordinal}"
                    ),
                    segment=segment,
                    atom_ordinal=ordinal,
                    atom=atom,
                )
            )
    return result


def _first_granular_claim(
    registry: dict[str, object],
    *,
    kind: str = "historical_empirical",
) -> tuple[str, dict[str, object]]:
    claims = registry["claims"]
    assert isinstance(claims, dict)
    return next(
        (claim_id, claim)
        for claim_id, claim in claims.items()
        if isinstance(claim, dict)
        and claim.get("kind") == kind
        and claim.get("superseded_by") is None
        and len(claim.get("surface_binding_ids", [])) == 1
    )


def test_provisional_candidate_has_exact_complete_binding_coverage(
    tmp_path: Path,
) -> None:
    registry = _candidate(tmp_path)
    failures, report = _validate_candidate(
        tmp_path,
        registry,
        check_internal=True,
    )
    assert failures == []
    assert report["unclassified_count"] == 0
    assert report["conflicting_projection_count"] == 0
    assert report["internally_regenerated_count"] == 6
    assert report["public_binding_count"] == len(registry["bindings"])
    assert report["registered_claim_count"] == len(registry["claims"])
    assert report["preregistered_surface_paths"] == [
        "README.md",
        "paper/telos.tex",
        guard.declared_surface_paths(ROOT)[3],
        "mission/current.json",
    ]
    assert report["supplemental_hardening_surface_paths"] == [
        "paper/README.md",
        guard.declared_surface_paths(ROOT)[4],
    ]
    assert report["retained_semantic_metadata_unresolved_count"] == (
        report["historical_semantic_metadata_unresolved_count"]
        + report["external_semantic_metadata_unresolved_count"]
    )


def test_frozen_repository_registry_and_report_when_authorized() -> None:
    gate = guard.read_json(ROOT / "mission/current.json")["active_gate"]
    retained = guard.read_json(ROOT / guard.REGISTRY_PATH)
    expected = guard.AUTHORIZED_BINDING_INVENTORY_SHA256.get(gate, "")
    if (
        "PENDING" in expected
        or retained.get("schema_version") != guard.SCHEMA_VERSION
        or "migration" not in retained
    ):
        pytest.skip("C1 public surfaces and authority digest are not frozen yet")
    failures, report = guard.validate()
    assert failures == []
    assert guard.read_json(
        ROOT / guard.report_path_for_gate(report["active_gate"])
    ) == report


def test_internal_claims_rebuild_with_strict_json_types() -> None:
    expected = builder.build_internal_claims()
    mutated = deepcopy(expected["telos.recurrence.fixed_cohort"])
    mutated["value"]["fixed_cohort_runs"]["iter223"]["N"] = 29.0
    mismatches = compare_json(
        mutated,
        expected["telos.recurrence.fixed_cohort"],
        path="claim",
    )
    assert any("JSON type changed" in mismatch for mismatch in mismatches)


def test_internal_prerequisites_execute_and_fail_closed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    expected = builder.build_internal_claims()
    assert guard.validate_internal_prerequisites(ROOT, expected) == []

    def fail_predecessor(
        argv: list[str],
        root: Path,
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(
            argv,
            9,
            stdout="",
            stderr="known-bad predecessor",
        )

    monkeypatch.setattr(guard, "_run_credential_stripped", fail_predecessor)
    failures = guard.validate_internal_prerequisites(ROOT, expected)
    assert any("exit=9" in failure for failure in failures)


def test_offline_environment_is_allowlist_only(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    for name in (
        "OPENAI_API_KEY",
        "GOOGLE_APPLICATION_CREDENTIALS",
        "GH_TOKEN",
        "GITHUB_TOKEN",
        "SSH_AUTH_SOCK",
        "AWS_PROFILE",
        "UNRELATED_VALUE",
    ):
        monkeypatch.setenv(name, "secret")
    captured: dict[str, str] = {}

    def fake_run(
        argv: list[str],
        **kwargs: object,
    ) -> subprocess.CompletedProcess[str]:
        captured.update(kwargs["env"])
        return subprocess.CompletedProcess(argv, 0, stdout="", stderr="")

    monkeypatch.setattr(guard.subprocess, "run", fake_run)
    guard._run_credential_stripped(["python3", "-V"], ROOT)
    assert not {
        "OPENAI_API_KEY",
        "GOOGLE_APPLICATION_CREDENTIALS",
        "GH_TOKEN",
        "GITHUB_TOKEN",
        "SSH_AUTH_SOCK",
        "AWS_PROFILE",
        "UNRELATED_VALUE",
    } & set(captured)
    assert captured["HOME"] != str(Path.home())
    assert captured["GIT_CONFIG_GLOBAL"] == guard.os.devnull


@pytest.mark.parametrize(
    ("text", "expected_type", "expected_value"),
    [
        ("dozen", "integer", 12),
        ("½", "ratio", ("1", "2")),
        ("10k", "integer", 10_000),
        ("one billion", "integer", 1_000_000_000),
        ("two-thirds", "ratio", ("2", "3")),
        ("−7", "scalar", "-7"),
        (".005", "scalar", "0.005"),
        ("1_000", "scalar", "1000"),
        ("21st", "integer", 21),
        ("none", "integer", 0),
        ("single", "integer", 1),
        ("once", "multiplier", 1),
        ("both", "integer", 2),
        ("twice", "multiplier", 2),
    ],
)
def test_exact_quantitative_grammar(
    text: str,
    expected_type: str,
    expected_value: object,
) -> None:
    atom = guard.quantitative_atoms(text)[0]
    assert atom.normalized["numeric_type"] == expected_type
    if expected_type == "ratio":
        assert (
            atom.normalized["numerator"],
            atom.normalized["denominator"],
        ) == expected_value
    else:
        assert atom.normalized["value"] == expected_value


def test_currency_magnitude_and_math_currency_are_distinct(
    tmp_path: Path,
) -> None:
    bindings = _bindings_for_text(
        tmp_path,
        r"Plan `$15k-$40k`; math $9/22$; invoice \$13.12.",
        relative="paper/telos.tex",
    )
    normalized = {
        binding.atom.text: binding.atom.normalized for binding in bindings
    }
    assert normalized["$15k"]["currency"] is True
    assert normalized["$40k"]["currency"] is True
    assert normalized["$9/22"]["currency"] is False
    assert normalized["$13.12"]["currency"] is True


def test_python_none_literals_are_not_zero_but_natural_none_is() -> None:
    for text in (r"\texttt{None}", r"\texttt{\{'id': None\}}", "`None`"):
        assert guard.quantitative_atoms(text) == ()
    separated = guard.quantitative_atoms(r"\texttt{x} None \texttt{y}")
    assert [(atom.text, atom.normalized["value"]) for atom in separated] == [
        ("None", 0)
    ]
    assert guard.quantitative_atoms("None establishes no result.")[0].normalized[
        "value"
    ] == 0


def test_registered_identifiers_are_token_local_nonclaims(
    tmp_path: Path,
) -> None:
    bindings = _bindings_for_text(
        tmp_path,
        "P0 and P0.1 reference T1 through T4; result 7 remains.",
    )
    by_text: dict[str, list[guard.AtomBinding]] = {}
    for binding in bindings:
        by_text.setdefault(binding.atom.text, []).append(binding)
    for text in ("P0", "P0.1", "T1", "T4"):
        resolution = guard.derive_nonclaim(by_text[text][0])
        assert resolution is not None
        assert resolution["category"] == "claim_or_section_identifier"
    assert guard.derive_nonclaim(by_text["7"][0]) is None


def test_coordinated_backticked_and_generic_versions_are_nonclaims(
    tmp_path: Path,
) -> None:
    bindings = _bindings_for_text(
        tmp_path,
        (
            "Python 3.11 and 3.12; Python `3.11.15`; "
            "Framework version 3.0; standalone 1.2.3; empirical result 3.14."
        ),
    )
    by_text = {binding.atom.text: binding for binding in bindings}
    assert "15" not in by_text
    for text in ("3.11", "3.12", "3.11.15", "3.0", "1.2.3"):
        resolution = guard.derive_nonclaim(by_text[text])
        assert resolution is not None
        assert resolution["category"] == "model_or_software_version"
    assert guard.derive_nonclaim(by_text["3.14"]) is None


def test_numbered_heading_is_format_not_identifier_claim(
    tmp_path: Path,
) -> None:
    path = tmp_path / "README.md"
    path.write_text("# P0.3 — Boundary\n\nOutcome 7.\n", encoding="utf-8")
    bindings = [
        guard.AtomBinding(
            binding_id="fixture",
            segment=segment,
            atom_ordinal=ordinal,
            atom=atom,
        )
        for segment in guard.extract_segments(tmp_path, "README.md")
        for ordinal, atom in enumerate(segment.atoms)
    ]
    heading = next(item for item in bindings if item.atom.text == "P0.3")
    resolution = guard.derive_nonclaim(heading)
    assert resolution is not None
    assert resolution["rule"] == "markdown_numbered_heading"


def test_sidedness_and_reviewed_configuration_atoms_are_protocol() -> None:
    required = {
        "README.md:c5865997d69b9f34dcf2:0:1",
        "paper/telos.tex:d5aad3b6426f1432ab9b:0:7",
        "paper/telos.tex:49891e97df008b2fc962:0:1",
        "paper/telos.tex:a4c627b2636fdb5cb3f4:0:1",
        "docs/TELOS-AUDIT-2026-07-19.md:f13baba2349012fe7ed7:0:2",
        "docs/TELOS-AUDIT-2026-07-19.md:f4da0bc3c22af2a08180:0:2",
        "docs/TELOS-AUDIT-2026-07-19.md:c7d10089c4dc91f2c73d:0:5",
        "paper/telos.tex:871460b55a2c239e32fb:0:0",
        "paper/telos.tex:47cb329178248bc34729:0:0",
        "paper/telos.tex:47cb329178248bc34729:0:1",
        "paper/telos.tex:607b985b4af6432e5555:0:0",
        "paper/telos.tex:607b985b4af6432e5555:0:1",
        "paper/telos.tex:d009dbcbfda661fb9b0c:0:0",
        "paper/telos.tex:d009dbcbfda661fb9b0c:0:1",
        "paper/telos.tex:d009dbcbfda661fb9b0c:0:2",
        "paper/telos.tex:63d4d0d67a85b5c3dc59:0:0",
        "paper/telos.tex:a8a0df40a79a93387ce9:0:0",
        "paper/telos.tex:a8a0df40a79a93387ce9:0:1",
        "paper/telos.tex:d1ce883b6545880c970f:0:0",
        "paper/telos.tex:d1ce883b6545880c970f:0:1",
        "paper/telos.tex:d1ce883b6545880c970f:0:2",
        "paper/telos.tex:eec04e995296c9116d44:0:4",
        "paper/telos.tex:74786cc52f1cc045eced:0:0",
        "paper/telos.tex:74786cc52f1cc045eced:0:1",
        "paper/telos.tex:ee61d3f4b6ec580db0aa:0:0",
    }
    assert required <= guard.CURATED_PROTOCOL_BINDINGS
    live = {
        binding.binding_id: binding
        for binding in guard.extract_all_bindings(ROOT)
    }
    for binding_id in required:
        binding = live[binding_id]
        assert guard.derive_nonclaim(binding) is None
        assert guard._retained_kind(binding) == "protocol_parameter"
    assert (
        guard._retained_kind(live["paper/telos.tex:d5aad3b6426f1432ab9b:0:6"])
        != "protocol_parameter"
    )
    assert (
        "paper/telos.tex:d5aad3b6426f1432ab9b:0:6"
        in guard.CURATED_INTERNAL_PROJECTIONS
    )
    engineering_id = (
        "docs/HANDOFF-2026-07-19-iter238.md:e145d87cd851d1ff6d4e:0:0"
    )
    assert engineering_id in guard.CURATED_ENGINEERING_BINDINGS
    assert guard._retained_kind(live[engineering_id]) == "engineering_verification"


def test_arbitrary_citation_adjacency_does_not_mint_external_claim(
    tmp_path: Path,
) -> None:
    bindings = _bindings_for_text(
        tmp_path,
        (
            r"A cited monitor reports 30\%~\cite{audit}."
            "\n\n"
            r"\begin{thebibliography}{2}"
            "\n"
            r"\bibitem{wrapped} A. Author. Journal, 2024."
            "\n"
            r"\end{thebibliography}"
        ),
        relative="paper/telos.tex",
    )
    body = next(item for item in bindings if item.atom.text == r"30\%")
    bibliography = next(item for item in bindings if item.atom.text == "2024")
    assert guard._retained_kind(body) == "historical_empirical"
    assert guard._retained_kind(bibliography) == "external_citation"


def test_unresolved_retained_semantics_are_machine_enforced(
    tmp_path: Path,
) -> None:
    registry = _candidate(tmp_path)
    _, claim = _first_granular_claim(registry)
    assert claim["value"]["semantic_metadata_resolution"] == (
        guard.UNRESOLVED_RETAINED_SEMANTIC_STATE
    )
    assert claim["unit"] == guard.UNRESOLVED_RETAINED_UNIT
    assert claim["cohort"] == guard.UNRESOLVED_RETAINED_COHORT
    assert claim["independence_boundary"] == (
        guard.UNRESOLVED_RETAINED_INDEPENDENCE
    )
    assert claim["excluded_inferences"] == guard.UNRESOLVED_RETAINED_EXCLUSIONS

    failures: list[str] = []
    changed = deepcopy(claim)
    changed["value"]["semantic_metadata_resolution"] = "complete"
    changed["excluded_inferences"].remove(
        "scientific reuse until unit, cohort, and independence metadata are adjudicated"
    )
    guard._validate_claim_schema(changed["claim_id"], changed, failures)
    assert any("unresolved retained semantic contract differs" in item for item in failures)


def test_source_binding_reciprocity_rejects_repoint(
    tmp_path: Path,
) -> None:
    def mutate(registry: dict[str, object]) -> None:
        _, claim = _first_granular_claim(registry)
        other = next(
            binding["binding_id"]
            for binding in registry["bindings"]
            if binding["binding_id"] not in claim["surface_binding_ids"]
        )
        claim["sources"][0]["binding_id"] = other

    failures, _ = _mutated_candidate(tmp_path, mutate)
    assert any("mutable segment sources do not exactly match" in item for item in failures)


@pytest.mark.parametrize("operation", ["delete", "repoint"])
def test_missingness_binding_reciprocity_rejects_drift(
    tmp_path: Path,
    operation: str,
) -> None:
    def mutate(registry: dict[str, object]) -> None:
        _, claim = _first_granular_claim(registry)
        if operation == "delete":
            claim["missingness"].pop("binding_id")
        else:
            claim["missingness"]["binding_id"] = "another:binding"

    failures, _ = _mutated_candidate(tmp_path, mutate)
    assert any("missingness binding" in item for item in failures)


def test_explicit_missingness_role_and_value_are_exact(
    tmp_path: Path,
) -> None:
    registry = _candidate(tmp_path)
    claim_id, claim = next(
        (claim_id, claim)
        for claim_id, claim in registry["claims"].items()
        if isinstance(claim, dict)
        and claim.get("missingness", {}).get("mode") == "surface_explicit"
        and claim.get("superseded_by") is None
    )
    original = deepcopy(registry)
    claim["missingness"]["normalized_value"] = {
        "numeric_type": "integer",
        "value": 999,
    }
    failures, _ = _validate_candidate(tmp_path, registry, authorize=original)
    assert any(
        f"claim {claim_id} explicit missingness role/value differs" in item
        for item in failures
    )


@pytest.mark.parametrize(
    "mutation",
    [
        lambda registry: registry.__setitem__(
            "revision", registry["revision"] + 1
        ),
        lambda registry: registry.__setitem__(
            "migration", {"schema_version": "unauthorized"}
        ),
        lambda registry: next(iter(registry["claims"].values())).__setitem__(
            "unit", "mutated unit"
        ),
        lambda registry: next(iter(registry["claims"].values())).__setitem__(
            "revision",
            next(iter(registry["claims"].values()))["revision"] + 1,
        ),
    ],
)
def test_authorization_hash_binds_registry_and_claim_semantics(
    tmp_path: Path,
    mutation: object,
) -> None:
    registry = _candidate(tmp_path)
    before = guard.binding_authorization_sha256(ROOT, registry=registry)
    mutation(registry)
    after = guard.binding_authorization_sha256(ROOT, registry=registry)
    assert after != before


def test_wording_rebind_preserves_id_and_increments_once(
    tmp_path: Path,
) -> None:
    registry = _candidate(tmp_path)
    claim_id, claim = _first_granular_claim(registry)
    binding_id = claim["surface_binding_ids"][0]
    registered = next(
        item for item in registry["bindings"] if item["binding_id"] == binding_id
    )
    atom = registered["atom"]["text"]
    replacement = next(
        item
        for item in _bindings_for_text(
            tmp_path / "rebind",
            f"Reworded retained observation {atom}.",
        )
        if item.atom.normalized == registered["atom"]["normalized"]
    )
    migrated = guard.propose_wording_rebind(
        registry,
        old_binding_id=binding_id,
        replacement=replacement,
    )
    assert claim_id in migrated["claims"]
    assert migrated["claims"][claim_id]["revision"] == claim["revision"] + 1
    assert migrated["claims"][claim_id]["surface_binding_ids"] == [
        replacement.binding_id
    ]


def test_wording_rebind_rejects_noop_and_material_value_change(
    tmp_path: Path,
) -> None:
    registry = _candidate(tmp_path)
    _, claim = _first_granular_claim(registry)
    binding_id = claim["surface_binding_ids"][0]
    live = {
        binding.binding_id: binding
        for binding in guard.extract_all_bindings(ROOT)
    }[binding_id]
    with pytest.raises(ValueError, match="distinct binding"):
        guard.propose_wording_rebind(
            registry,
            old_binding_id=binding_id,
            replacement=live,
        )
    changed_atom = replace(
        live.atom,
        normalized={"numeric_type": "integer", "value": 999},
    )
    with pytest.raises(ValueError, match="material correction lineage"):
        guard.propose_wording_rebind(
            registry,
            old_binding_id=binding_id,
            replacement=replace(
                live,
                binding_id=f"{live.binding_id}:changed",
                atom=changed_atom,
            ),
        )


def test_disconnected_fake_lineage_is_rejected(tmp_path: Path) -> None:
    registry = _candidate(tmp_path)
    _, template = _first_granular_claim(registry)
    predecessor = deepcopy(template)
    successor = deepcopy(template)
    predecessor.update(
        {
            "claim_id": "fixture.fake.old",
            "status": "corrected",
            "surface_binding_ids": [],
            "superseded_by": "fixture.fake.new",
            "supersedes": [],
        }
    )
    successor.update(
        {
            "claim_id": "fixture.fake.new",
            "surface_binding_ids": [],
            "superseded_by": None,
            "supersedes": ["fixture.fake.old"],
        }
    )
    claims = {
        predecessor["claim_id"]: predecessor,
        successor["claim_id"]: successor,
    }
    failures = guard._supersession_failures(claims)
    assert any("lacks immutable sealed evidence" in item for item in failures)
    assert any("head is unbound" in item for item in failures)


def test_claim_schema_hostile_types_fail_without_throwing(
    tmp_path: Path,
) -> None:
    registry = _candidate(tmp_path)
    for field, value in (
        ("kind", {}),
        ("status", []),
        ("superseded_by", {}),
        ("supersedes", {}),
        ("missingness", []),
    ):
        hostile = deepcopy(registry)
        _, claim = _first_granular_claim(hostile)
        claim[field] = value
        failures, _ = _validate_candidate(
            tmp_path,
            hostile,
            authorize=registry,
        )
        assert failures

    for target, value in (
        ("category", {}),
        ("operator", []),
        ("classification", {}),
        ("digest_scope", []),
        ("digest_scope", {}),
        ("binding_id", []),
        ("surface_binding_ids", ["valid:binding", {}]),
    ):
        hostile = deepcopy(registry)
        if target == "category":
            binding = next(
                item
                for item in hostile["bindings"]
                if item["resolution"].get("type") == "typed_non_claim"
            )
            binding["resolution"]["category"] = value
        elif target == "operator":
            binding = next(
                item
                for item in hostile["bindings"]
                if item["resolution"].get("type") == "claim_projection"
            )
            binding["resolution"]["projection"]["operator"] = value
        elif target in {"classification", "digest_scope", "binding_id"}:
            _, claim = _first_granular_claim(hostile)
            claim["sources"][0][target] = value
        else:
            _, claim = _first_granular_claim(hostile)
            claim["surface_binding_ids"] = value
        failures, _ = _validate_candidate(
            tmp_path,
            hostile,
            authorize=registry,
        )
        assert failures


def test_projection_out_of_range_fails_without_throwing(
    tmp_path: Path,
) -> None:
    binding = _bindings_for_text(tmp_path, "Observed 7.")[0]
    matched, detail = guard.projection_matches(
        binding,
        {"value": []},
        {
            "operator": "equals",
            "pointer": "/value/4",
            "currency": False,
            "percent": False,
        },
    )
    assert not matched
    assert "cannot resolve" in detail


def test_successor_snapshot_exposes_exact_tree_membership(
    tmp_path: Path,
) -> None:
    repo = tmp_path / "repo"
    report = repo / "experiments/iter238_gate/proof/report.json"
    _write_json(report, {"accepted": True})
    subprocess.run(["git", "init", "-q", repo], check=True)
    subprocess.run(["git", "-C", repo, "add", "."], check=True)
    subprocess.run(
        [
            "git",
            "-C",
            repo,
            "-c",
            "user.name=Fixture",
            "-c",
            "user.email=fixture@example.com",
            "commit",
            "-qm",
            "fixture",
        ],
        check=True,
    )
    commit = subprocess.run(
        ["git", "-C", repo, "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    registry = {
        "records": [
            {
                "seal_id": "successor",
                "record_type": "successor_path_snapshot",
                "reference_commit": commit,
                "protected_sets": [
                    {
                        "selector": {
                            "kind": "tree",
                            "path": "experiments/iter238_gate",
                        }
                    }
                ],
            }
        ]
    }
    member, digest = guard._seal_membership(
        repo,
        registry,
        "successor",
        "experiments/iter238_gate/proof/report.json",
    )
    assert member
    assert digest == hashlib.sha256(report.read_bytes()).hexdigest()
    assert not guard._seal_membership(
        repo,
        registry,
        "successor",
        "experiments/other/report.json",
    )[0]


@pytest.mark.parametrize(
    "registry",
    [
        {"records": 0},
        {"records": [0]},
        {
            "records": [
                {
                    "seal_id": "broken",
                    "record_type": "successor_path_snapshot",
                    "reference_commit": "0" * 40,
                    "protected_sets": 0,
                }
            ]
        },
        {
            "records": [
                {
                    "seal_id": "broken",
                    "record_type": "successor_path_snapshot",
                    "reference_commit": "0" * 40,
                    "protected_sets": [0],
                }
            ]
        },
    ],
)
def test_malformed_seal_registry_fails_closed_without_exception(
    tmp_path: Path,
    registry: dict[str, object],
) -> None:
    member, detail = guard._seal_membership(
        tmp_path,
        registry,
        "broken",
        "proof/report.json",
    )
    assert not member
    assert isinstance(detail, str) and detail


def _prior_evidence_fixture(
    tmp_path: Path,
    *,
    binding_authority_passed: object,
) -> tuple[Path, dict[str, object], dict[str, str], str]:
    repo = tmp_path / "prior"
    gate = "experiments/iter238_gate/HYPOTHESIS.md"
    report_path = "experiments/iter238_gate/proof/claim_coverage_report.json"
    prior = {
        "active_gate": gate,
        "coverage_report_path": report_path,
    }
    registry_path = repo / guard.REGISTRY_PATH
    _write_json(registry_path, prior)
    registry_digest = hashlib.sha256(registry_path.read_bytes()).hexdigest()
    report = {
        "registry_sha256": registry_digest,
        "active_gate": gate,
        "unclassified_count": 0,
        "conflicting_projection_count": 0,
        "binding_authority_passed": binding_authority_passed,
        "internal_prerequisite_passed": True,
        "stale_superseded_assertion_count": 0,
        "verified_material_predecessor_ids": [],
    }
    report_file = repo / report_path
    _write_json(report_file, report)
    subprocess.run(["git", "init", "-q", repo], check=True)
    subprocess.run(["git", "-C", repo, "add", "."], check=True)
    subprocess.run(
        [
            "git",
            "-C",
            repo,
            "-c",
            "user.name=Fixture",
            "-c",
            "user.email=fixture@example.com",
            "commit",
            "-qm",
            "prior",
        ],
        check=True,
    )
    commit = subprocess.run(
        ["git", "-C", repo, "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    seal = {
        "records": [
            {
                "seal_id": "prior-successor",
                "record_type": "successor_path_snapshot",
                "reference_commit": commit,
                "protected_sets": [
                    {
                        "selector": {
                            "kind": "tree",
                            "path": "experiments/iter238_gate",
                        }
                    }
                ],
            }
        ]
    }
    _write_json(repo / guard.SEAL_REGISTRY_PATH, seal)
    evidence = {
        "commit": commit,
        "registry_path": guard.REGISTRY_PATH.as_posix(),
        "registry_sha256": registry_digest,
        "coverage_report_path": report_path,
        "coverage_report_sha256": hashlib.sha256(
            report_file.read_bytes()
        ).hexdigest(),
        "report_seal_id": "prior-successor",
    }
    return repo, prior, evidence, gate


def test_prior_registry_evidence_requires_accepted_sealed_report(
    tmp_path: Path,
) -> None:
    good_repo, prior, evidence, gate = _prior_evidence_fixture(
        tmp_path / "good",
        binding_authority_passed=True,
    )
    assert guard._prior_registry_from_evidence(
        good_repo,
        evidence,
        expected_active_gate=gate,
    ) == prior

    bad_repo, _, bad_evidence, bad_gate = _prior_evidence_fixture(
        tmp_path / "bad",
        binding_authority_passed=False,
    )
    with pytest.raises(ValueError, match="accepted C1 controls"):
        guard._prior_registry_from_evidence(
            bad_repo,
            bad_evidence,
            expected_active_gate=bad_gate,
        )
    typed_repo, _, typed_evidence, typed_gate = _prior_evidence_fixture(
        tmp_path / "typed",
        binding_authority_passed=1,
    )
    with pytest.raises(ValueError, match="accepted C1 controls"):
        guard._prior_registry_from_evidence(
            typed_repo,
            typed_evidence,
            expected_active_gate=typed_gate,
        )


def _commit_prior_claim_authority(
    root: Path,
    prior: dict[str, object],
    *,
    verified_material_predecessor_ids: tuple[str, ...] = (),
) -> dict[str, str]:
    registry_file = root / guard.REGISTRY_PATH
    _write_json(registry_file, prior)
    registry_digest = hashlib.sha256(registry_file.read_bytes()).hexdigest()
    report_path = prior["coverage_report_path"]
    assert isinstance(report_path, str)
    report_file = root / report_path
    _write_json(
        report_file,
        {
            "registry_sha256": registry_digest,
            "active_gate": prior["active_gate"],
            "unclassified_count": 0,
            "conflicting_projection_count": 0,
            "binding_authority_passed": True,
            "internal_prerequisite_passed": True,
            "stale_superseded_assertion_count": 0,
            "verified_material_predecessor_ids": sorted(
                verified_material_predecessor_ids
            ),
        },
    )
    subprocess.run(["git", "init", "-q", root], check=True)
    subprocess.run(["git", "-C", root, "add", "."], check=True)
    subprocess.run(
        [
            "git",
            "-C",
            root,
            "-c",
            "user.name=Fixture",
            "-c",
            "user.email=fixture@example.com",
            "commit",
            "-qm",
            "sealed prior claim authority",
        ],
        check=True,
    )
    commit = subprocess.run(
        ["git", "-C", root, "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    gate_parent = Path(prior["active_gate"]).parent.as_posix()
    seal_id = f"fixture-prior-successor-r{prior.get('revision', 'unknown')}"
    seal_path = root / guard.SEAL_REGISTRY_PATH
    try:
        seal_registry = guard.read_json(seal_path)
    except (OSError, ValueError):
        seal_registry = {"records": []}
    records = seal_registry.get("records")
    if not isinstance(records, list):
        records = []
        seal_registry = {"records": records}
    records.append(
        {
            "seal_id": seal_id,
            "record_type": "successor_path_snapshot",
            "reference_commit": commit,
            "protected_sets": [
                {
                    "selector": {
                        "kind": "tree",
                        "path": gate_parent,
                    }
                }
            ],
        }
    )
    _write_json(
        seal_path,
        seal_registry,
    )
    return {
        "commit": commit,
        "registry_path": guard.REGISTRY_PATH.as_posix(),
        "registry_sha256": registry_digest,
        "coverage_report_path": report_path,
        "coverage_report_sha256": hashlib.sha256(
            report_file.read_bytes()
        ).hexdigest(),
        "report_seal_id": seal_id,
    }


def test_future_gate_migration_replays_two_rebinds_add_remove_and_gate_change(
    tmp_path: Path,
) -> None:
    root = tmp_path / "migration-repo"
    _clone_current_evidence_context(root)
    prior = guard.bootstrap_registry(
        root,
        internal_claims=builder.build_internal_claims(),
    )
    evidence = _commit_prior_claim_authority(root, prior)
    prior_live = {
        binding.binding_id: binding
        for binding in guard.extract_all_bindings(root)
    }
    registered = {
        binding["binding_id"]: binding for binding in prior["bindings"]
    }

    grouped: dict[str, list[guard.AtomBinding]] = {}
    for binding_id, record in registered.items():
        resolution = record["resolution"]
        live = prior_live[binding_id]
        if (
            resolution.get("type") == "claim_projection"
            and resolution.get("claim_id")
            == "telos.recurrence.fixed_cohort"
            and len(live.segment.atoms) == 1
            and (root / live.segment.path)
            .read_text(encoding="utf-8")
            .count(live.segment.text)
            == 1
        ):
            grouped.setdefault(resolution["claim_id"], []).append(live)
    old_rebinds = grouped["telos.recurrence.fixed_cohort"][:2]
    assert len(old_rebinds) == 2
    replacement_texts: dict[str, str] = {}
    for index, binding in enumerate(old_rebinds, start=1):
        source = root / binding.segment.path
        text = source.read_text(encoding="utf-8")
        replacement_text = (
            binding.segment.text[:-1] + f" migrationword{index}."
            if binding.segment.text.endswith(".")
            else binding.segment.text + f" migrationword{index}"
        )
        assert text.count(binding.segment.text) == 1
        source.write_text(
            text.replace(binding.segment.text, replacement_text, 1),
            encoding="utf-8",
        )
        replacement_texts[binding.binding_id] = replacement_text

    removable = next(
        live
        for binding_id, live in prior_live.items()
        if registered[binding_id]["resolution"].get("type") == "typed_non_claim"
        and live.segment.path != "mission/current.json"
        and len(live.segment.atoms) == 1
        and (root / live.segment.path)
        .read_text(encoding="utf-8")
        .count(live.segment.text)
        == 1
        and not live.segment.text.lstrip().startswith("#")
    )
    removable_file = root / removable.segment.path
    removable_text = removable_file.read_text(encoding="utf-8")
    removable_file.write_text(
        removable_text.replace(
            removable.segment.text,
            "Migration fixture removed an obsolete identifier.",
            1,
        ),
        encoding="utf-8",
    )

    readme = root / "README.md"
    readme.write_text(
        readme.read_text(encoding="utf-8")
        + "\n\nMigration fixture protocol cap 17.\n",
        encoding="utf-8",
    )
    target_gate = (
        "experiments/iter239_claim_registry_migration/HYPOTHESIS.md"
    )
    current = guard.read_json(root / "mission/current.json")
    current["active_gate"] = target_gate
    _write_json(root / "mission/current.json", current)

    live = {
        binding.binding_id: binding
        for binding in guard.extract_all_bindings(root)
    }
    rebindings: list[dict[str, str]] = []
    for old in old_rebinds:
        replacement = next(
            binding
            for binding in live.values()
            if binding.segment.path == old.segment.path
            and binding.segment.text == replacement_texts[old.binding_id]
            and binding.atom.normalized == old.atom.normalized
        )
        rebindings.append(
            {
                "old_binding_id": old.binding_id,
                "new_binding_id": replacement.binding_id,
            }
        )

    old_gate_binding = next(
        (
            binding
            for binding in prior_live.values()
            if binding.segment.path == "mission/current.json"
            and binding.segment.locator == "/active_gate"
        ),
        None,
    )
    new_gate_binding = next(
        (
            binding
            for binding in live.values()
            if binding.segment.path == "mission/current.json"
            and binding.segment.locator == "/active_gate"
        ),
        None,
    )
    gate_updates: list[dict[str, object]] = []
    if (
        old_gate_binding is not None
        and new_gate_binding is not None
        and old_gate_binding.binding_id == new_gate_binding.binding_id
    ):
        gate_updates = [
            {
                "binding_id": old_gate_binding.binding_id,
                "new_resolution": guard.derive_nonclaim(new_gate_binding),
            }
        ]
    elif old_gate_binding is not None and new_gate_binding is not None:
        rebindings.append(
            {
                "old_binding_id": old_gate_binding.binding_id,
                "new_binding_id": new_gate_binding.binding_id,
            }
        )

    added = next(
        binding
        for binding in live.values()
        if binding.segment.text == "Migration fixture protocol cap 17."
    )
    new_claim_id = "fixture.migration.protocol_cap"
    new_claim = guard.build_retained_claim(
        root,
        added,
        guard._retained_kind(added),
        new_claim_id,
    )
    new_resolution = {
        "type": "claim_projection",
        "claim_id": new_claim_id,
        "projection": {
            "operator": "equals",
            "pointer": "/value/surface_atom",
            "currency": False,
            "percent": False,
        },
    }
    plan_path = (
        "experiments/iter239_claim_registry_migration/proof/"
        "claim_registry_migration.json"
    )
    plan = {
        "schema_version": guard.MIGRATION_SCHEMA_VERSION,
        "prior_registry_canonical_sha256": guard._canonical_json_sha256(prior),
        "from_active_gate": prior["active_gate"],
        "to_active_gate": target_gate,
        "plan_path": plan_path,
        "prior_registry_evidence": evidence,
        "rebindings": rebindings,
        "material_binding_updates": gate_updates,
        "lineage_binding_reassignments": [],
        "removed_binding_ids": [removable.binding_id],
        "new_binding_resolutions": {added.binding_id: new_resolution},
        "new_claims": {new_claim_id: new_claim},
        "claim_updates": {},
    }
    candidate = guard.build_migration_candidate(root, prior, plan)
    fixed_claim = "telos.recurrence.fixed_cohort"
    assert candidate["revision"] == prior["revision"] + 1
    assert candidate["claims"][fixed_claim]["revision"] == (
        prior["claims"][fixed_claim]["revision"] + 1
    )
    assert new_claim_id in candidate["claims"]
    assert removable.binding_id not in {
        binding["binding_id"] for binding in candidate["bindings"]
    }

    _write_json(root / plan_path, plan)
    _write_json(root / guard.REGISTRY_PATH, candidate)
    assert guard._migration_failures(root, candidate) == []
    gate = candidate["active_gate"]
    guard.AUTHORIZED_BINDING_INVENTORY_SHA256[gate] = (
        guard.binding_authorization_sha256(root, registry=candidate)
    )
    full_failures, _ = guard.validate(
        root=root,
        check_internal=False,
        check_source_digests=True,
        check_seals=True,
        check_report=False,
    )
    assert full_failures == []
    _, generated_report = guard.validate(
        root=root,
        check_internal=False,
        check_source_digests=True,
        check_seals=True,
        check_report=False,
    )
    _write_json(root / candidate["coverage_report_path"], generated_report)
    report_failures, _ = guard.validate(
        root=root,
        check_internal=False,
        check_source_digests=True,
        check_seals=True,
        check_report=True,
    )
    assert report_failures == []
    near_tolerance = deepcopy(candidate)
    near_tolerance["claims"][builder.SELECTOR_PREDECESSOR_CLAIM_ID][
        "value"
    ]["reported_p"] = 0.008000000004
    assert any(
        "replay differs exactly" in failure
        for failure in guard._migration_failures(root, near_tolerance)
    )
    drifted = deepcopy(plan)
    drifted["removed_binding_ids"] = []
    _write_json(root / plan_path, drifted)
    assert any(
        "plan digest differs" in failure
        for failure in guard._migration_failures(root, candidate)
    )


def _empty_migration_plan(
    prior: dict[str, object],
    *,
    claim_updates: dict[str, object] | None = None,
) -> dict[str, object]:
    gate = prior["active_gate"]
    return {
        "schema_version": guard.MIGRATION_SCHEMA_VERSION,
        "prior_registry_canonical_sha256": guard._canonical_json_sha256(prior),
        "from_active_gate": gate,
        "to_active_gate": gate,
        "plan_path": (
            f"{Path(gate).parent.as_posix()}/proof/"
            "claim_registry_migration.json"
        ),
        "prior_registry_evidence": {},
        "rebindings": [],
        "material_binding_updates": [],
        "lineage_binding_reassignments": [],
        "removed_binding_ids": [],
        "new_binding_resolutions": {},
        "new_claims": {},
        "claim_updates": claim_updates or {},
    }


def test_empty_and_revision_only_migrations_are_rejected(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = tmp_path / "no-op"
    _copy_surfaces(root)
    prior = guard.bootstrap_registry(
        root,
        internal_claims=builder.build_internal_claims(),
    )
    monkeypatch.setattr(
        guard,
        "_prior_registry_from_evidence",
        lambda *args, **kwargs: prior,
    )
    with pytest.raises(ValueError, match="no reviewed transition"):
        guard.build_migration_candidate(
            root,
            prior,
            _empty_migration_plan(prior),
            require_current_prior=False,
        )
    claim_id, claim = _first_granular_claim(prior)
    update = deepcopy(claim)
    update["revision"] += 1
    with pytest.raises(ValueError, match="revision-only no-op"):
        guard.build_migration_candidate(
            root,
            prior,
            _empty_migration_plan(
                prior,
                claim_updates={claim_id: update},
            ),
            require_current_prior=False,
        )


def test_same_binding_material_correction_requires_new_reciprocal_lineage(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = tmp_path / "material"
    root.mkdir()
    (root / "README.md").write_text(
        "# Material fixture\n\nObserved outcome 7.\n",
        encoding="utf-8",
    )
    gate = "experiments/iter238_material_fixture/HYPOTHESIS.md"
    _write_json(root / "mission/current.json", {"active_gate": gate})
    monkeypatch.setattr(
        guard,
        "declared_surface_paths",
        lambda _root=root: ("README.md",),
    )
    old = guard.extract_all_bindings(root)[0]
    old_claim_id = "fixture.material.old"
    prior_claim = guard.build_retained_claim(
        root,
        old,
        "historical_empirical",
        old_claim_id,
    )
    old_resolution = {
        "type": "claim_projection",
        "claim_id": old_claim_id,
        "projection": {
            "operator": "equals",
            "pointer": "/value/surface_atom",
            "currency": False,
            "percent": False,
        },
    }
    prior = {
        "schema_version": guard.SCHEMA_VERSION,
        "revision": 2,
        "active_gate": gate,
        "coverage_report_path": guard.report_path_for_gate(gate),
        "migration": None,
        "declared_surfaces": [
            {
                "path": "README.md",
                "format": "markdown",
                "sha256": guard.sha256(root / "README.md"),
            }
        ],
        "non_claim_categories": sorted(guard.ALLOWED_NONCLAIM_CATEGORIES),
        "claim_kinds": sorted(guard.ALLOWED_CLAIM_KINDS),
        "claims": {old_claim_id: prior_claim},
        "bindings": [guard._live_binding_record(old, old_resolution)],
    }
    evidence = _commit_prior_claim_authority(root, prior)

    (root / "README.md").write_text(
        "# Material fixture\n\nObserved outcome 8.\n",
        encoding="utf-8",
    )
    changed = guard.extract_all_bindings(root)[0]
    assert changed.binding_id == old.binding_id
    assert changed.atom.normalized != old.atom.normalized

    new_claim_id = f"{old_claim_id}.corrected"
    successor = guard.build_retained_claim(
        root,
        changed,
        "historical_empirical",
        new_claim_id,
    )
    successor["supersedes"] = [old_claim_id]
    predecessor = deepcopy(prior["claims"][old_claim_id])
    predecessor["revision"] += 1
    predecessor["status"] = "corrected"
    predecessor["superseded_by"] = new_claim_id
    predecessor["surface_binding_ids"] = []
    predecessor["missingness"].pop("binding_id", None)
    prior_segment_source = prior_claim["sources"][0]
    predecessor["sources"] = [
        {
            "path": prior_segment_source["path"],
            "sha256": prior_segment_source["sha256"],
            "classification": "historical_git_blob",
            "seal_ids": [],
            "digest_scope": "normalized_surface_segment_at_commit",
            "reference_commit": evidence["commit"],
            "binding_id": old.binding_id,
        }
    ]
    resolution = {
        "type": "claim_projection",
        "claim_id": new_claim_id,
        "projection": {
            "operator": "equals",
            "pointer": "/value/surface_atom",
            "currency": changed.atom.normalized.get("currency", False),
            "percent": changed.atom.normalized.get("percent", False),
        },
    }
    plan = _empty_migration_plan(
        prior,
        claim_updates={old_claim_id: predecessor},
    )
    plan["prior_registry_evidence"] = evidence
    plan["material_binding_updates"] = [
        {
            "binding_id": old.binding_id,
            "new_resolution": resolution,
        }
    ]
    plan["new_claims"] = {new_claim_id: successor}
    candidate = guard.build_migration_candidate(
        root,
        prior,
        plan,
    )
    assert candidate["claims"][old_claim_id]["revision"] == (
        prior["claims"][old_claim_id]["revision"] + 1
    )
    assert candidate["claims"][new_claim_id]["revision"] == 1
    assert candidate["claims"][old_claim_id]["superseded_by"] == new_claim_id
    assert old_claim_id in candidate["claims"][new_claim_id]["supersedes"]

    _write_json(root / plan["plan_path"], plan)
    _write_json(root / guard.REGISTRY_PATH, candidate)
    gate = candidate["active_gate"]
    guard.AUTHORIZED_BINDING_INVENTORY_SHA256[gate] = (
        guard.binding_authorization_sha256(root, registry=candidate)
    )
    failures, _ = guard.validate(
        root=root,
        check_internal=False,
        check_source_digests=True,
        check_seals=True,
        check_report=False,
    )
    assert failures == []

    for field, value in (
        ("reference_commit", "0" * 40),
        ("sha256", "0" * 64),
        ("binding_id", "wrong:binding"),
    ):
        malformed = deepcopy(plan)
        malformed["claim_updates"][old_claim_id]["sources"][0][field] = value
        with pytest.raises(ValueError, match="provenance transition differs"):
            guard.build_migration_candidate(
                root,
                prior,
                malformed,
                require_current_prior=False,
            )

    in_place = deepcopy(plan)
    in_place["material_binding_updates"][0]["new_resolution"][
        "claim_id"
    ] = old_claim_id
    in_place["new_claims"] = {}
    in_place["claim_updates"] = {}
    with pytest.raises(ValueError, match="distinct explicit"):
        guard.build_migration_candidate(
            root,
            prior,
            in_place,
            require_current_prior=False,
        )

    (root / "README.md").write_text(
        "# Material fixture\n\nReworded outcome 9.\n",
        encoding="utf-8",
    )
    structurally_new = guard.extract_all_bindings(root)[0]
    assert structurally_new.binding_id != old.binding_id
    implicit_claim_id = "fixture.material.implicit"
    implicit_successor = guard.build_retained_claim(
        root,
        structurally_new,
        "historical_empirical",
        implicit_claim_id,
    )
    implicit_successor["supersedes"] = [old_claim_id]
    implicit_predecessor = deepcopy(prior_claim)
    implicit_predecessor["revision"] += 1
    implicit_predecessor["status"] = "corrected"
    implicit_predecessor["superseded_by"] = implicit_claim_id
    implicit_predecessor["surface_binding_ids"] = []
    implicit_predecessor["missingness"].pop("binding_id", None)
    implicit_plan = _empty_migration_plan(
        prior,
        claim_updates={old_claim_id: implicit_predecessor},
    )
    implicit_plan["prior_registry_evidence"] = evidence
    implicit_plan["removed_binding_ids"] = [old.binding_id]
    implicit_plan["new_binding_resolutions"] = {
        structurally_new.binding_id: {
            "type": "claim_projection",
            "claim_id": implicit_claim_id,
            "projection": {
                "operator": "equals",
                "pointer": "/value/surface_atom",
                "currency": False,
                "percent": False,
            },
        }
    }
    implicit_plan["new_claims"] = {
        implicit_claim_id: implicit_successor
    }
    with pytest.raises(ValueError, match="explicit reciprocal material"):
        guard.build_migration_candidate(
            root,
            prior,
            implicit_plan,
            require_current_prior=False,
        )


def test_internal_multi_binding_material_correction_reassigns_all_lineage(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = tmp_path / "internal-material"
    root.mkdir()
    (root / "README.md").write_text(
        "# Internal material fixture\n\n"
        "Primary outcome 7. Sibling outcome 3.\n",
        encoding="utf-8",
    )
    proof_path = "proof/internal_source.json"
    _write_json(
        root / proof_path,
        {"old_primary": 7, "new_primary": 8, "sibling": 3},
    )
    source = {
        "path": proof_path,
        "sha256": guard.sha256(root / proof_path),
        "classification": "mutable",
        "seal_ids": [],
    }
    gate = "experiments/iter238_internal_material/HYPOTHESIS.md"
    _write_json(root / "mission/current.json", {"active_gate": gate})
    monkeypatch.setattr(
        guard,
        "declared_surface_paths",
        lambda _root=root: ("README.md",),
    )
    prior_bindings = guard.extract_all_bindings(root)
    assert len(prior_bindings) == 2
    primary, sibling = prior_bindings
    old_claim_id = "fixture.internal.old"
    prior_claim = builder.claim(
        claim_id=old_claim_id,
        status="supported",
        unit="fixture outcome",
        cohort="one retained fixture cohort",
        independence_boundary="fixture rows are not independent",
        value={"primary": 7, "sibling": 3},
        missingness={
            "mode": "not_applicable",
            "reason": "fixture values are observed",
        },
        excluded_inferences=["no population inference"],
        sources=[source],
    )
    prior_claim["surface_binding_ids"] = sorted(
        [primary.binding_id, sibling.binding_id]
    )

    def resolution(
        claim_id: str,
        pointer: str,
    ) -> dict[str, object]:
        return {
            "type": "claim_projection",
            "claim_id": claim_id,
            "projection": {
                "operator": "equals",
                "pointer": pointer,
                "currency": False,
                "percent": False,
            },
        }

    prior = {
        "schema_version": guard.SCHEMA_VERSION,
        "revision": 2,
        "active_gate": gate,
        "coverage_report_path": guard.report_path_for_gate(gate),
        "migration": None,
        "declared_surfaces": [
            {
                "path": "README.md",
                "format": "markdown",
                "sha256": guard.sha256(root / "README.md"),
            }
        ],
        "non_claim_categories": sorted(guard.ALLOWED_NONCLAIM_CATEGORIES),
        "claim_kinds": sorted(guard.ALLOWED_CLAIM_KINDS),
        "claims": {old_claim_id: prior_claim},
        "bindings": sorted(
            [
                guard._live_binding_record(
                    primary,
                    resolution(old_claim_id, "/value/primary"),
                ),
                guard._live_binding_record(
                    sibling,
                    resolution(old_claim_id, "/value/sibling"),
                ),
            ],
            key=lambda item: item["binding_id"],
        ),
    }
    evidence = _commit_prior_claim_authority(root, prior)
    readme = root / "README.md"
    readme.write_text(
        readme.read_text(encoding="utf-8").replace(
            "Primary outcome 7.",
            "Primary outcome 8.",
        ),
        encoding="utf-8",
    )
    live_by_text = {
        binding.segment.text: binding
        for binding in guard.extract_all_bindings(root)
    }
    changed = live_by_text["Primary outcome 8."]
    unchanged = live_by_text["Sibling outcome 3."]
    assert changed.binding_id == primary.binding_id
    assert unchanged.binding_id == sibling.binding_id

    new_claim_id = "fixture.internal.corrected"
    successor = builder.claim(
        claim_id=new_claim_id,
        status="supported",
        unit=prior_claim["unit"],
        cohort=prior_claim["cohort"],
        independence_boundary=prior_claim["independence_boundary"],
        value={"primary": 8, "sibling": 3},
        missingness=deepcopy(prior_claim["missingness"]),
        excluded_inferences=deepcopy(prior_claim["excluded_inferences"]),
        sources=[deepcopy(source)],
        supersedes=[old_claim_id],
    )
    successor["surface_binding_ids"] = sorted(
        [changed.binding_id, unchanged.binding_id]
    )
    predecessor = deepcopy(prior_claim)
    predecessor["revision"] += 1
    predecessor["status"] = "corrected"
    predecessor["superseded_by"] = new_claim_id
    predecessor["surface_binding_ids"] = []
    historical_sources = {
        binding.binding_id: guard._prior_binding_historical_source(
            root,
            prior,
            next(
                record
                for record in prior["bindings"]
                if record["binding_id"] == binding.binding_id
            ),
            evidence["commit"],
        )
        for binding in (primary, sibling)
    }
    predecessor["sources"] = guard._expected_material_predecessor_sources(
        prior_claim,
        historical_sources,
    )
    material_resolution = resolution(new_claim_id, "/value/primary")
    sibling_resolution = resolution(new_claim_id, "/value/sibling")
    plan = _empty_migration_plan(
        prior,
        claim_updates={old_claim_id: predecessor},
    )
    plan["prior_registry_evidence"] = evidence
    plan["material_binding_updates"] = [
        {
            "binding_id": changed.binding_id,
            "new_resolution": material_resolution,
        }
    ]
    plan["lineage_binding_reassignments"] = [
        {
            "binding_id": unchanged.binding_id,
            "new_resolution": sibling_resolution,
        }
    ]
    plan["new_claims"] = {new_claim_id: successor}

    candidate = guard.build_migration_candidate(root, prior, plan)
    _write_json(root / plan["plan_path"], plan)
    _write_json(root / guard.REGISTRY_PATH, candidate)
    guard.AUTHORIZED_BINDING_INVENTORY_SHA256[gate] = (
        guard.binding_authorization_sha256(root, registry=candidate)
    )
    failures, report = guard.validate(
        root=root,
        check_internal=False,
        check_source_digests=True,
        check_seals=True,
        check_report=False,
    )
    assert failures == []
    assert report["verified_material_predecessor_ids"] == [old_claim_id]

    incomplete = deepcopy(plan)
    incomplete["lineage_binding_reassignments"] = []
    incomplete["claim_updates"][old_claim_id]["sources"] = (
        guard._expected_material_predecessor_sources(
            prior_claim,
            {primary.binding_id: historical_sources[primary.binding_id]},
        )
    )
    with pytest.raises(ValueError, match="leaves non-corrective"):
        guard.build_migration_candidate(
            root,
            prior,
            incomplete,
            require_current_prior=False,
        )
    duplicated = deepcopy(plan)
    duplicated["lineage_binding_reassignments"].append(
        deepcopy(duplicated["lineage_binding_reassignments"][0])
    )
    with pytest.raises(ValueError, match="duplicated or overlaps"):
        guard.build_migration_candidate(
            root,
            prior,
            duplicated,
            require_current_prior=False,
        )
    overlapping = deepcopy(plan)
    overlapping["lineage_binding_reassignments"].append(
        {
            "binding_id": changed.binding_id,
            "new_resolution": material_resolution,
        }
    )
    with pytest.raises(ValueError, match="duplicated or overlaps"):
        guard.build_migration_candidate(
            root,
            prior,
            overlapping,
            require_current_prior=False,
        )
    wrong_successor = deepcopy(plan)
    wrong_successor["lineage_binding_reassignments"][0]["new_resolution"][
        "claim_id"
    ] = "fixture.internal.wrong"
    with pytest.raises(ValueError, match="reciprocal material successor"):
        guard.build_migration_candidate(
            root,
            prior,
            wrong_successor,
            require_current_prior=False,
        )
    wrong_projection = deepcopy(plan)
    wrong_projection["lineage_binding_reassignments"][0]["new_resolution"][
        "projection"
    ]["pointer"] = "/value/primary"
    with pytest.raises(ValueError, match="projection conflicts"):
        guard.build_migration_candidate(
            root,
            prior,
            wrong_projection,
            require_current_prior=False,
        )
    incomplete_reverse = deepcopy(plan)
    incomplete_reverse["new_claims"][new_claim_id][
        "surface_binding_ids"
    ].remove(unchanged.binding_id)
    with pytest.raises(ValueError, match="reciprocity is incomplete"):
        guard.build_migration_candidate(
            root,
            prior,
            incomplete_reverse,
            require_current_prior=False,
        )
    dropped_source = deepcopy(plan)
    dropped_source["claim_updates"][old_claim_id]["sources"] = [
        source
        for source in dropped_source["claim_updates"][old_claim_id][
            "sources"
        ]
        if source.get("path") != proof_path
    ]
    with pytest.raises(ValueError, match="provenance transition differs"):
        guard.build_migration_candidate(
            root,
            prior,
            dropped_source,
            require_current_prior=False,
        )
    forged_source = deepcopy(plan)
    forged_source["claim_updates"][old_claim_id]["sources"][-1][
        "sha256"
    ] = "0" * 64
    with pytest.raises(ValueError, match="provenance transition differs"):
        guard.build_migration_candidate(
            root,
            prior,
            forged_source,
            require_current_prior=False,
        )
    derivation_drift = deepcopy(plan)
    derivation_drift["claim_updates"][old_claim_id]["derivation"][
        "argv"
    ].append("--forged")
    with pytest.raises(ValueError, match="material semantics"):
        guard.build_migration_candidate(
            root,
            prior,
            derivation_drift,
            require_current_prior=False,
        )


@pytest.mark.parametrize("field", ["normalized", "role"])
def test_sealed_prior_binding_atom_and_role_are_reconstructed_exactly(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    field: str,
) -> None:
    root = tmp_path / field
    root.mkdir()
    (root / "README.md").write_text(
        "# Reconstruction fixture\n\nObserved 7.\n",
        encoding="utf-8",
    )
    gate = "experiments/iter238_reconstruction/HYPOTHESIS.md"
    _write_json(root / "mission/current.json", {"active_gate": gate})
    monkeypatch.setattr(
        guard,
        "declared_surface_paths",
        lambda _root=root: ("README.md",),
    )
    binding = guard.extract_all_bindings(root)[0]
    record = guard._live_binding_record(
        binding,
        guard.derive_nonclaim(binding)
        or {
            "type": "typed_non_claim",
            "category": "protocol_parameter",
            "rule": "fixture",
        },
    )
    if field == "normalized":
        record["atom"]["normalized"] = {
            "numeric_type": "integer",
            "value": 999,
        }
    else:
        record["role"] = "explicit_missingness"
    prior = {
        "schema_version": guard.SCHEMA_VERSION,
        "revision": 2,
        "active_gate": gate,
        "coverage_report_path": guard.report_path_for_gate(gate),
        "migration": None,
        "declared_surfaces": [
            {
                "path": "README.md",
                "format": "markdown",
                "sha256": guard.sha256(root / "README.md"),
            }
        ],
        "non_claim_categories": sorted(guard.ALLOWED_NONCLAIM_CATEGORIES),
        "claim_kinds": sorted(guard.ALLOWED_CLAIM_KINDS),
        "claims": {},
        "bindings": [record],
    }
    evidence = _commit_prior_claim_authority(root, prior)
    with pytest.raises(ValueError, match="prior atom/role differs"):
        guard._prior_binding_historical_source(
            root,
            prior,
            record,
            evidence["commit"],
        )


def test_material_lineage_survives_wording_chain_and_later_migration(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = tmp_path / "lineage-generations"
    root.mkdir()
    (root / "README.md").write_text(
        "# Lineage generations\n\nObserved outcome 7.\n",
        encoding="utf-8",
    )
    gate = "experiments/iter238_lineage_generations/HYPOTHESIS.md"
    _write_json(root / "mission/current.json", {"active_gate": gate})
    monkeypatch.setattr(
        guard,
        "declared_surface_paths",
        lambda _root=root: ("README.md",),
    )

    def resolution(
        claim_id: str,
    ) -> dict[str, object]:
        return {
            "type": "claim_projection",
            "claim_id": claim_id,
            "projection": {
                "operator": "equals",
                "pointer": "/value/surface_atom",
                "currency": False,
                "percent": False,
            },
        }

    initial_binding = guard.extract_all_bindings(root)[0]
    claim_a = "fixture.chain.a"
    initial_claim = guard.build_retained_claim(
        root,
        initial_binding,
        "historical_empirical",
        claim_a,
    )
    initial = {
        "schema_version": guard.SCHEMA_VERSION,
        "revision": 2,
        "active_gate": gate,
        "coverage_report_path": guard.report_path_for_gate(gate),
        "migration": None,
        "declared_surfaces": [
            {
                "path": "README.md",
                "format": "markdown",
                "sha256": guard.sha256(root / "README.md"),
            }
        ],
        "non_claim_categories": sorted(guard.ALLOWED_NONCLAIM_CATEGORIES),
        "claim_kinds": sorted(guard.ALLOWED_CLAIM_KINDS),
        "claims": {claim_a: initial_claim},
        "bindings": [
            guard._live_binding_record(
                initial_binding,
                resolution(claim_a),
            )
        ],
    }
    evidence = _commit_prior_claim_authority(root, initial)

    def material_successor(
        prior: dict[str, object],
        prior_evidence: dict[str, str],
        predecessor_id: str,
        successor_id: str,
        old_binding: guard.AtomBinding,
        new_binding: guard.AtomBinding,
    ) -> tuple[dict[str, object], dict[str, object]]:
        successor = guard.build_retained_claim(
            root,
            new_binding,
            "historical_empirical",
            successor_id,
        )
        successor["supersedes"] = [predecessor_id]
        predecessor = deepcopy(prior["claims"][predecessor_id])
        predecessor["revision"] += 1
        predecessor["status"] = "corrected"
        predecessor["superseded_by"] = successor_id
        predecessor["surface_binding_ids"] = []
        predecessor["missingness"].pop("binding_id", None)
        prior_record = next(
            record
            for record in prior["bindings"]
            if record["binding_id"] == old_binding.binding_id
        )
        historical = guard._prior_binding_historical_source(
            root,
            prior,
            prior_record,
            prior_evidence["commit"],
        )
        predecessor["sources"] = (
            guard._expected_material_predecessor_sources(
                prior["claims"][predecessor_id],
                {old_binding.binding_id: historical},
            )
        )
        plan = _empty_migration_plan(
            prior,
            claim_updates={predecessor_id: predecessor},
        )
        plan["prior_registry_evidence"] = prior_evidence
        plan["material_binding_updates"] = [
            {
                "binding_id": new_binding.binding_id,
                "new_resolution": resolution(successor_id),
            }
        ]
        plan["new_claims"] = {successor_id: successor}
        return guard.build_migration_candidate(root, prior, plan), plan

    def validate_and_seal(
        candidate: dict[str, object],
        plan: dict[str, object],
        expected_verified: list[str],
    ) -> dict[str, str]:
        _write_json(root / plan["plan_path"], plan)
        _write_json(root / guard.REGISTRY_PATH, candidate)
        guard.AUTHORIZED_BINDING_INVENTORY_SHA256[gate] = (
            guard.binding_authorization_sha256(
                root,
                registry=candidate,
            )
        )
        failures, report = guard.validate(
            root=root,
            check_internal=False,
            check_source_digests=True,
            check_seals=True,
            check_report=False,
        )
        assert failures == []
        assert report["verified_material_predecessor_ids"] == expected_verified
        _write_json(root / candidate["coverage_report_path"], report)
        retained_failures, _ = guard.validate(
            root=root,
            check_internal=False,
            check_source_digests=True,
            check_seals=True,
            check_report=True,
        )
        assert retained_failures == []
        return _commit_prior_claim_authority(
            root,
            candidate,
            verified_material_predecessor_ids=tuple(expected_verified),
        )

    (root / "README.md").write_text(
        "# Lineage generations\n\nObserved outcome 8.\n",
        encoding="utf-8",
    )
    binding_b = guard.extract_all_bindings(root)[0]
    assert binding_b.binding_id == initial_binding.binding_id
    claim_b = "fixture.chain.b"
    registry_b, plan_b = material_successor(
        initial,
        evidence,
        claim_a,
        claim_b,
        initial_binding,
        binding_b,
    )
    evidence_b = validate_and_seal(registry_b, plan_b, [claim_a])

    (root / "README.md").write_text(
        "# Lineage generations\n\nReworded observed outcome 8.\n",
        encoding="utf-8",
    )
    reworded_b = guard.extract_all_bindings(root)[0]
    assert reworded_b.binding_id != binding_b.binding_id
    wording_plan = _empty_migration_plan(registry_b)
    wording_plan["prior_registry_evidence"] = evidence_b
    wording_plan["rebindings"] = [
        {
            "old_binding_id": binding_b.binding_id,
            "new_binding_id": reworded_b.binding_id,
        }
    ]
    wording_registry = guard.build_migration_candidate(
        root,
        registry_b,
        wording_plan,
    )
    assert wording_registry["claims"][claim_b]["supersedes"] == [claim_a]
    evidence_wording = validate_and_seal(
        wording_registry,
        wording_plan,
        [claim_a],
    )

    (root / "README.md").write_text(
        "# Lineage generations\n\nReworded observed outcome 9.\n",
        encoding="utf-8",
    )
    binding_c = guard.extract_all_bindings(root)[0]
    assert binding_c.binding_id == reworded_b.binding_id
    claim_c = "fixture.chain.c"
    registry_c, plan_c = material_successor(
        wording_registry,
        evidence_wording,
        claim_b,
        claim_c,
        reworded_b,
        binding_c,
    )
    evidence_c = validate_and_seal(
        registry_c,
        plan_c,
        [claim_a, claim_b],
    )

    (root / "README.md").write_text(
        (root / "README.md").read_text(encoding="utf-8")
        + "\nRuntime version v3.0.0.\n",
        encoding="utf-8",
    )
    added = next(
        binding
        for binding in guard.extract_all_bindings(root)
        if binding.binding_id
        not in {
            record["binding_id"] for record in registry_c["bindings"]
        }
    )
    nonclaim = guard.derive_nonclaim(added)
    assert nonclaim is not None
    unrelated_plan = _empty_migration_plan(registry_c)
    unrelated_plan["prior_registry_evidence"] = evidence_c
    unrelated_plan["new_binding_resolutions"] = {
        added.binding_id: nonclaim
    }
    unrelated = guard.build_migration_candidate(
        root,
        registry_c,
        unrelated_plan,
    )
    validate_and_seal(
        unrelated,
        unrelated_plan,
        [claim_a, claim_b],
    )

    unplanned = deepcopy(unrelated)
    unplanned["claims"][claim_c]["value"]["surface_atom"]["value"] = 10
    assert any(
        "replay differs exactly" in failure
        for failure in guard._migration_failures(root, unplanned)
    )


def test_internal_wording_rebind_cannot_absorb_builder_science_drift(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = tmp_path / "internal-wording"
    root.mkdir()
    (root / "README.md").write_text(
        "# Internal wording\n\nObserved internal value 7.\n",
        encoding="utf-8",
    )
    proof_path = "proof/internal.json"
    _write_json(root / proof_path, {"value": 7})
    gate = "experiments/iter238_internal_wording/HYPOTHESIS.md"
    _write_json(root / "mission/current.json", {"active_gate": gate})
    monkeypatch.setattr(
        guard,
        "declared_surface_paths",
        lambda _root=root: ("README.md",),
    )
    old_binding = guard.extract_all_bindings(root)[0]
    claim_id = "fixture.internal.wording"
    source = {
        "path": proof_path,
        "sha256": guard.sha256(root / proof_path),
        "classification": "mutable",
        "seal_ids": [],
    }
    claim = builder.claim(
        claim_id=claim_id,
        status="supported",
        unit="fixture value",
        cohort="one fixture",
        independence_boundary="not an independent population sample",
        value={"observed": 7},
        missingness={
            "mode": "not_applicable",
            "reason": "fixture value is present",
        },
        excluded_inferences=["no population inference"],
        sources=[source],
    )
    claim["surface_binding_ids"] = [old_binding.binding_id]
    resolution = {
        "type": "claim_projection",
        "claim_id": claim_id,
        "projection": {
            "operator": "equals",
            "pointer": "/value/observed",
            "currency": False,
            "percent": False,
        },
    }
    prior = {
        "schema_version": guard.SCHEMA_VERSION,
        "revision": 2,
        "active_gate": gate,
        "coverage_report_path": guard.report_path_for_gate(gate),
        "migration": None,
        "declared_surfaces": [
            {
                "path": "README.md",
                "format": "markdown",
                "sha256": guard.sha256(root / "README.md"),
            }
        ],
        "non_claim_categories": sorted(guard.ALLOWED_NONCLAIM_CATEGORIES),
        "claim_kinds": sorted(guard.ALLOWED_CLAIM_KINDS),
        "claims": {claim_id: claim},
        "bindings": [
            guard._live_binding_record(old_binding, resolution)
        ],
    }
    evidence = _commit_prior_claim_authority(root, prior)
    (root / "README.md").write_text(
        "# Internal wording\n\nReworded internal value 7.\n",
        encoding="utf-8",
    )
    replacement = guard.extract_all_bindings(root)[0]
    assert replacement.binding_id != old_binding.binding_id
    plan = _empty_migration_plan(prior)
    plan["prior_registry_evidence"] = evidence
    plan["rebindings"] = [
        {
            "old_binding_id": old_binding.binding_id,
            "new_binding_id": replacement.binding_id,
        }
    ]
    regenerated = deepcopy(claim)
    regenerated["revision"] = 1
    regenerated["surface_binding_ids"] = []
    monkeypatch.setattr(
        builder,
        "build_internal_claims",
        lambda: {claim_id: deepcopy(regenerated)},
    )
    candidate = guard.build_migration_candidate(root, prior, plan)
    assert candidate["claims"][claim_id]["value"] == claim["value"]

    for mutation in ("value", "derivation", "sources"):
        drifted = deepcopy(regenerated)
        if mutation == "value":
            drifted["value"]["observed"] = 8
        elif mutation == "derivation":
            drifted["derivation"]["argv"].append("--forged")
        else:
            drifted["sources"][0]["sha256"] = "0" * 64
        monkeypatch.setattr(
            builder,
            "build_internal_claims",
            lambda drifted=drifted: {claim_id: deepcopy(drifted)},
        )
        with pytest.raises(
            ValueError,
            match="internal wording rebind changed material",
        ):
            guard.build_migration_candidate(
                root,
                prior,
                plan,
                require_current_prior=False,
            )


def test_curated_lineage_wording_rebind_allows_only_exact_source_refresh(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = tmp_path / "curated-wording"
    root.mkdir()
    (root / "README.md").write_text(
        "# Curated wording\n\nCorrected historical value 7.\n",
        encoding="utf-8",
    )
    gate = "experiments/iter238_curated_wording/HYPOTHESIS.md"
    _write_json(root / "mission/current.json", {"active_gate": gate})
    monkeypatch.setattr(
        guard,
        "declared_surface_paths",
        lambda _root=root: ("README.md",),
    )
    old_binding = guard.extract_all_bindings(root)[0]
    claim_id = builder.SELECTOR_PREDECESSOR_CLAIM_ID
    claim = guard.build_retained_claim(
        root,
        old_binding,
        "historical_empirical",
        claim_id,
    )
    claim["missingness"].pop("binding_id", None)
    resolution = {
        "type": "claim_projection",
        "claim_id": claim_id,
        "projection": {
            "operator": "equals",
            "pointer": "/value/surface_atom",
            "currency": False,
            "percent": False,
        },
    }
    prior = {
        "schema_version": guard.SCHEMA_VERSION,
        "revision": 2,
        "active_gate": gate,
        "coverage_report_path": guard.report_path_for_gate(gate),
        "migration": None,
        "declared_surfaces": [
            {
                "path": "README.md",
                "format": "markdown",
                "sha256": guard.sha256(root / "README.md"),
            }
        ],
        "non_claim_categories": sorted(guard.ALLOWED_NONCLAIM_CATEGORIES),
        "claim_kinds": sorted(guard.ALLOWED_CLAIM_KINDS),
        "claims": {claim_id: claim},
        "bindings": [
            guard._live_binding_record(old_binding, resolution)
        ],
    }
    _write_json(root / guard.REGISTRY_PATH, prior)
    monkeypatch.setattr(
        guard,
        "_prior_registry_from_evidence",
        lambda *args, **kwargs: prior,
    )
    (root / "README.md").write_text(
        "# Curated wording\n\nReworded corrected historical value 7.\n",
        encoding="utf-8",
    )
    replacement = guard.extract_all_bindings(root)[0]
    rebuilt = guard.build_retained_claim(
        root,
        replacement,
        "historical_empirical",
        claim_id,
    )
    rebuilt["missingness"].pop("binding_id", None)
    plan = _empty_migration_plan(prior)
    plan["rebindings"] = [
        {
            "old_binding_id": old_binding.binding_id,
            "new_binding_id": replacement.binding_id,
        }
    ]
    monkeypatch.setattr(
        guard,
        "build_curated_lineage_claims",
        lambda _root=root: {claim_id: deepcopy(rebuilt)},
    )
    candidate = guard.build_migration_candidate(root, prior, plan)
    assert candidate["claims"][claim_id]["value"] == claim["value"]

    for mutation in ("value", "derivation", "sources"):
        drifted = deepcopy(rebuilt)
        if mutation == "value":
            drifted["value"]["surface_atom"]["value"] = 8
        elif mutation == "derivation":
            drifted["derivation"]["argv"].append("--forged")
        else:
            drifted["sources"].append(deepcopy(drifted["sources"][0]))
        monkeypatch.setattr(
            guard,
            "build_curated_lineage_claims",
            lambda _root=root, drifted=drifted: {
                claim_id: deepcopy(drifted)
            },
        )
        with pytest.raises(
            ValueError,
            match="curated lineage",
        ):
            guard.build_migration_candidate(
                root,
                prior,
                plan,
                require_current_prior=False,
            )


def test_bootstrap_is_initial_only(tmp_path: Path) -> None:
    _copy_surfaces(tmp_path)
    target = tmp_path / guard.REGISTRY_PATH
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("{}\n", encoding="utf-8")
    with pytest.raises(ValueError, match="already exists"):
        guard.bootstrap_registry(tmp_path, internal_claims={})


def test_duplicate_and_nonfinite_json_are_rejected(tmp_path: Path) -> None:
    duplicate = tmp_path / "duplicate.json"
    duplicate.write_text('{"revision": 1, "revision": 2}\n', encoding="utf-8")
    with pytest.raises(guard.DuplicateKeyError):
        guard.read_json(duplicate)
    nonfinite = tmp_path / "nonfinite.json"
    nonfinite.write_text('{"revision": NaN}\n', encoding="utf-8")
    with pytest.raises(ValueError, match="non-finite"):
        guard.read_json(nonfinite)
