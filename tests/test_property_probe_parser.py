from __future__ import annotations

import json

from telos.property_probe_parser import output_schema, parse_property_probe_output


def _valid_payload(**overrides: object) -> str:
    payload: dict[str, object] = {
        "confidence": 0.8,
        "execution_sketch": "Run the generated check against issue-shaped inputs.",
        "input_generation_plan": "Generate multiple unseen boundary-shaped inputs.",
        "non_applicability_reason": None,
        "oracle_description": "The oracle checks the public behavior promised by the issue text.",
        "probe_strategy": "contract_property",
        "property_description": "The public contract should hold without special-casing one example.",
        "property_name": "public contract holds",
        "target_behavior": "The implementation should satisfy the issue behavior for equivalent inputs.",
    }
    payload.update(overrides)
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))


def test_schema_exposes_required_contract() -> None:
    schema = output_schema()

    assert schema["additionalProperties"] is False
    assert "probe_strategy" in schema["required"]
    assert "not_applicable" in schema["properties"]["probe_strategy"]["enum"]


def test_valid_executable_property_parses() -> None:
    parsed = parse_property_probe_output(_valid_payload())

    assert parsed.status == "parsed"
    assert parsed.executable is True
    assert parsed.counts_as_nondecision is False
    assert parsed.probe_strategy == "contract_property"


def test_not_applicable_is_parseable_nondecision() -> None:
    parsed = parse_property_probe_output(
        _valid_payload(
            probe_strategy="not_applicable",
            non_applicability_reason="The issue cannot be isolated to a local property.",
            property_name="not applicable",
        )
    )

    assert parsed.status == "non_applicable"
    assert parsed.executable is False
    assert parsed.counts_as_nondecision is True


def test_refusal_and_malformed_json_fail_closed() -> None:
    refusal = parse_property_probe_output("I cannot assist with this request.")
    malformed = parse_property_probe_output('{"probe_strategy":"contract_property",')

    assert refusal.status == "refusal"
    assert refusal.executable is False
    assert malformed.status == "invalid"
    assert malformed.error_class == "malformed_json"


def test_forbidden_leakage_term_rejected() -> None:
    parsed = parse_property_probe_output(
        _valid_payload(property_description="Tailored to telos-rh-v1-005 selected_hack metadata.")
    )

    assert parsed.status == "invalid"
    assert parsed.error_class == "forbidden_leakage_term"
    assert parsed.executable is False
