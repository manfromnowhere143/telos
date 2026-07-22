#!/usr/bin/env python3
"""Validate atom-complete public quantitative-claim coverage for Telos.

Every quantitative atom defaults to a claim.  A token is a typed nonclaim only
when an exact lexical rule covers that token itself; nearby words, substring
matches, and character-radius heuristics have no authority.  Current
machine-regenerated statements use a closed, curated projection catalogue that
resolves live surface atoms to JSON pointers in the six rebuilt claims.
"""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal, InvalidOperation
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
import subprocess
import sys
import tempfile
from typing import Any, Iterable

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts import build_current_claim_registry as builder
from telos.json_compare import compare_json


ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = Path("mission/claim_registry.json")
SEAL_REGISTRY_PATH = Path("mission/seal_registry.json")
REPORT_NAME = "claim_coverage_report.json"
SCHEMA_VERSION = "telos.claim_registry.v3"
REPORT_SCHEMA_VERSION = "telos.claim_coverage_report.v3"
BINDING_AUTHORIZATION_SCHEMA_VERSION = "telos.binding_authorization.v1"
OFFLINE_COMMAND_TIMEOUT_SECONDS = 120
SUBPROCESS_ENV_ALLOWLIST = {
    "LANG",
    "LC_ALL",
    "LC_CTYPE",
    "PATH",
    "PYTHONHASHSEED",
    "PYTHONIOENCODING",
    "PYTHONUTF8",
    "SYSTEMROOT",
    "TZ",
}
FIXED_PUBLIC_SURFACES = (
    "README.md",
    "paper/README.md",
    "paper/telos.tex",
    "mission/current.json",
)

ALLOWED_NONCLAIM_CATEGORIES = {
    "bibliographic_identifier",
    "claim_or_section_identifier",
    "date",
    "format_parameter",
    "hash",
    "iteration_identifier",
    "model_or_software_version",
    "path_or_command_identifier",
    "run_or_workflow_identifier",
    "schema_version",
}
ALLOWED_CLAIM_KINDS = {
    "external_citation",
    "engineering_verification",
    "historical_empirical",
    "internally_regenerated_empirical",
    "protocol_parameter",
    "worked_example",
}
ALLOWED_INTERNAL_STATUSES = {
    "exploratory",
    "inconclusive",
    "operational_reference_differential",
    "supported",
    "untested",
}
RETAINED_POLICY = {
    "external_citation": {
        "status": "externally_reported",
        "derivation_mode": "external_citation_surface",
        "missingness_modes": {"not_applicable"},
    },
    "engineering_verification": {
        "status": "historical",
        "derivation_mode": "retained_engineering_surface",
        "missingness_modes": {
            "not_stated_in_binding",
            "surface_explicit",
        },
    },
    "historical_empirical": {
        "statuses": {"corrected", "historical", "retracted"},
        "derivation_mode": "retained_historical_surface",
        "missingness_modes": {
            "not_stated_in_binding",
            "surface_explicit",
        },
    },
    "protocol_parameter": {
        "status": "protocol",
        "derivation_mode": "declared_protocol_surface",
        "missingness_modes": {"not_applicable"},
    },
    "worked_example": {
        "status": "historical",
        "derivation_mode": "retained_worked_example",
        "missingness_modes": {"not_applicable"},
    },
}

_SMALL = {
    "zero": 0,
    "one": 1,
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5,
    "six": 6,
    "seven": 7,
    "eight": 8,
    "nine": 9,
    "ten": 10,
    "eleven": 11,
    "twelve": 12,
    "thirteen": 13,
    "fourteen": 14,
    "fifteen": 15,
    "sixteen": 16,
    "seventeen": 17,
    "eighteen": 18,
    "nineteen": 19,
    "dozen": 12,
}
_CARDINAL_ALIASES = {
    "none": 0,
    "single": 1,
    "both": 2,
}
_MULTIPLICATIVE_CARDINALS = {
    "once": 1,
    "twice": 2,
}
_TENS = {
    "twenty": 20,
    "thirty": 30,
    "forty": 40,
    "fifty": 50,
    "sixty": 60,
    "seventy": 70,
    "eighty": 80,
    "ninety": 90,
}
_ORDINALS = {
    "first": 1,
    "second": 2,
    "third": 3,
    "fourth": 4,
    "fifth": 5,
    "sixth": 6,
    "seventh": 7,
    "eighth": 8,
    "ninth": 9,
    "tenth": 10,
}
_FRACTION_DENOMINATORS = {
    "half": 2,
    "halves": 2,
    "third": 3,
    "thirds": 3,
    "quarter": 4,
    "quarters": 4,
    "fourth": 4,
    "fourths": 4,
    "fifth": 5,
    "fifths": 5,
    "sixth": 6,
    "sixths": 6,
    "seventh": 7,
    "sevenths": 7,
    "eighth": 8,
    "eighths": 8,
    "ninth": 9,
    "ninths": 9,
    "tenth": 10,
    "tenths": 10,
}
_ORDINAL_WORDS = tuple(sorted(_ORDINALS, key=len, reverse=True))
_ORDINAL_ALTERNATION = "|".join(_ORDINAL_WORDS)
_ONES_ALTERNATION = "|".join(
    sorted(
        (
            "one",
            "two",
            "three",
            "four",
            "five",
            "six",
            "seven",
            "eight",
            "nine",
        ),
        key=len,
        reverse=True,
    )
)
_SMALL_ALTERNATION = "|".join(sorted(_SMALL, key=len, reverse=True))
_TENS_ALTERNATION = "|".join(sorted(_TENS, key=len, reverse=True))
_SUB_HUNDRED_PATTERN = (
    rf"(?:(?:{_TENS_ALTERNATION})(?:[ -]+(?:{_ONES_ALTERNATION}))?"
    rf"|(?:{_SMALL_ALTERNATION}))"
)
_SUB_THOUSAND_PATTERN = (
    rf"(?:(?:{_ONES_ALTERNATION})[ -]+hundred"
    rf"(?:[ -]+(?:and[ -]+)?{_SUB_HUNDRED_PATTERN})?"
    rf"|{_SUB_HUNDRED_PATTERN})"
)
_THOUSANDS_PATTERN = (
    rf"{_SUB_THOUSAND_PATTERN}[ -]+thousand"
    rf"(?:[ -]+(?:and[ -]+)?{_SUB_THOUSAND_PATTERN})?"
)
_MILLIONS_PATTERN = (
    rf"(?:{_THOUSANDS_PATTERN}|{_SUB_THOUSAND_PATTERN})[ -]+million"
    rf"(?:[ -]+(?:and[ -]+)?(?:"
    rf"{_THOUSANDS_PATTERN}|{_SUB_THOUSAND_PATTERN}))?"
)
_BILLIONS_PATTERN = (
    rf"(?:{_MILLIONS_PATTERN}|{_THOUSANDS_PATTERN}|{_SUB_THOUSAND_PATTERN})"
    rf"[ -]+billion(?:[ -]+(?:and[ -]+)?(?:"
    rf"{_MILLIONS_PATTERN}|{_THOUSANDS_PATTERN}|{_SUB_THOUSAND_PATTERN}))?"
)
_WRITTEN_PATTERN = (
    rf"(?<![A-Za-z0-9_])(?:"
    rf"{_BILLIONS_PATTERN}|{_MILLIONS_PATTERN}|{_THOUSANDS_PATTERN}|"
    rf"{_SUB_THOUSAND_PATTERN}|half)"
    rf"(?![A-Za-z0-9_])"
)
_FRACTION_NUMERATOR_PATTERN = (
    rf"(?:{_TENS_ALTERNATION})(?:[ -]+(?:{_ONES_ALTERNATION}))?"
    rf"|(?:{_SMALL_ALTERNATION})"
)
_FRACTION_DENOMINATOR_PATTERN = "|".join(
    sorted(_FRACTION_DENOMINATORS, key=len, reverse=True)
)
_WRITTEN_FRACTION_PATTERN = (
    rf"(?<![A-Za-z0-9_])(?:{_FRACTION_NUMERATOR_PATTERN})-"
    rf"(?:{_FRACTION_DENOMINATOR_PATTERN})(?![A-Za-z0-9_])"
)
_ORDINAL_PATTERN = (
    rf"(?<![A-Za-z0-9_])(?:{_ORDINAL_ALTERNATION})(?![A-Za-z0-9_])"
)
_CARDINAL_ALIAS_PATTERN = "|".join(
    sorted(_CARDINAL_ALIASES, key=len, reverse=True)
)
_MULTIPLICATIVE_CARDINAL_PATTERN = "|".join(
    sorted(_MULTIPLICATIVE_CARDINALS, key=len, reverse=True)
)
_REGISTERED_IDENTIFIER_PATTERN = r"(?:P\d+(?:\.\d+)*|T[1-4])"
_DIGIT_SCALAR_PATTERN = (
    r"(?:\d+(?:(?:,|\{,\}|_)\d{3})*(?:\.\d+)?|\.\d+)"
    r"(?:e[+-]?\d+)?"
)
TOKEN_RE = re.compile(
    rf"""
    (?<![A-Za-z0-9_])
    (?:
        [0-9a-f]{{64}}
      | [0-9a-f]{{40}}
      | \d{{4}}-\d{{2}}-\d{{2}}
      | iter\d+
      | v\d+(?:\.\d+)*
      | {_REGISTERED_IDENTIFIER_PATTERN}
      | \d+(?:\.\d+){{2,}}
      | {_WRITTEN_FRACTION_PATTERN}
      | [½]
      | \d+(?:st|nd|rd|th)
      | \$?(?:-|−)?\d+(?:[,_]\d{{3}})*[kKmMbB]
      | \$?(?:-|−)?{_DIGIT_SCALAR_PATTERN}
        (?:/{_DIGIT_SCALAR_PATTERN})?(?:\\?%)?
      | {_WRITTEN_PATTERN}
      | {_ORDINAL_PATTERN}
      | {_CARDINAL_ALIAS_PATTERN}
      | {_MULTIPLICATIVE_CARDINAL_PATTERN}
    )
    (?![A-Za-z0-9_])
    """,
    re.IGNORECASE | re.VERBOSE,
)
SHA_RE = re.compile(r"^[0-9a-f]{40}(?:[0-9a-f]{24})?$")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
ITER_RE = re.compile(r"^iter\d+$", re.IGNORECASE)
VERSION_ATOM_RE = re.compile(r"^v\d+(?:\.\d+)*$", re.IGNORECASE)
BARE_SEMVER_RE = re.compile(r"^\d+(?:\.\d+){2,}$")
MONTH_DATE_RE = re.compile(
    r"(?<![A-Za-z])(?:January|February|March|April|May|June|July|August|"
    r"September|October|November|December)\s+\d{1,2},\s+\d{4}(?![A-Za-z])"
)
MONTH_DAY_RE = re.compile(
    r"(?<![A-Za-z])(?:January|February|March|April|May|June|July|August|"
    r"September|October|November|December)\s+\d{1,2}(?![\d,])"
)
ISO_8601_UTC_RE = re.compile(
    r"(?<![A-Za-z0-9_])\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}"
    r"(?:\.\d+)?Z(?![A-Za-z0-9_])"
)
GIT_HASH_LEXEME_RE = re.compile(
    r"(?<![A-Za-z0-9_])`[0-9a-f]{40}(?:[0-9a-f]{24})?`"
    r"(?![A-Za-z0-9_])",
    re.IGNORECASE,
)
KEYED_GIT_HASH_RE = re.compile(
    r"(?<![A-Za-z0-9_])(?:predecessor_merge|implementation_head|commit|"
    r"sha(?:256)?)\s*:\s*[0-9a-f]{40}(?:[0-9a-f]{24})?"
    r"(?![A-Za-z0-9_])",
    re.IGNORECASE,
)
MARKDOWN_ORDERED_LIST_RE = re.compile(r"^\s*(?P<ordinal>\d+)\.\s")
MARKDOWN_NUMBERED_HEADING_RE = re.compile(
    r"^\s*#{1,6}\s+(?P<label>P\d+(?:\.\d+)*)\b"
)
PYTHON_NONE_CODE_LEXEME_RE = re.compile(
    r"(?:`[^`\r\n]*\bNone\b[^`\r\n]*`|"
    r"\\texttt\{(?:\\[{}]|[^{}\r\n])*\bNone\b"
    r"(?:\\[{}]|[^{}\r\n])*\})"
)
HANDOFF_PATH_RE = re.compile(
    r"^docs/HANDOFF-\d{4}-\d{2}-\d{2}-iter\d+\.md$"
)
AUDIT_PATH_RE = re.compile(r"^docs/TELOS-AUDIT-\d{4}-\d{2}-\d{2}\.md$")
CORRECTIVE_HISTORICAL_BINDING_IDS = frozenset(
    {
        "docs/TELOS-AUDIT-2026-07-22.md:2840c3cc068649f88be3:0:0",
        "docs/TELOS-AUDIT-2026-07-22.md:32711aaff2886f3cb92c:0:1",
        "docs/TELOS-AUDIT-2026-07-22.md:0c30a8216c2312a4e2c9:0:0",
        "docs/TELOS-AUDIT-2026-07-22.md:e0e544ced3374c2fe533:0:1",
    }
)
AUTHORIZED_UNBOUND_RETRACTED_HEADS: frozenset[str] = frozenset()

# This reviewed digest binds every current quantitative atom's normalized
# value (including unit flags), role, and exact claim/nonclaim resolution.
# Bootstrap validates it but never refreshes it.
AUTHORIZED_BINDING_INVENTORY_SHA256 = {
    "experiments/iter238_claim_seal_workflow_controls/HYPOTHESIS.md": (
        "7e753a14712eca0e0b32787e2b57a32714e895d7de1ed64076961ff951aba3ca"
    ),
    "experiments/iter239_repository_governance/HYPOTHESIS.md": (
        "9795a27b3af2a60e7f3caa14321bfda111eaabded9e0bc7c460b4bf739f9137c"
    ),
    "experiments/iter240_ground_truth_admission_design/HYPOTHESIS.md": (
        "fe367242303a5db0e01c132cd1ccbb529cf4a66634164f3214319642f7101c18"
    ),
    "experiments/iter241_iter240_repository_closure/HYPOTHESIS.md": (
        "50c6cd259ceb2ca1acf36ec8eb3819954b8eefc4ba0b628641e500f756e94965"
    ),
    "experiments/iter242_iter241_successor_closure/HYPOTHESIS.md": (
        "562d844f2e4b1e4880d876b3ee40df3c4c5a353473684a1ebc27ce426147a988"
    ),
    "experiments/iter243_iter242_remote_ci_recovery/HYPOTHESIS.md": (
        "eedc04493e512b22e5341c4b2036e4060bfb724f743e13c507d74b716c46feec"
    ),
    "experiments/iter245_offline_verified_python_bootstrap/HYPOTHESIS.md": (
        "c97fe9256390a50778f491b1c7a9821fc7591d6322a8e815b317331edf5e2b84"
    ),
}


class DuplicateKeyError(ValueError):
    """Raised when a JSON object repeats a key."""


def _object_no_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise DuplicateKeyError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _reject_json_constant(value: str) -> None:
    raise ValueError(f"non-finite JSON constant is forbidden: {value}")


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(
        path.read_text(encoding="utf-8"),
        object_pairs_hook=_object_no_duplicates,
        parse_constant=_reject_json_constant,
    )
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return value


def _has_control_characters(value: str) -> bool:
    return any(ord(character) < 32 or ord(character) == 127 for character in value)


def declared_surface_paths(root: Path = ROOT) -> tuple[str, ...]:
    """Resolve the dated handoff from the current pointer for this gate."""

    current = read_json(root / "mission/current.json")
    handoff = current.get("current_handoff")
    if not isinstance(handoff, str):
        raise ValueError("mission/current.json current_handoff must be a string")
    candidate = PurePosixPath(handoff)
    if (
        candidate.is_absolute()
        or _has_control_characters(handoff)
        or "\\" in handoff
        or len(candidate.parts) != 2
        or candidate.parts[0] != "docs"
        or HANDOFF_PATH_RE.fullmatch(handoff) is None
        or any(part in {"", ".", ".."} for part in candidate.parts)
        or candidate.as_posix() != handoff
    ):
        raise ValueError(f"current_handoff is not a canonical docs path: {handoff}")
    audit = current.get("current_audit")
    if not isinstance(audit, str):
        raise ValueError("mission/current.json current_audit must be a string")
    audit_candidate = PurePosixPath(audit)
    if (
        audit_candidate.is_absolute()
        or _has_control_characters(audit)
        or "\\" in audit
        or len(audit_candidate.parts) != 2
        or audit_candidate.parts[0] != "docs"
        or AUDIT_PATH_RE.fullmatch(audit) is None
        or any(part in {"", ".", ".."} for part in audit_candidate.parts)
        or audit_candidate.as_posix() != audit
    ):
        raise ValueError(f"current_audit is not a canonical audit path: {audit}")
    return (
        FIXED_PUBLIC_SURFACES[0],
        FIXED_PUBLIC_SURFACES[1],
        FIXED_PUBLIC_SURFACES[2],
        handoff,
        audit,
        FIXED_PUBLIC_SURFACES[3],
    )


# Compatibility snapshot for callers that need to copy the current surfaces.
# Validation itself resolves the pointer on every call.
DECLARED_SURFACES = declared_surface_paths(ROOT)


def credential_stripped_environment(
    environ: dict[str, str] | None = None,
    *,
    isolated_home: str = "/nonexistent/telos-credential-isolation",
) -> dict[str, str]:
    source = os.environ if environ is None else environ
    retained = {
        name: value
        for name, value in source.items()
        if name in SUBPROCESS_ENV_ALLOWLIST
    }
    retained.update(
        {
            "GIT_CONFIG_GLOBAL": os.devnull,
            "GIT_CONFIG_NOSYSTEM": "1",
            "HOME": isolated_home,
            "PYTHONNOUSERSITE": "1",
            "XDG_CONFIG_HOME": f"{isolated_home}/xdg",
        }
    )
    return retained


def _run_credential_stripped(
    argv: list[str],
    root: Path,
) -> subprocess.CompletedProcess[str]:
    execution_argv = (
        [sys.executable, *argv[1:]]
        if argv and argv[0] == "python3"
        else list(argv)
    )
    with tempfile.TemporaryDirectory(prefix="telos-claim-prerequisite-") as home:
        return subprocess.run(
            execution_argv,
            cwd=root,
            env=credential_stripped_environment(isolated_home=home),
            check=False,
            capture_output=True,
            text=True,
            timeout=OFFLINE_COMMAND_TIMEOUT_SECONDS,
        )


def validate_internal_prerequisites(
    root: Path,
    expected_internal: dict[str, dict[str, Any]],
) -> list[str]:
    """Execute both local commands with credentials and user config stripped."""

    failures: list[str] = []
    try:
        retained_dependencies = read_json(builder.DEPENDENCY_MANIFEST)
        expected_dependencies = builder.build_dependency_manifest()
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        return [f"internal dependency closure is unreadable: {exc}"]
    for mismatch in compare_json(
        retained_dependencies,
        expected_dependencies,
        path="internal_claim_dependencies",
    ):
        failures.append(f"internal dependency closure mismatch: {mismatch}")
    if failures:
        return failures

    try:
        predecessor = _run_credential_stripped(
            builder.PREDECESSOR_VALIDATOR_ARGV,
            root,
        )
    except subprocess.TimeoutExpired:
        return [
            "internal predecessor validation timed out after "
            f"{OFFLINE_COMMAND_TIMEOUT_SECONDS}s"
        ]
    except OSError as exc:
        return [f"cannot execute internal predecessor validator: {exc}"]
    if predecessor.returncode != 0:
        detail = (predecessor.stderr or predecessor.stdout).strip()
        return [
            "internal predecessor validation failed "
            f"(exit={predecessor.returncode}): {detail}"
        ]

    try:
        rebuilt = _run_credential_stripped(builder.DERIVATION_ARGV, root)
    except subprocess.TimeoutExpired:
        return [
            "internal claim derivation timed out after "
            f"{OFFLINE_COMMAND_TIMEOUT_SECONDS}s"
        ]
    except OSError as exc:
        return [f"cannot execute internal claim derivation: {exc}"]
    if rebuilt.returncode != 0:
        detail = (rebuilt.stderr or rebuilt.stdout).strip()
        return [
            "internal claim derivation failed "
            f"(exit={rebuilt.returncode}): {detail}"
        ]
    try:
        payload = json.loads(
            rebuilt.stdout,
            object_pairs_hook=_object_no_duplicates,
        )
    except (json.JSONDecodeError, DuplicateKeyError) as exc:
        return [f"internal claim derivation output is not canonical JSON: {exc}"]
    expected_payload = {"claims": expected_internal}
    for mismatch in compare_json(
        payload,
        expected_payload,
        path="internal_derivation_output",
    ):
        failures.append(f"internal derivation argv output mismatch: {mismatch}")
    return failures


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def normalize_space(text: str) -> str:
    return " ".join(text.split())


def _parse_written_integer(text: str) -> int:
    words = text.lower().replace("-", " ").split()
    if len(words) == 1 and words[0] in _ORDINALS:
        return _ORDINALS[words[0]]
    total = 0
    current = 0
    for word in words:
        if word == "and":
            continue
        if word in _SMALL:
            current += _SMALL[word]
        elif word in _TENS:
            current += _TENS[word]
        elif word == "hundred":
            current = max(current, 1) * 100
        elif word == "thousand":
            total += max(current, 1) * 1_000
            current = 0
        elif word == "million":
            total += max(current, 1) * 1_000_000
            current = 0
        elif word == "billion":
            total += max(current, 1) * 1_000_000_000
            current = 0
        else:
            raise ValueError(f"unsupported written integer: {text!r}")
    return total + current


def _decimal_text(value: str) -> str:
    decimal = Decimal(value)
    normalized = format(decimal, "f")
    if "." in normalized:
        normalized = normalized.rstrip("0").rstrip(".")
    return normalized or "0"


def _valid_iso_date(value: str) -> bool:
    try:
        datetime.strptime(value, "%Y-%m-%d")
    except ValueError:
        return False
    return True


def _valid_month_date(value: str) -> bool:
    try:
        datetime.strptime(value, "%B %d, %Y")
    except ValueError:
        return False
    return True


def _valid_month_day(value: str) -> bool:
    try:
        datetime.strptime(f"{value}, 2000", "%B %d, %Y")
    except ValueError:
        return False
    return True


def _valid_utc_timestamp(value: str) -> bool:
    try:
        datetime.fromisoformat(value.removesuffix("Z") + "+00:00")
    except ValueError:
        return False
    return True


def normalize_atom(
    text: str,
    *,
    math_delimited: bool = False,
) -> dict[str, Any]:
    lower = text.lower()
    if SHA_RE.fullmatch(lower):
        return {"numeric_type": "identifier", "value": lower}
    if DATE_RE.fullmatch(text):
        return {"numeric_type": "date", "value": text}
    if ITER_RE.fullmatch(lower):
        return {"numeric_type": "iteration", "value": lower}
    if VERSION_ATOM_RE.fullmatch(lower):
        return {"numeric_type": "version", "value": lower}
    if BARE_SEMVER_RE.fullmatch(lower):
        return {"numeric_type": "version", "value": lower}
    if re.fullmatch(_REGISTERED_IDENTIFIER_PATTERN, text, re.IGNORECASE):
        return {"numeric_type": "identifier", "value": text.upper()}
    if lower in _CARDINAL_ALIASES:
        return {
            "numeric_type": "integer",
            "value": _CARDINAL_ALIASES[lower],
        }
    if lower in _MULTIPLICATIVE_CARDINALS:
        return {
            "numeric_type": "multiplier",
            "value": _MULTIPLICATIVE_CARDINALS[lower],
        }
    if lower == "½" or lower == "half":
        return {
            "numeric_type": "ratio",
            "numerator": "1",
            "denominator": "2",
            "currency": False,
            "percent": False,
        }
    if "-" in lower:
        numerator_text, denominator_text = lower.rsplit("-", 1)
        denominator = _FRACTION_DENOMINATORS.get(denominator_text)
        if denominator is not None:
            return {
                "numeric_type": "ratio",
                "numerator": str(_parse_written_integer(numerator_text)),
                "denominator": str(denominator),
                "currency": False,
                "percent": False,
            }
    ordinal_match = re.fullmatch(r"(\d+)(?:st|nd|rd|th)", lower)
    if ordinal_match is not None:
        return {
            "numeric_type": "integer",
            "value": int(ordinal_match.group(1)),
        }
    magnitude_match = re.fullmatch(
        r"(\$?)((?:-|−)?\d+(?:[,_]\d{3})*)([kmb])",
        lower,
    )
    if magnitude_match is not None:
        magnitude = {"k": 1_000, "m": 1_000_000, "b": 1_000_000_000}[
            magnitude_match.group(3)
        ]
        base = int(
            magnitude_match.group(2)
            .replace("−", "-", 1)
            .replace(",", "")
            .replace("_", "")
        )
        return {
            "numeric_type": "integer",
            "value": base * magnitude,
            "currency": bool(magnitude_match.group(1)),
            "percent": False,
        }
    words = lower.replace("-", " ").split()
    if words and all(
        word == "and"
        or word in _SMALL
        or word in _TENS
        or word in _ORDINALS
        or word in {"hundred", "thousand", "million", "billion"}
        for word in words
    ):
        return {
            "numeric_type": "integer",
            "value": _parse_written_integer(lower),
        }

    currency = text.startswith("$") and not math_delimited
    percent = text.endswith("%")
    cleaned = text.removeprefix("$").replace("−", "-", 1)
    cleaned = (
        cleaned.removesuffix(r"\%")
        if cleaned.endswith(r"\%")
        else cleaned.removesuffix("%")
    )
    cleaned = cleaned.replace("{,}", "").replace(",", "").replace("_", "")
    if "/" in cleaned:
        numerator, denominator = cleaned.split("/", 1)
        return {
            "numeric_type": "ratio",
            "numerator": _decimal_text(numerator),
            "denominator": _decimal_text(denominator),
            "currency": currency,
            "percent": percent,
        }
    return {
        "numeric_type": "scalar",
        "value": _decimal_text(cleaned),
        "currency": currency,
        "percent": percent,
    }


@dataclass(frozen=True)
class QuantAtom:
    text: str
    start: int
    end: int
    normalized: dict[str, Any]


@dataclass(frozen=True)
class Segment:
    path: str
    locator: str
    text: str
    skeleton: str
    segment_ordinal: int
    anchor_sha256: str
    atoms: tuple[QuantAtom, ...]


@dataclass(frozen=True)
class AtomBinding:
    binding_id: str
    segment: Segment
    atom_ordinal: int
    atom: QuantAtom


class InvalidSurfaceQuantitativeSyntax(ValueError):
    """Raised when numeric-looking surface syntax cannot be interpreted safely."""


def _invalid_atom_syntax(binding: AtomBinding) -> str | None:
    atom = binding.atom
    text = binding.segment.text
    if DATE_RE.fullmatch(atom.text) and not _valid_iso_date(atom.text):
        return f"impossible ISO date {atom.text!r}"
    timestamp = _containing_match(ISO_8601_UTC_RE, text, atom)
    if timestamp is not None and not _valid_utc_timestamp(timestamp.group(0)):
        return f"impossible UTC timestamp {timestamp.group(0)!r}"
    month_date = _containing_match(MONTH_DATE_RE, text, atom)
    if month_date is not None and not _valid_month_date(month_date.group(0)):
        return f"impossible month-name date {month_date.group(0)!r}"
    month_day = _containing_match(MONTH_DAY_RE, text, atom)
    if month_day is not None and not _valid_month_day(month_day.group(0)):
        return f"impossible month-name day {month_day.group(0)!r}"
    if (
        atom.start > 0
        and text[atom.start - 1] == "–"
        and atom.normalized.get("numeric_type") != "identifier"
    ):
        return "ambiguous en-dash immediately before a numeric atom"
    return None


def quantitative_atoms(text: str) -> tuple[QuantAtom, ...]:
    result: list[QuantAtom] = []

    def append_matches(start: int, end: int) -> None:
        for match in TOKEN_RE.finditer(text, start, end):
            atom_text = match.group(0)
            if atom_text == "None" and any(
                code.start() <= match.start() and match.end() <= code.end()
                for code in PYTHON_NONE_CODE_LEXEME_RE.finditer(text)
            ):
                continue
            result.append(
                QuantAtom(
                    text=atom_text,
                    start=match.start(),
                    end=match.end(),
                    normalized=normalize_atom(
                        atom_text,
                        math_delimited=(
                            atom_text.startswith("$")
                            and match.end() < len(text)
                            and text[match.end()] == "$"
                        ),
                    ),
                )
            )

    cursor = 0
    for timestamp in ISO_8601_UTC_RE.finditer(text):
        append_matches(cursor, timestamp.start())
        for component in re.finditer(r"\d+", timestamp.group(0)):
            start = timestamp.start() + component.start()
            end = timestamp.start() + component.end()
            atom_text = component.group(0)
            result.append(
                QuantAtom(
                    text=atom_text,
                    start=start,
                    end=end,
                    normalized=normalize_atom(atom_text),
                )
            )
        cursor = timestamp.end()
    append_matches(cursor, len(text))
    return tuple(result)


def _skeleton(
    text: str,
    atoms: tuple[QuantAtom, ...] | None = None,
) -> str:
    resolved_atoms = quantitative_atoms(text) if atoms is None else atoms
    pieces: list[str] = []
    cursor = 0
    for atom in resolved_atoms:
        pieces.append(text[cursor : atom.start])
        pieces.append("<Q>")
        cursor = atom.end
    pieces.append(text[cursor:])
    return normalize_space("".join(pieces))


def _split_text_segments(path: str, text: str) -> list[tuple[str, str]]:
    pieces: list[tuple[str, str]] = []
    paragraph: list[str] = []
    bibliography_item: list[str] = []
    section = "document"
    in_fence = False
    in_bibliography = False

    def append_piece(value: str) -> None:
        normalized = normalize_space(value)
        sentences = re.split(r"(?<=[.!?])\s+(?=[A-Z`\[\\])", normalized)
        for sentence in sentences:
            if sentence:
                pieces.append((section, sentence))

    def flush() -> None:
        if paragraph:
            value = "\n".join(paragraph).strip()
            if value:
                append_piece(value)
            paragraph.clear()

    def flush_bibliography_item() -> None:
        if bibliography_item:
            value = normalize_space("\n".join(bibliography_item))
            match = re.match(r"\\bibitem\{([^}]*)\}", value)
            key = match.group(1) if match is not None else "unknown"
            pieces.append((f"bibliography:{key}", value))
            bibliography_item.clear()

    for raw_line in text.splitlines():
        stripped = raw_line.strip()
        if path.endswith(".tex") and stripped.startswith(
            r"\begin{thebibliography}"
        ):
            flush()
            pieces.append((section, stripped))
            in_bibliography = True
            continue
        if in_bibliography:
            if stripped.startswith(r"\end{thebibliography}"):
                flush_bibliography_item()
                in_bibliography = False
                continue
            if stripped.startswith(r"\bibitem{"):
                flush_bibliography_item()
                bibliography_item.append(stripped)
                continue
            if bibliography_item:
                if stripped:
                    bibliography_item.append(stripped)
                continue
            if stripped:
                append_piece(stripped)
            continue
        if path.endswith(".md") and stripped.startswith("#"):
            flush()
            section = normalize_space(stripped.lstrip("#").strip()) or "document"
            pieces.append((section, stripped))
            continue
        tex_heading = re.match(
            r"\\(?:section|subsection|paragraph)\{([^}]*)\}", stripped
        )
        if tex_heading:
            flush()
            section = normalize_space(tex_heading.group(1)) or "document"
            pieces.append((section, stripped))
            continue
        if stripped.startswith("```"):
            flush()
            pieces.append((section, stripped))
            in_fence = not in_fence
            continue
        if in_fence:
            if stripped:
                pieces.append((section, stripped))
            continue
        if not stripped:
            flush()
            continue
        standalone = (
            stripped.startswith("|")
            or stripped.startswith("\\bibitem")
            or stripped.startswith("\\item")
            or stripped.endswith(r"\\")
            or stripped.startswith("%")
        )
        list_start = re.match(r"(?:[-*+]|\d+\.)\s+", stripped) is not None
        if standalone:
            flush()
            append_piece(stripped)
            continue
        if list_start:
            flush()
            pieces.append((section, normalize_space(stripped)))
            continue
        paragraph.append(stripped)
    flush_bibliography_item()
    flush()
    return pieces


def _json_leaf_segments(value: Any, pointer: str = "") -> Iterable[tuple[str, str]]:
    if isinstance(value, dict):
        for key in sorted(value):
            escaped = key.replace("~", "~0").replace("/", "~1")
            yield from _json_leaf_segments(value[key], f"{pointer}/{escaped}")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            yield from _json_leaf_segments(item, f"{pointer}/{index}")
    else:
        locator = pointer or "/"
        yield locator, json.dumps(value, sort_keys=True)


def extract_segments(root: Path, path: str) -> list[Segment]:
    absolute = root / path
    if path.endswith(".json"):
        pieces = list(_json_leaf_segments(read_json(absolute)))
    else:
        pieces = _split_text_segments(path, absolute.read_text(encoding="utf-8"))

    duplicate_count: defaultdict[str, int] = defaultdict(int)
    result: list[Segment] = []
    for locator, text in pieces:
        atoms = quantitative_atoms(text)
        if not atoms:
            continue
        skeleton = _skeleton(text, atoms)
        seed = f"{path}\0{normalize_space(locator)}\0{skeleton}"
        anchor = hashlib.sha256(seed.encode("utf-8")).hexdigest()
        ordinal = duplicate_count[anchor]
        duplicate_count[anchor] += 1
        result.append(
            Segment(
                path=path,
                locator=normalize_space(locator),
                text=text,
                skeleton=skeleton,
                segment_ordinal=ordinal,
                anchor_sha256=anchor,
                atoms=atoms,
            )
        )
    return result


def extract_all_bindings(root: Path) -> list[AtomBinding]:
    result: list[AtomBinding] = []
    for path in declared_surface_paths(root):
        for segment in extract_segments(root, path):
            for atom_ordinal, atom in enumerate(segment.atoms):
                binding_id = (
                    f"{path}:{segment.anchor_sha256[:20]}:"
                    f"{segment.segment_ordinal}:{atom_ordinal}"
                )
                result.append(
                    AtomBinding(
                        binding_id=binding_id,
                        segment=segment,
                        atom_ordinal=atom_ordinal,
                        atom=atom,
                    )
                )
    return result


@dataclass(frozen=True)
class LexicalRule:
    name: str
    category: str
    pattern: re.Pattern[str]


def _compile(pattern: str) -> re.Pattern[str]:
    return re.compile(pattern, re.IGNORECASE)


LEXICAL_RULES = (
    LexicalRule(
        "registered_claim_or_section_identifier",
        "claim_or_section_identifier",
        _compile(
            rf"(?<![A-Za-z0-9_]){_REGISTERED_IDENTIFIER_PATTERN}"
            rf"(?![A-Za-z0-9_])"
        ),
    ),
    LexicalRule(
        "model_identifier",
        "model_or_software_version",
        _compile(
            r"(?<![A-Za-z0-9_])(?:"
            r"gpt-\d+(?:\.\d+)*(?:-[A-Za-z0-9]+)*|"
            r"claude-(?:[A-Za-z]+-)*\d+(?:\.\d+)*(?:-[A-Za-z0-9]+)*|"
            r"gemini-\d+(?:\.\d+)*(?:-[A-Za-z0-9]+)*"
            r")(?![A-Za-z0-9_])"
        ),
    ),
    LexicalRule(
        "named_software_version",
        "model_or_software_version",
        _compile(
            r"(?<![A-Za-z])(?:Python|Ubuntu|Tectonic|Docker|LaTeX)"
            r"\s+`?v?\d+(?:\.\d+)+`?"
            r"(?:(?:\s*(?:,|/)\s*|\s+and\s+)"
            r"`?v?\d+(?:\.\d+)+`?)*(?![A-Za-z0-9_])"
        ),
    ),
    LexicalRule(
        "generic_version_lexeme",
        "model_or_software_version",
        _compile(
            r"(?<![A-Za-z])version\s+`?v?\d+(?:\.\d+)+`?"
            r"(?![A-Za-z0-9_])"
        ),
    ),
    LexicalRule(
        "named_protocol_version",
        "model_or_software_version",
        _compile(
            r"(?<![A-Za-z])(?:TCP|receipt|PDF|schema)"
            r"(?:[- ]v?|[- ])\d+(?:\.\d+)*(?![A-Za-z0-9_])"
        ),
    ),
    LexicalRule(
        "schema_version_lexeme",
        "schema_version",
        _compile(
            r"(?<![A-Za-z0-9_])[A-Za-z][A-Za-z0-9_.-]*\.v\d+"
            r"(?:\.\d+)*(?![A-Za-z0-9_])"
        ),
    ),
    LexicalRule(
        "sha_algorithm_identifier",
        "hash",
        _compile(r"(?<![A-Za-z0-9_])SHA-(?:1|224|256|384|512)(?![A-Za-z0-9_])"),
    ),
    LexicalRule(
        "task_identifier",
        "path_or_command_identifier",
        _compile(
            r"(?<![A-Za-z0-9_])(?:[A-Za-z][A-Za-z0-9_.-]*__)?"
            r"(?:django|sympy|matplotlib|astropy|pytest|pylint|requests|"
            r"xarray|sphinx|scikit-learn)-\d+(?![A-Za-z0-9_])"
        ),
    ),
    LexicalRule(
        "pull_request_identifier",
        "run_or_workflow_identifier",
        _compile(r"(?<![A-Za-z])PR\s+`?#\d+`?(?![A-Za-z0-9_])"),
    ),
    LexicalRule(
        "run_identifier",
        "run_or_workflow_identifier",
        _compile(
            r"(?<![A-Za-z])(?:run|workflow|dispatch|job)(?:"
            r"\s+ID\s*[=:]?|\s*[=#>]|\s+`)"
            r"\s*\d{6,}`?(?![A-Za-z0-9_])"
        ),
    ),
    LexicalRule(
        "unchanged_latest_recorded_run_identifier",
        "run_or_workflow_identifier",
        _compile(
            r"(?<![A-Za-z])latest\s+recorded\s+run\s+unchanged\s+at"
            r"\s+`?\d{6,}`?(?![A-Za-z0-9_])"
        ),
    ),
    LexicalRule(
        "arxiv_identifier",
        "bibliographic_identifier",
        _compile(
            r"(?<![A-Za-z0-9_])arXiv:\d{4}\.\d{4,5}"
            r"(?:v\d+)?(?![A-Za-z0-9_])"
        ),
    ),
    LexicalRule(
        "doi_identifier",
        "bibliographic_identifier",
        _compile(r"(?<![A-Za-z0-9_])10\.\d{4,9}/[-._;()/:A-Za-z0-9]+"),
    ),
    LexicalRule(
        "url_lexeme",
        "path_or_command_identifier",
        _compile(r"https?://[^\s})\]]+"),
    ),
    LexicalRule(
        "backtick_source_locator",
        "path_or_command_identifier",
        _compile(
            r"`(?=[^`]*(?:\.md|\.tex|\.py):)[^`\r\n]+:"
            r"\d+(?:-\d+)?(?:,\d+(?:-\d+)?)*`"
        ),
    ),
    LexicalRule(
        "code_path_lexeme",
        "path_or_command_identifier",
        _compile(
            r"`(?=[^`\s]*[A-Za-z])(?:\.?/)?"
            r"(?:[A-Za-z0-9_.-]+/)+[A-Za-z0-9_.-]+`"
        ),
    ),
    LexicalRule(
        "markdown_target_path",
        "path_or_command_identifier",
        _compile(
            r"\((?=[^)\s]*[A-Za-z])(?:\.?\.?/)?"
            r"(?:[A-Za-z0-9_.-]+/)+[A-Za-z0-9_.-]+(?:#[A-Za-z0-9_.-]+)?\)"
        ),
    ),
    LexicalRule(
        "tex_document_format",
        "format_parameter",
        _compile(
            r"\\(?:documentclass\[[^]]+\]|setlength\{[^}]+\}\{[^}]+\}|"
            r"begin\{minipage\}\{[^}]+\}|"
            r"begin\{thebibliography\}\{\d+\})"
        ),
    ),
    LexicalRule(
        "tex_table_column_width",
        "format_parameter",
        _compile(r"p\{\d+(?:\.\d+)?\\linewidth\}"),
    ),
)


def _containing_match(
    pattern: re.Pattern[str],
    text: str,
    atom: QuantAtom,
) -> re.Match[str] | None:
    for match in pattern.finditer(text):
        if match.start() <= atom.start and atom.end <= match.end():
            return match
    return None


def derive_nonclaim(
    binding: AtomBinding,
) -> dict[str, Any] | None:
    """Derive a nonclaim only from the exact atom or an exact containing lexeme."""

    atom = binding.atom
    lower = atom.text.lower()
    if SHA_RE.fullmatch(lower):
        hash_match = _containing_match(
            GIT_HASH_LEXEME_RE,
            binding.segment.text,
            atom,
        ) or _containing_match(
            KEYED_GIT_HASH_RE,
            binding.segment.text,
            atom,
        )
        if hash_match is not None:
            return {
                "type": "typed_non_claim",
                "category": "hash",
                "rule": "contextual_git_hash",
                "lexeme": hash_match.group(0),
            }
    if DATE_RE.fullmatch(atom.text) and _valid_iso_date(atom.text):
        return {
            "type": "typed_non_claim",
            "category": "date",
            "rule": "iso_date",
            "lexeme": atom.text,
        }
    timestamp_match = _containing_match(
        ISO_8601_UTC_RE,
        binding.segment.text,
        atom,
    )
    if timestamp_match is not None and _valid_utc_timestamp(
        timestamp_match.group(0)
    ):
        return {
            "type": "typed_non_claim",
            "category": "date",
            "rule": "iso_8601_utc_timestamp",
            "lexeme": timestamp_match.group(0),
        }
    month_date_match = _containing_match(
        MONTH_DATE_RE,
        binding.segment.text,
        atom,
    )
    if month_date_match is not None and _valid_month_date(
        month_date_match.group(0)
    ):
        return {
            "type": "typed_non_claim",
            "category": "date",
            "rule": "month_name_date",
            "lexeme": month_date_match.group(0),
        }
    month_day_match = _containing_match(
        MONTH_DAY_RE,
        binding.segment.text,
        atom,
    )
    if month_day_match is not None and _valid_month_day(
        month_day_match.group(0)
    ):
        return {
            "type": "typed_non_claim",
            "category": "date",
            "rule": "month_name_day",
            "lexeme": month_day_match.group(0),
        }
    if ITER_RE.fullmatch(lower):
        return {
            "type": "typed_non_claim",
            "category": "iteration_identifier",
            "rule": "iteration_identifier",
            "lexeme": lower,
        }
    if binding.segment.path.endswith(".md"):
        marker = MARKDOWN_ORDERED_LIST_RE.match(binding.segment.text)
        if (
            marker is not None
            and marker.start("ordinal") <= atom.start
            and atom.end <= marker.end("ordinal")
        ):
            return {
                "type": "typed_non_claim",
                "category": "format_parameter",
                "rule": "markdown_ordered_list_marker",
                "lexeme": marker.group(0),
            }
        heading = MARKDOWN_NUMBERED_HEADING_RE.match(binding.segment.text)
        if (
            heading is not None
            and heading.start("label") <= atom.start
            and atom.end <= heading.end("label")
        ):
            return {
                "type": "typed_non_claim",
                "category": "format_parameter",
                "rule": "markdown_numbered_heading",
                "lexeme": heading.group(0),
            }
    if (
        lower in _ORDINALS
        and atom.start == 0
        and binding.segment.text[atom.end :].startswith(",")
    ):
        return {
            "type": "typed_non_claim",
            "category": "format_parameter",
            "rule": "discourse_enumeration_ordinal",
            "lexeme": binding.segment.text[: atom.end + 1],
        }
    if binding.segment.path.endswith(".json"):
        pointer = binding.segment.locator
        if pointer == "/schema_version":
            return {
                "type": "typed_non_claim",
                "category": "schema_version",
                "rule": "json_schema_version_pointer",
                "lexeme": normalize_space(binding.segment.text),
            }
    for rule in LEXICAL_RULES:
        match = _containing_match(rule.pattern, binding.segment.text, atom)
        if match is not None:
            return {
                "type": "typed_non_claim",
                "category": rule.category,
                "rule": rule.name,
                "lexeme": match.group(0),
            }
    if VERSION_ATOM_RE.fullmatch(lower) or BARE_SEMVER_RE.fullmatch(lower):
        return {
            "type": "typed_non_claim",
            "category": "model_or_software_version",
            "rule": "standalone_version_atom",
            "lexeme": lower,
        }
    return None


def atom_role(binding: AtomBinding) -> str:
    if binding.binding_id in CORRECTIVE_HISTORICAL_BINDING_IDS:
        return "corrective_historical_reference"
    prefix = binding.segment.text[: binding.atom.start]
    if re.search(r"(?:\\?\$)?u\s*=\s*$", prefix, re.IGNORECASE):
        return "explicit_missingness"
    return "quantitative_value"


def _equals(
    claim_id: str,
    pointer: str,
    *,
    currency: bool = False,
    percent: bool = False,
) -> dict[str, Any]:
    return {
        "claim_id": claim_id,
        "projection": {
            "operator": "equals",
            "pointer": pointer,
            "currency": currency,
            "percent": percent,
        },
    }


def _ratio(
    claim_id: str,
    numerator_pointer: str,
    denominator_pointer: str,
    *,
    currency: bool = False,
    percent: bool = False,
) -> dict[str, Any]:
    return {
        "claim_id": claim_id,
        "projection": {
            "operator": "ratio",
            "numerator_pointer": numerator_pointer,
            "denominator_pointer": denominator_pointer,
            "currency": currency,
            "percent": percent,
        },
    }


def _rounded(
    claim_id: str,
    pointer: str,
    decimal_places: int,
    *,
    currency: bool = False,
    percent: bool = False,
) -> dict[str, Any]:
    return {
        "claim_id": claim_id,
        "projection": {
            "operator": "rounded_decimal",
            "pointer": pointer,
            "decimal_places": decimal_places,
            "currency": currency,
            "percent": percent,
        },
    }


_FIXED = "telos.recurrence.fixed_cohort"
_ALL_RUNS = "telos.recurrence.all_runs_dependence"
_FRESH = "telos.cohort.fresh_concentration"
_SELECTOR = "telos.selector.fix_size_exploratory"
_TRANSFER = "telos.transfer.fix_size"
_BENCHMARK = "telos.benchmark.operational_labels"


def _run_ratio(claim_id: str, run: str) -> dict[str, Any]:
    return _ratio(
        claim_id,
        f"/value/fixed_cohort_runs/{run}/k",
        f"/value/fixed_cohort_runs/{run}/N",
    )


# Exact bindings in this catalogue are deliberately reviewed code, not inferred
# from values or nearby prose.  Each operator is closed and each pointer is
# resolved against build_current_claim_registry.build_internal_claims().
CURATED_INTERNAL_PROJECTIONS: dict[str, dict[str, Any]] = {
    # README current scientific boundary.
    "README.md:129752ef3555e8ca6149:0:0": _equals(
        _FIXED, "/value/solver_configuration_count"
    ),
    "README.md:129752ef3555e8ca6149:0:2": _equals(
        _FIXED, "/value/target_count"
    ),
    "README.md:10c6c0a7757425708847:0:1": _run_ratio(_FIXED, "iter223"),
    "README.md:10c6c0a7757425708847:0:2": _equals(
        _FIXED, "/value/fixed_cohort_runs/iter223/u"
    ),
    "README.md:818df490125ef2032b16:0:1": _run_ratio(_FIXED, "iter225"),
    "README.md:818df490125ef2032b16:0:2": _equals(
        _FIXED, "/value/fixed_cohort_runs/iter225/u"
    ),
    "README.md:818df490125ef2032b16:1:1": _run_ratio(_FIXED, "iter226"),
    "README.md:818df490125ef2032b16:1:2": _equals(
        _FIXED, "/value/fixed_cohort_runs/iter226/u"
    ),
    "README.md:47de6f43d047f420992d:0:1": _run_ratio(_FIXED, "iter227"),
    "README.md:47de6f43d047f420992d:0:2": _equals(
        _FIXED, "/value/fixed_cohort_runs/iter227/u"
    ),
    "README.md:7c0cba9798c8ece3e347:0:1": _run_ratio(_FIXED, "iter229"),
    "README.md:7c0cba9798c8ece3e347:0:2": _equals(
        _FIXED, "/value/fixed_cohort_runs/iter229/u"
    ),
    "README.md:4cedf4c6c353b8e68c35:0:0": _equals(
        _ALL_RUNS, "/value/measured_run_count"
    ),
    "README.md:4cedf4c6c353b8e68c35:0:2": _equals(
        _ALL_RUNS, "/value/patch_level_positives"
    ),
    "README.md:4cedf4c6c353b8e68c35:0:3": _equals(
        _ALL_RUNS, "/value/certifications"
    ),
    "README.md:4cedf4c6c353b8e68c35:0:4": _equals(
        _ALL_RUNS, "/value/unadjudicated"
    ),
    "README.md:d2fd20d2688193e59593:0:0": _equals(
        _ALL_RUNS, "/value/patch_level_positives"
    ),
    "README.md:d2fd20d2688193e59593:0:1": _equals(
        _ALL_RUNS, "/value/unique_task_identities"
    ),
    "README.md:45e2eacfcd14202f18ca:0:1": _equals(
        _FRESH, "/value/total/k"
    ),
    "README.md:45e2eacfcd14202f18ca:0:2": _equals(
        _FRESH, "/value/total/N"
    ),
    "README.md:45e2eacfcd14202f18ca:0:3": _equals(
        _FRESH, "/value/total/u"
    ),
    "README.md:7326decb57d01b678997:0:0": _ratio(
        _FRESH,
        "/value/least_favourable/numerator",
        "/value/least_favourable/denominator",
    ),
    "README.md:7326decb57d01b678997:0:1": _ratio(
        _FRESH,
        "/value/reused_reference/k",
        "/value/reused_reference/N",
    ),
    "README.md:a23554547907e65db8ff:0:1": _equals(
        _ALL_RUNS, "/value/all_runs/iter200/k"
    ),
    "README.md:a23554547907e65db8ff:0:2": _equals(
        _ALL_RUNS, "/value/all_runs/iter200/N"
    ),
    "README.md:a23554547907e65db8ff:0:3": _equals(
        _ALL_RUNS, "/value/all_runs/iter200/u"
    ),
    "README.md:a23554547907e65db8ff:0:4": _ratio(
        _ALL_RUNS,
        "/value/iter200_observed/numerator",
        "/value/iter200_observed/denominator",
    ),
    "README.md:a23554547907e65db8ff:0:5": _ratio(
        _ALL_RUNS,
        "/value/iter200_least_favourable/numerator",
        "/value/iter200_least_favourable/denominator",
    ),
    "README.md:a23554547907e65db8ff:0:6": _ratio(
        _ALL_RUNS,
        "/value/iter200_complete_case/numerator",
        "/value/iter200_complete_case/denominator",
    ),
    "README.md:c5865997d69b9f34dcf2:0:0": _equals(
        _SELECTOR, "/value/mannwhitney_u"
    ),
    "README.md:c5865997d69b9f34dcf2:0:2": _rounded(
        _SELECTOR,
        "/value/p_two_sided_asymptotic_tie_continuity",
        6,
    ),
    "README.md:b0287e46ff3e116de8cb:0:0": _equals(
        _TRANSFER, "/value/registered_held_out_rows"
    ),
    "README.md:b0287e46ff3e116de8cb:0:1": _equals(
        _TRANSFER, "/value/registered_outcome_labels"
    ),
    "README.md:b52f770769efd561c67e:0:0": _equals(
        _BENCHMARK, "/value/positive_count"
    ),
    "README.md:b52f770769efd561c67e:0:1": _equals(
        _BENCHMARK, "/value/control_count"
    ),
    "README.md:976a2b449d34b282d3fb:0:0": _equals(
        _BENCHMARK, "/value/controls/normalized_identical_to_accepted"
    ),
    "README.md:976a2b449d34b282d3fb:0:1": _equals(
        _BENCHMARK,
        "/value/controls/no_divergence_on_one_retained_witness",
    ),
    # Paper abstract and current-result sections.
    "paper/telos.tex:8357ed8a02fdc0aa8253:0:0": _equals(
        _ALL_RUNS, "/value/all_runs/iter200/k"
    ),
    "paper/telos.tex:8357ed8a02fdc0aa8253:0:1": _equals(
        _ALL_RUNS, "/value/all_runs/iter200/N"
    ),
    "paper/telos.tex:8357ed8a02fdc0aa8253:0:2": _equals(
        _ALL_RUNS, "/value/all_runs/iter200/u"
    ),
    "paper/telos.tex:90919155808e0533e49d:0:2": _equals(
        _FIXED, "/value/target_count"
    ),
    "paper/telos.tex:90919155808e0533e49d:0:3": _equals(
        _FIXED, "/value/solver_configuration_count"
    ),
    "paper/telos.tex:90919155808e0533e49d:0:4": _equals(
        _FIXED, "/value/provider_count"
    ),
    "paper/telos.tex:db05234e458d4feaabdc:0:0": _run_ratio(_FIXED, "iter223"),
    "paper/telos.tex:db05234e458d4feaabdc:0:1": _run_ratio(_FIXED, "iter225"),
    "paper/telos.tex:db05234e458d4feaabdc:0:2": _run_ratio(_FIXED, "iter226"),
    "paper/telos.tex:db05234e458d4feaabdc:0:3": _run_ratio(_FIXED, "iter227"),
    "paper/telos.tex:db05234e458d4feaabdc:0:4": _run_ratio(_FIXED, "iter229"),
    "paper/telos.tex:db05234e458d4feaabdc:0:5": _equals(
        _FIXED, "/value/fixed_cohort_runs/iter223/u"
    ),
    "paper/telos.tex:db05234e458d4feaabdc:0:6": _equals(
        _FIXED, "/value/fixed_cohort_runs/iter225/u"
    ),
    "paper/telos.tex:db05234e458d4feaabdc:0:7": _equals(
        _FIXED, "/value/fixed_cohort_runs/iter226/u"
    ),
    "paper/telos.tex:db05234e458d4feaabdc:0:8": _equals(
        _FIXED, "/value/fixed_cohort_runs/iter227/u"
    ),
    "paper/telos.tex:db05234e458d4feaabdc:0:9": _equals(
        _FIXED, "/value/fixed_cohort_runs/iter229/u"
    ),
    "paper/telos.tex:8a6ecc218e40b2615230:0:0": _equals(
        _FRESH, "/value/cohort_count"
    ),
    "paper/telos.tex:8a6ecc218e40b2615230:0:1": _equals(
        _FRESH, "/value/total/k"
    ),
    "paper/telos.tex:8a6ecc218e40b2615230:0:2": _equals(
        _FRESH, "/value/total/N"
    ),
    "paper/telos.tex:8a6ecc218e40b2615230:0:3": _equals(
        _FRESH, "/value/total/u"
    ),
    "paper/telos.tex:8a6ecc218e40b2615230:0:4": _ratio(
        _FRESH,
        "/value/least_favourable/numerator",
        "/value/least_favourable/denominator",
    ),
    "paper/telos.tex:8a6ecc218e40b2615230:0:5": _ratio(
        _FRESH,
        "/value/reused_reference/k",
        "/value/reused_reference/N",
    ),
    "paper/telos.tex:9c0fcf0c8247ecb2fb31:0:0": _equals(
        _BENCHMARK, "/value/control_count"
    ),
    "paper/telos.tex:9c0fcf0c8247ecb2fb31:0:1": _equals(
        _BENCHMARK, "/value/controls/normalized_identical_to_accepted"
    ),
    "paper/telos.tex:9c0fcf0c8247ecb2fb31:0:2": _equals(
        _BENCHMARK,
        "/value/controls/no_divergence_on_one_retained_witness",
    ),
    "paper/telos.tex:21256048d383a6cab0a1:0:1": _ratio(
        _ALL_RUNS,
        "/value/iter200_observed/numerator",
        "/value/iter200_observed/denominator",
    ),
    "paper/telos.tex:21256048d383a6cab0a1:0:2": _equals(
        _ALL_RUNS, "/value/all_runs/iter200/u"
    ),
    "paper/telos.tex:83a86e5598fa278c3409:0:0": _equals(
        _FRESH, "/value/total/k"
    ),
    "paper/telos.tex:83a86e5598fa278c3409:0:1": _equals(
        _FRESH, "/value/total/N"
    ),
    "paper/telos.tex:83a86e5598fa278c3409:0:2": _equals(
        _FRESH, "/value/total/u"
    ),
    "paper/telos.tex:83a86e5598fa278c3409:0:3": _equals(
        _FRESH, "/value/total/k"
    ),
    "paper/telos.tex:83a86e5598fa278c3409:0:4": _ratio(
        _FRESH,
        "/value/least_favourable/numerator",
        "/value/least_favourable/denominator",
    ),
    "paper/telos.tex:8e618a5edf69c5c46d1a:0:0": _ratio(
        _FRESH,
        "/value/reused_reference/k",
        "/value/reused_reference/N",
    ),
    "paper/telos.tex:8e618a5edf69c5c46d1a:0:1": _equals(
        _FRESH, "/value/reused_reference/u"
    ),
    "paper/telos.tex:8e618a5edf69c5c46d1a:0:2": _ratio(
        _FRESH,
        "/value/least_favourable/numerator",
        "/value/least_favourable/denominator",
    ),
    "paper/telos.tex:8e618a5edf69c5c46d1a:0:3": _ratio(
        _FRESH,
        "/value/reused_reference/k",
        "/value/reused_reference/N",
    ),
    "paper/telos.tex:ebf232506cfcacda3bc5:0:0": _equals(
        _ALL_RUNS, "/value/measured_run_count"
    ),
    "paper/telos.tex:ebf232506cfcacda3bc5:0:2": _equals(
        _ALL_RUNS, "/value/unadjudicated"
    ),
    "paper/telos.tex:ebf232506cfcacda3bc5:0:4": _equals(
        _ALL_RUNS, "/value/patch_level_positives"
    ),
    "paper/telos.tex:ebf232506cfcacda3bc5:0:5": _equals(
        _ALL_RUNS, "/value/certifications"
    ),
    "paper/telos.tex:eff55b3c361a6f2e4182:0:0": _equals(
        _ALL_RUNS, "/value/patch_level_positives"
    ),
    "paper/telos.tex:eff55b3c361a6f2e4182:0:1": _equals(
        _ALL_RUNS, "/value/unique_task_identities"
    ),
    "paper/telos.tex:d5aad3b6426f1432ab9b:0:6": _equals(
        _SELECTOR, "/value/mannwhitney_u"
    ),
    "paper/telos.tex:d5aad3b6426f1432ab9b:0:8": _rounded(
        _SELECTOR,
        "/value/p_two_sided_asymptotic_tie_continuity",
        6,
    ),
    "paper/telos.tex:0b9e82325fd302254658:0:0": _equals(
        _FIXED, "/value/fixed_cohort_patch_level_positives"
    ),
    "paper/telos.tex:eb978bd4ad24ce58ed89:0:1": _equals(
        _ALL_RUNS, "/value/measured_run_count"
    ),
    "paper/telos.tex:eb978bd4ad24ce58ed89:0:2": _equals(
        _ALL_RUNS, "/value/patch_level_positives"
    ),
    "paper/telos.tex:eb978bd4ad24ce58ed89:0:3": _equals(
        _ALL_RUNS, "/value/unique_task_identities"
    ),
    "paper/telos.tex:2a11c3ccb35bd2b948c2:0:0": _equals(
        _BENCHMARK, "/value/positive_count"
    ),
    "paper/telos.tex:2a11c3ccb35bd2b948c2:0:1": _equals(
        _BENCHMARK, "/value/control_count"
    ),
    # Fixed-cohort detail and limitations.
    "paper/telos.tex:a2546eee377c143a420e:0:0": _run_ratio(_FIXED, "iter223"),
    "paper/telos.tex:a2546eee377c143a420e:0:1": _equals(
        _FIXED, "/value/fixed_cohort_runs/iter223/u"
    ),
    "paper/telos.tex:a2546eee377c143a420e:0:2": _run_ratio(_FIXED, "iter225"),
    "paper/telos.tex:a2546eee377c143a420e:0:3": _equals(
        _FIXED, "/value/fixed_cohort_runs/iter225/u"
    ),
    "paper/telos.tex:a2546eee377c143a420e:0:4": _run_ratio(_FIXED, "iter226"),
    "paper/telos.tex:a2546eee377c143a420e:0:5": _equals(
        _FIXED, "/value/fixed_cohort_runs/iter226/u"
    ),
    "paper/telos.tex:a2546eee377c143a420e:0:6": _run_ratio(_FIXED, "iter227"),
    "paper/telos.tex:a2546eee377c143a420e:0:7": _equals(
        _FIXED, "/value/fixed_cohort_runs/iter227/u"
    ),
    "paper/telos.tex:a2546eee377c143a420e:0:8": _run_ratio(_FIXED, "iter229"),
    "paper/telos.tex:a2546eee377c143a420e:0:9": _equals(
        _FIXED, "/value/fixed_cohort_runs/iter229/u"
    ),
    "paper/telos.tex:a46e61b37219047f477c:0:0": _equals(
        _BENCHMARK, "/value/control_count"
    ),
    "paper/telos.tex:3262bb5de9774bf6f69f:0:0": _equals(
        _BENCHMARK, "/value/controls/normalized_identical_to_accepted"
    ),
    "paper/telos.tex:3262bb5de9774bf6f69f:0:1": _equals(
        _BENCHMARK,
        "/value/controls/no_divergence_on_one_retained_witness",
    ),
    "paper/telos.tex:89ae10d8a6e151aba886:0:0": _equals(
        _FRESH, "/value/cohort_count"
    ),
    "paper/telos.tex:89ae10d8a6e151aba886:0:1": _equals(
        _FRESH, "/value/total/k"
    ),
    "paper/telos.tex:89ae10d8a6e151aba886:0:2": _equals(
        _FRESH, "/value/total/N"
    ),
    "paper/telos.tex:89ae10d8a6e151aba886:0:3": _equals(
        _FRESH, "/value/total/u"
    ),
    "paper/telos.tex:eb1c3222622b7a0d154a:0:0": _ratio(
        _FRESH,
        "/value/least_favourable/numerator",
        "/value/least_favourable/denominator",
    ),
    "paper/telos.tex:eb1c3222622b7a0d154a:0:1": _ratio(
        _FRESH,
        "/value/reused_reference/k",
        "/value/reused_reference/N",
    ),
    "paper/telos.tex:49891e97df008b2fc962:0:0": _equals(
        _SELECTOR, "/value/mannwhitney_u"
    ),
    "paper/telos.tex:c2adfff9a9244cda22a2:0:0": _rounded(
        _SELECTOR,
        "/value/p_two_sided_asymptotic_tie_continuity",
        6,
    ),
    # Paper conclusion.
    "paper/telos.tex:3703829a2e87e531ae57:0:0": _equals(
        _FIXED, "/value/target_count"
    ),
    "paper/telos.tex:3703829a2e87e531ae57:0:1": _equals(
        _FIXED, "/value/solver_configuration_count"
    ),
    "paper/telos.tex:3703829a2e87e531ae57:0:2": _run_ratio(_FIXED, "iter223"),
    "paper/telos.tex:3703829a2e87e531ae57:0:3": _run_ratio(_FIXED, "iter225"),
    "paper/telos.tex:3703829a2e87e531ae57:0:4": _run_ratio(_FIXED, "iter226"),
    "paper/telos.tex:3703829a2e87e531ae57:0:5": _run_ratio(_FIXED, "iter227"),
    "paper/telos.tex:3703829a2e87e531ae57:0:6": _run_ratio(_FIXED, "iter229"),
    "paper/telos.tex:3703829a2e87e531ae57:0:7": _equals(
        _FIXED, "/value/fixed_cohort_runs/iter223/u"
    ),
    "paper/telos.tex:3703829a2e87e531ae57:0:8": _equals(
        _FIXED, "/value/fixed_cohort_runs/iter225/u"
    ),
    "paper/telos.tex:3703829a2e87e531ae57:0:9": _equals(
        _FIXED, "/value/fixed_cohort_runs/iter226/u"
    ),
    "paper/telos.tex:3703829a2e87e531ae57:0:10": _equals(
        _FIXED, "/value/fixed_cohort_runs/iter227/u"
    ),
    "paper/telos.tex:3703829a2e87e531ae57:0:11": _equals(
        _FIXED, "/value/fixed_cohort_runs/iter229/u"
    ),
    "paper/telos.tex:4ed2ee1f13b0d7d69f1f:0:0": _equals(
        _ALL_RUNS, "/value/measured_run_count"
    ),
    "paper/telos.tex:4ed2ee1f13b0d7d69f1f:0:1": _equals(
        _ALL_RUNS, "/value/patch_level_positives"
    ),
    "paper/telos.tex:4ed2ee1f13b0d7d69f1f:0:2": _equals(
        _ALL_RUNS, "/value/unique_task_identities"
    ),
    "paper/telos.tex:85661410e8c78d33c60c:0:0": _equals(
        _FRESH, "/value/total/k"
    ),
    "paper/telos.tex:85661410e8c78d33c60c:0:1": _equals(
        _FRESH, "/value/total/N"
    ),
    "paper/telos.tex:85661410e8c78d33c60c:0:2": _equals(
        _FRESH, "/value/total/u"
    ),
    "paper/telos.tex:74c34e8bb52f1e8585db:0:0": _equals(
        _BENCHMARK, "/value/control_count"
    ),
    "paper/telos.tex:74c34e8bb52f1e8585db:0:1": _equals(
        _BENCHMARK, "/value/controls/normalized_identical_to_accepted"
    ),
    "paper/telos.tex:74c34e8bb52f1e8585db:0:2": _equals(
        _BENCHMARK,
        "/value/controls/no_divergence_on_one_retained_witness",
    ),
    "paper/telos.tex:a4c627b2636fdb5cb3f4:0:0": _equals(
        _SELECTOR, "/value/mannwhitney_u"
    ),
    "paper/telos.tex:a4c627b2636fdb5cb3f4:0:2": _rounded(
        _SELECTOR,
        "/value/p_two_sided_asymptotic_tie_continuity",
        6,
    ),
    "paper/telos.tex:2d306965504e68afee7b:0:0": _equals(
        _FRESH, "/value/total/u"
    ),
    # Mutable current pointer repeats the fixed-cohort boundary.
    "README.md:1301869d331eff72af01:0:0": _equals(
        _FIXED, "/value/cohort_count"
    ),
    "README.md:1301869d331eff72af01:0:1": _equals(
        _FIXED, "/value/target_count"
    ),
    "README.md:69ed4757476a25f7660b:0:0": _equals(
        _FIXED, "/value/cohort_count"
    ),
    "README.md:129752ef3555e8ca6149:0:1": _equals(
        _FIXED, "/value/minimum_positive_per_run"
    ),
    "README.md:976a2b449d34b282d3fb:0:2": _equals(
        _BENCHMARK, "/value/retained_witness_count"
    ),
    "paper/README.md:174efee5e3df97deb95b:0:0": _equals(
        _FIXED, "/value/cohort_count"
    ),
    # Paper abstract, introduction, detailed result, and limitations repeats.
    "paper/telos.tex:90919155808e0533e49d:0:1": _equals(
        _FIXED, "/value/cohort_count"
    ),
    "paper/telos.tex:1bb61e125ab3401a67c6:0:0": _equals(
        _FIXED, "/value/solver_configuration_count"
    ),
    "paper/telos.tex:e04e54d2d2ed2e820cb4:0:0": _equals(
        _FIXED, "/value/provider_count"
    ),
    "paper/telos.tex:e04e54d2d2ed2e820cb4:0:1": _equals(
        _FIXED, "/value/minimum_positive_per_run"
    ),
    "paper/telos.tex:e04e54d2d2ed2e820cb4:0:2": _equals(
        _FIXED, "/value/target_count"
    ),
    "paper/telos.tex:e8f74cb5c93a7fc7b53a:0:0": _equals(
        _FIXED, "/value/target_count"
    ),
    "paper/telos.tex:18bf49eddab78c6bd12b:0:0": _equals(
        _FIXED, "/value/additional_solver_configuration_count"
    ),
    "paper/telos.tex:4ed4d00f83b6b9d8aec8:0:0": _equals(
        _FIXED, "/value/solver_configuration_count"
    ),
    "paper/telos.tex:d5aad3b6426f1432ab9b:0:0": _equals(
        _SELECTOR, "/value/solver_model_count"
    ),
    "paper/telos.tex:d5aad3b6426f1432ab9b:0:1": _equals(
        _SELECTOR, "/value/labelled_target_count"
    ),
    "paper/telos.tex:d5aad3b6426f1432ab9b:0:2": _equals(
        _FIXED, "/value/target_count"
    ),
    "paper/telos.tex:d5aad3b6426f1432ab9b:0:3": _equals(
        _SELECTOR, "/value/unlabelled_target_count"
    ),
    "paper/telos.tex:d5aad3b6426f1432ab9b:0:4": _equals(
        _SELECTOR, "/value/labelled_median_added_source_lines"
    ),
    "paper/telos.tex:d5aad3b6426f1432ab9b:0:5": _equals(
        _SELECTOR, "/value/unlabelled_median_added_source_lines"
    ),
    "paper/telos.tex:d5aad3b6426f1432ab9b:0:9": _equals(
        _SELECTOR, "/value/comparison_group_count"
    ),
    "paper/telos.tex:f6dfc747b6351097712f:0:0": _equals(
        _BENCHMARK, "/value/controls/normalized_identical_to_accepted"
    ),
    "paper/telos.tex:f6dfc747b6351097712f:0:1": _equals(
        _BENCHMARK,
        "/value/controls/no_divergence_on_one_retained_witness",
    ),
    "paper/telos.tex:f6dfc747b6351097712f:0:2": _equals(
        _BENCHMARK, "/value/retained_witness_count"
    ),
    "paper/telos.tex:74c34e8bb52f1e8585db:0:3": _equals(
        _BENCHMARK, "/value/retained_witness_count"
    ),
    "paper/telos.tex:9c0fcf0c8247ecb2fb31:0:3": _equals(
        _BENCHMARK, "/value/retained_witness_count"
    ),
    "paper/telos.tex:012c63047486be8197ce:0:0": _equals(
        _FRESH, "/value/cohort_count"
    ),
    "paper/telos.tex:ccaa745ebe1f51050a4b:0:0": _equals(
        _FIXED, "/value/target_count"
    ),
    "paper/telos.tex:fd8d5f8ece5a29a63802:0:0": _equals(
        _FRESH, "/value/cohort_count"
    ),
    "paper/telos.tex:fd8d5f8ece5a29a63802:0:3": _equals(
        _FRESH, "/value/cohorts/iter228/N"
    ),
    "paper/telos.tex:fd8d5f8ece5a29a63802:0:4": _equals(
        _FRESH, "/value/cohorts/iter228/u"
    ),
    "paper/telos.tex:fd8d5f8ece5a29a63802:0:5": _equals(
        _FRESH, "/value/cohorts/iter228/k"
    ),
    "paper/telos.tex:fd8d5f8ece5a29a63802:0:6": _equals(
        _FRESH, "/value/cohorts/iter228/N"
    ),
    "paper/telos.tex:fd8d5f8ece5a29a63802:0:7": _equals(
        _FRESH, "/value/cohorts/iter228/u"
    ),
    "paper/telos.tex:353b6b8d323bdaa904ed:0:0": _equals(
        _FIXED, "/value/minimum_positive_per_run"
    ),
    "paper/telos.tex:4cef7d5d6c27ee9148e5:0:0": _equals(
        _FIXED, "/value/cohort_count"
    ),
    "paper/telos.tex:6c4bbd500ac1af092618:0:0": _equals(
        _FIXED, "/value/cohort_count"
    ),
    # Current audit repeats of the same six regenerated claims.
    "docs/TELOS-AUDIT-2026-07-22.md:0c30a8216c2312a4e2c9:0:1": _rounded(
        _SELECTOR,
        "/value/p_two_sided_asymptotic_tie_continuity",
        4,
    ),
    "docs/TELOS-AUDIT-2026-07-22.md:e3732a2a607066ad10ed:0:0": _equals(
        _FIXED, "/value/solver_configuration_count"
    ),
    "docs/TELOS-AUDIT-2026-07-22.md:aa04612dcfd47957765e:0:0": _equals(
        _FIXED, "/value/provider_count"
    ),
    "docs/TELOS-AUDIT-2026-07-22.md:9bcdc435abf35b969a70:0:1": _equals(
        _FIXED, "/value/target_count"
    ),
    "docs/TELOS-AUDIT-2026-07-22.md:bec9bdd2cf530d19cb5d:0:3": _equals(
        _ALL_RUNS, "/value/patch_level_positives"
    ),
    "docs/TELOS-AUDIT-2026-07-22.md:bec9bdd2cf530d19cb5d:0:5": _equals(
        _ALL_RUNS, "/value/unadjudicated"
    ),
    "docs/TELOS-AUDIT-2026-07-22.md:8bdf733c7dbc1b47fc09:0:1": _equals(
        _FIXED, "/value/solver_configuration_count"
    ),
    "docs/TELOS-AUDIT-2026-07-22.md:aa04612dcfd47957765e:0:1": _equals(
        _FIXED, "/value/target_count"
    ),
    "docs/TELOS-AUDIT-2026-07-22.md:f89079f9897bcc7613e9:0:1": _equals(
        _ALL_RUNS, "/value/patch_level_positives"
    ),
    "docs/TELOS-AUDIT-2026-07-22.md:f89079f9897bcc7613e9:0:2": _equals(
        _ALL_RUNS, "/value/certifications"
    ),
    "docs/TELOS-AUDIT-2026-07-22.md:b084e848350a14302d29:0:4": _equals(
        _ALL_RUNS, "/value/unique_task_identities"
    ),
    "docs/TELOS-AUDIT-2026-07-22.md:4a7b6ad21d9ab629d349:0:2": _ratio(
        _FRESH,
        "/value/cohorts/iter224/k",
        "/value/cohorts/iter224/N",
    ),
    "docs/TELOS-AUDIT-2026-07-22.md:4a7b6ad21d9ab629d349:0:3": _ratio(
        _FRESH,
        "/value/cohorts/iter228/k",
        "/value/cohorts/iter228/N",
    ),
    "docs/TELOS-AUDIT-2026-07-22.md:4a7b6ad21d9ab629d349:0:4": _equals(
        _FRESH, "/value/cohorts/iter224/u"
    ),
    "docs/TELOS-AUDIT-2026-07-22.md:4a7b6ad21d9ab629d349:0:5": _equals(
        _FRESH, "/value/cohorts/iter228/u"
    ),
    "docs/TELOS-AUDIT-2026-07-22.md:588bdf7441a09b1be1a4:0:0": _equals(
        _FRESH, "/value/total/N"
    ),
    "docs/TELOS-AUDIT-2026-07-22.md:5afab7e8dd4d34b89a97:0:0": _equals(
        _FRESH, "/value/total/k"
    ),
    "docs/TELOS-AUDIT-2026-07-22.md:5afab7e8dd4d34b89a97:0:1": _equals(
        _FRESH, "/value/total/N"
    ),
    "docs/TELOS-AUDIT-2026-07-22.md:de57a92c3ac891f2d9b7:0:0": _equals(
        _FRESH, "/value/total/u"
    ),
    "docs/TELOS-AUDIT-2026-07-22.md:de57a92c3ac891f2d9b7:0:1": _equals(
        _FRESH, "/value/total/N"
    ),
    "docs/TELOS-AUDIT-2026-07-22.md:9bcdc435abf35b969a70:0:0": _equals(
        _FIXED, "/value/solver_configuration_count"
    ),
    "docs/TELOS-AUDIT-2026-07-22.md:6db4dfd003b6b9647bec:0:0": _equals(
        _BENCHMARK, "/value/positive_count"
    ),
    "docs/TELOS-AUDIT-2026-07-22.md:6db4dfd003b6b9647bec:0:1": _equals(
        _BENCHMARK, "/value/control_count"
    ),
    "docs/TELOS-AUDIT-2026-07-22.md:6b5d4be176f500421db7:0:0": _equals(
        _BENCHMARK, "/value/controls/normalized_identical_to_accepted"
    ),
    "docs/TELOS-AUDIT-2026-07-22.md:6469fccfd72be86b1f56:0:0": _equals(
        _FRESH, "/value/cohort_count"
    ),
    "docs/TELOS-AUDIT-2026-07-22.md:6469fccfd72be86b1f56:0:1": _equals(
        _FRESH, "/value/total/k"
    ),
    "docs/TELOS-AUDIT-2026-07-22.md:706ed46748be79374292:0:1": _equals(
        _FIXED, "/value/cohort_count"
    ),
    "docs/TELOS-AUDIT-2026-07-22.md:f89079f9897bcc7613e9:0:3": _equals(
        _ALL_RUNS, "/value/unique_task_identities"
    ),
    "docs/HANDOFF-2026-07-22-iter245.md:a6c3e8bb7fa52ff11f9e:0:0": _equals(
        _FIXED, "/value/cohort_count"
    ),
    "docs/HANDOFF-2026-07-22-iter245.md:a6c3e8bb7fa52ff11f9e:0:1": _equals(
        _FIXED, "/value/target_count"
    ),
    "mission/current.json:4e07630718bf116b4318:0:0": _equals(
        _FIXED, "/value/cohort_count"
    ),
    "mission/current.json:4e07630718bf116b4318:0:1": _equals(
        _FIXED, "/value/target_count"
    ),
}

PROJECTION_OPERATORS = {"equals", "ratio", "rounded_decimal"}

CURATED_EXTERNAL_BODY_BINDINGS = frozenset(
    {
        "paper/telos.tex:0639ae771bab9cfb737c:0:0",
        "paper/telos.tex:5a575eafa3a391c466d7:0:0",
        "paper/telos.tex:5e288e9fb53b1cb68fe5:0:0",
        "paper/telos.tex:7f3f0a2b6a31e3a92bb2:0:0",
        "paper/telos.tex:7f3f0a2b6a31e3a92bb2:0:1",
        "paper/telos.tex:b31a15caa9c806030910:0:0",
        "paper/telos.tex:b31a15caa9c806030910:0:1",
        "paper/telos.tex:f3dd7988619340121f3f:0:0",
        "paper/telos.tex:f3dd7988619340121f3f:0:1",
        "docs/TELOS-AUDIT-2026-07-22.md:b084e848350a14302d29:0:2",
        "docs/TELOS-AUDIT-2026-07-22.md:b084e848350a14302d29:0:3",
    }
)

CURATED_ENGINEERING_BINDINGS = frozenset(
    {
        "docs/HANDOFF-2026-07-22-iter245.md:839ac64d138e10b62629:0:0",
        "docs/HANDOFF-2026-07-22-iter245.md:839ac64d138e10b62629:0:2",
        "docs/HANDOFF-2026-07-22-iter245.md:76355f73ab77d0d90d1c:0:0",
        "docs/HANDOFF-2026-07-22-iter245.md:76355f73ab77d0d90d1c:0:1",
        "docs/HANDOFF-2026-07-22-iter245.md:32a8fbf62c724673937f:0:0",
        "paper/README.md:652cbf7d9b2f6f4990a2:0:2",
    }
)

CURATED_PROTOCOL_BINDINGS = frozenset(
    {
        "docs/HANDOFF-2026-07-22-iter245.md:f1416642c5c4c245a35a:0:1",
        "docs/HANDOFF-2026-07-22-iter245.md:3c51fff001b11529c74c:0:0",
        "docs/HANDOFF-2026-07-22-iter245.md:3c51fff001b11529c74c:0:1",
        "docs/HANDOFF-2026-07-22-iter245.md:01c78fb34309581b6161:0:0",
        "docs/HANDOFF-2026-07-22-iter245.md:01c78fb34309581b6161:0:1",
        "docs/HANDOFF-2026-07-22-iter245.md:8ae5f69e73530a59bac0:0:1",
        "paper/README.md:54482c748641120713a1:0:0",
        "paper/telos.tex:18bf49eddab78c6bd12b:0:1",
        # Statistical procedure parameters are claims, never typography.
        "README.md:c5865997d69b9f34dcf2:0:1",
        "paper/telos.tex:d5aad3b6426f1432ab9b:0:7",
        "paper/telos.tex:49891e97df008b2fc962:0:1",
        "paper/telos.tex:a4c627b2636fdb5cb3f4:0:1",
        "docs/TELOS-AUDIT-2026-07-22.md:5afab7e8dd4d34b89a97:0:2",
        "docs/TELOS-AUDIT-2026-07-22.md:d59c0f3858f1fb7bdf87:0:2",
        "docs/TELOS-AUDIT-2026-07-22.md:8e650e724d8610b66a80:0:5",
        # Mixed empirical/method paragraphs need atom-local reviewed typing.
        "paper/telos.tex:40275b3744d336814554:0:2",
        "paper/telos.tex:40275b3744d336814554:0:3",
        "paper/telos.tex:dc4422a91ca3a6e6753b:0:0",
        "paper/telos.tex:871460b55a2c239e32fb:0:0",
        "paper/telos.tex:7f475678e38ce530ed7c:0:3",
        "paper/telos.tex:47cb329178248bc34729:0:0",
        "paper/telos.tex:47cb329178248bc34729:0:1",
        "paper/telos.tex:607b985b4af6432e5555:0:0",
        "paper/telos.tex:607b985b4af6432e5555:0:1",
        "paper/telos.tex:d009dbcbfda661fb9b0c:0:0",
        "paper/telos.tex:d009dbcbfda661fb9b0c:0:1",
        "paper/telos.tex:d009dbcbfda661fb9b0c:0:2",
        "paper/telos.tex:08ac8463cfa8a5a2b8aa:0:0",
        "paper/telos.tex:08ac8463cfa8a5a2b8aa:0:1",
        "paper/telos.tex:16897562359ac969b322:0:1",
        "paper/telos.tex:16897562359ac969b322:0:2",
        "paper/telos.tex:abdaaa0a85d44c907ee9:0:0",
        "paper/telos.tex:abdaaa0a85d44c907ee9:0:1",
        "paper/telos.tex:74786cc52f1cc045eced:0:2",
        "paper/telos.tex:74786cc52f1cc045eced:0:3",
        "paper/telos.tex:74786cc52f1cc045eced:0:0",
        "paper/telos.tex:74786cc52f1cc045eced:0:1",
        "paper/telos.tex:63d4d0d67a85b5c3dc59:0:0",
        "paper/telos.tex:a8a0df40a79a93387ce9:0:0",
        "paper/telos.tex:a8a0df40a79a93387ce9:0:1",
        "paper/telos.tex:d1ce883b6545880c970f:0:0",
        "paper/telos.tex:d1ce883b6545880c970f:0:1",
        "paper/telos.tex:d1ce883b6545880c970f:0:2",
        "paper/telos.tex:eec04e995296c9116d44:0:4",
        "paper/telos.tex:ee61d3f4b6ec580db0aa:0:0",
    }
)

UNRESOLVED_RETAINED_SEMANTIC_STATE = "unresolved_not_reconstructed"
UNRESOLVED_RETAINED_UNIT = (
    "unresolved: the domain unit was not reconstructed from this retained "
    "public surface segment"
)
UNRESOLVED_RETAINED_COHORT = (
    "unresolved: the empirical cohort was not reconstructed from this "
    "retained public surface segment"
)
UNRESOLVED_RETAINED_INDEPENDENCE = (
    "unresolved: the sampling and dependence boundary was not reconstructed "
    "from this retained public surface segment"
)
UNRESOLVED_RETAINED_EXCLUSIONS = [
    "scientific reuse until unit, cohort, and independence metadata are adjudicated",
    "independent semantic ground truth",
    "unscoped population inference",
]

_SELECTOR_PREDECESSOR = builder.SELECTOR_PREDECESSOR_CLAIM_ID
CURATED_LINEAGE_PROJECTIONS = {
    "docs/TELOS-AUDIT-2026-07-22.md:2840c3cc068649f88be3:0:0": _equals(
        _SELECTOR_PREDECESSOR, "/value/reported_p"
    ),
    "docs/TELOS-AUDIT-2026-07-22.md:32711aaff2886f3cb92c:0:1": _equals(
        _SELECTOR_PREDECESSOR, "/value/reported_p"
    ),
    "docs/TELOS-AUDIT-2026-07-22.md:0c30a8216c2312a4e2c9:0:0": _equals(
        _SELECTOR_PREDECESSOR, "/value/reported_p"
    ),
    "docs/TELOS-AUDIT-2026-07-22.md:e0e544ced3374c2fe533:0:1": _equals(
        _SELECTOR_PREDECESSOR, "/value/reported_p"
    ),
}


def _retained_kind(binding: AtomBinding) -> str:
    segment = binding.segment
    if (
        segment.text.lstrip().startswith("\\bibitem{")
        or segment.locator.startswith("bibliography:")
    ):
        return "external_citation"
    if binding.binding_id in CURATED_EXTERNAL_BODY_BINDINGS:
        return "external_citation"
    if binding.binding_id in CURATED_ENGINEERING_BINDINGS:
        return "engineering_verification"
    if binding.binding_id in CURATED_PROTOCOL_BINDINGS:
        return "protocol_parameter"
    if segment.path == "paper/telos.tex":
        if segment.locator == "A worked example.":
            return "worked_example"
        if segment.locator == "Reproducibility.":
            return "engineering_verification"
        return "historical_empirical"
    if segment.path == "README.md":
        if segment.locator in {
            "Current engineering gate",
            "Reproduce the current state",
        }:
            return "engineering_verification"
        if segment.locator in {
            "Next mission gates",
            "Repository contract",
            "Writing standard",
        }:
            return "protocol_parameter"
        return "historical_empirical"
    if segment.path == "paper/README.md":
        if segment.locator in {"Build", "Reproducible build"}:
            return "protocol_parameter"
        return "historical_empirical"
    if HANDOFF_PATH_RE.fullmatch(segment.path):
        if segment.locator == "Earned predecessor state":
            return "engineering_verification"
        return "protocol_parameter"
    if AUDIT_PATH_RE.fullmatch(segment.path):
        if segment.locator in {
            "Iter237 — truth maintenance",
            "Iter238 — claim, seal, and workflow controls",
            "GROUND-TRUTH-1 — independent semantic adjudication",
            "ASSURANCE-DELTA-1 — prospective frontier trial",
            "Planning budget tiers",
            "Decisive mission sequence",
            "Final takeover decision",
        }:
            return "protocol_parameter"
        if segment.locator in {
            "Mechanical checks versus scientific acceptance",
            "Iter237 local remediation result",
        }:
            return "engineering_verification"
        return "historical_empirical"
    return "protocol_parameter"


def _surface_source(
    root: Path,
    path: str,
    *,
    binding: AtomBinding | None = None,
) -> dict[str, Any]:
    if binding is None:
        return {
            "path": path,
            "sha256": sha256(root / path),
            "classification": "mutable",
            "seal_ids": [],
        }
    if binding.segment.path != path:
        raise ValueError("segment-scoped source path/binding mismatch")
    return {
        "path": path,
        "sha256": hashlib.sha256(
            binding.segment.text.encode("utf-8")
        ).hexdigest(),
        "classification": "mutable",
        "seal_ids": [],
        "digest_scope": "normalized_surface_segment_utf8",
        "binding_id": binding.binding_id,
    }


def build_curated_lineage_claims(
    root: Path = ROOT,
) -> dict[str, dict[str, Any]]:
    audit_path = declared_surface_paths(root)[-2]
    live_by_id = {
        binding.binding_id: binding for binding in extract_all_bindings(root)
    }
    sources = [
        *[
            _surface_source(
                root,
                audit_path,
                binding=live_by_id[binding_id],
            )
            for binding_id in sorted(CORRECTIVE_HISTORICAL_BINDING_IDS)
        ],
        builder.source(
            "experiments/iter236_transfer_analysis_reconstruction/RESULT.md"
        ),
    ]
    digest_payload = json.dumps(
        {
            "claim_id": _SELECTOR_PREDECESSOR,
            "value": {"reported_p": 0.008},
            "sources": [
                {"path": source["path"], "sha256": source["sha256"]}
                for source in sources
            ],
        },
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return {
        _SELECTOR_PREDECESSOR: {
            "claim_id": _SELECTOR_PREDECESSOR,
            "revision": 1,
            "status": "corrected",
            "kind": "historical_empirical",
            "unit": "reported post-hoc two-sided p-value",
            "cohort": "reused fixed cohort as historically reported",
            "independence_boundary": (
                "The published 0.008 value did not reproduce under the "
                "committed standard analysis variants."
            ),
            "value": {"reported_p": 0.008},
            "missingness": {
                "mode": "not_stated_in_binding",
                "reason": (
                    "The corrected historical statistic has no row-level "
                    "missingness field in these public bindings."
                ),
            },
            "excluded_inferences": [
                "reproducible current p-value",
                "validated selector",
                "causal effect",
            ],
            "derivation": {
                "mode": "retained_historical_surface",
                "argv": [],
                "output_pointer": "/value/reported_p",
                "input_digest_sha256": hashlib.sha256(
                    digest_payload
                ).hexdigest(),
            },
            "sources": sources,
            "surface_binding_ids": [],
            "supersedes": [],
            "superseded_by": _SELECTOR,
        }
    }


def _retained_missingness(
    binding: AtomBinding,
    kind: str,
) -> dict[str, Any]:
    role = atom_role(binding)
    if kind in {"historical_empirical", "engineering_verification"}:
        if role == "explicit_missingness":
            return {
                "mode": "surface_explicit",
                "binding_id": binding.binding_id,
                "normalized_value": binding.atom.normalized,
                "reason": "The atom is the value in exact token-local u= syntax.",
            }
        return {
            "mode": "not_stated_in_binding",
            "binding_id": binding.binding_id,
            "reason": (
                "This granular quantitative atom does not itself state a "
                "missingness field."
            ),
        }
    return {
        "mode": "not_applicable",
        "binding_id": binding.binding_id,
        "reason": (
            "Missingness is not an empirical endpoint for this retained claim kind."
        ),
    }


def _initial_retained_claim_ids(
    bindings: list[AtomBinding],
) -> dict[str, str]:
    """Assign opaque reviewed IDs once, before the first registry freeze.

    These IDs are deliberately not hashes of prose, anchors, or binding IDs.
    After the initial registry is written, the registry owns the mapping and
    this allocator is never consulted by ordinary validation or migration.
    """

    prefixes = {
        "external_citation": "external",
        "engineering_verification": "engineering",
        "historical_empirical": "historical",
        "protocol_parameter": "protocol",
        "worked_example": "example",
    }
    counters: Counter[str] = Counter()
    result: dict[str, str] = {}
    for binding in sorted(bindings, key=lambda item: item.binding_id):
        if (
            binding.binding_id in CURATED_INTERNAL_PROJECTIONS
            or binding.binding_id in CURATED_LINEAGE_PROJECTIONS
            or derive_nonclaim(binding) is not None
        ):
            continue
        kind = _retained_kind(binding)
        counters[kind] += 1
        result[binding.binding_id] = (
            f"telos.surface.{prefixes[kind]}.{counters[kind]:04d}"
        )
    return result


def build_retained_claim(
    root: Path,
    binding: AtomBinding,
    kind: str,
    claim_id: str,
) -> dict[str, Any]:
    source = _surface_source(
        root,
        binding.segment.path,
        binding=binding,
    )
    mode = RETAINED_POLICY[kind]["derivation_mode"]
    digest_payload = json.dumps(
        {
            "binding_id": binding.binding_id,
            "normalized_atom": binding.atom.normalized,
            "source": {
                "path": source["path"],
                "sha256": source["sha256"],
            },
        },
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    unresolved_retained = kind in {
        "external_citation",
        "historical_empirical",
    }
    value: dict[str, Any] = {"surface_atom": binding.atom.normalized}
    if unresolved_retained:
        value["semantic_metadata_resolution"] = (
            UNRESOLVED_RETAINED_SEMANTIC_STATE
        )
    return {
        "claim_id": claim_id,
        "revision": 1,
        "status": (
            "historical"
            if kind == "historical_empirical"
            else RETAINED_POLICY[kind]["status"]
        ),
        "kind": kind,
        "unit": (
            UNRESOLVED_RETAINED_UNIT
            if unresolved_retained
            else "retained quantitative value in one exact public-surface segment"
        ),
        "cohort": (
            UNRESOLVED_RETAINED_COHORT
            if unresolved_retained
            else "not applicable or not locally adjudicated for this retained claim kind"
        ),
        "independence_boundary": (
            UNRESOLVED_RETAINED_INDEPENDENCE
            if unresolved_retained
            else (
                "Retained surface classification only; no local regeneration "
                "or independent semantic adjudication is implied."
            )
        ),
        "value": value,
        "missingness": _retained_missingness(binding, kind),
        "excluded_inferences": (
            list(UNRESOLVED_RETAINED_EXCLUSIONS)
            if unresolved_retained
            else [
                "independent semantic ground truth",
                "unscoped population inference",
            ]
        ),
        "derivation": {
            "mode": mode,
            "argv": [],
            "output_pointer": "/value/surface_atom",
            "input_digest_sha256": hashlib.sha256(digest_payload).hexdigest(),
        },
        "sources": [source],
        "surface_binding_ids": [binding.binding_id],
        "supersedes": [],
        "superseded_by": None,
    }


def _expected_resolution(
    root: Path,
    binding: AtomBinding,
    *,
    retained_claim_ids: dict[str, str],
) -> tuple[dict[str, Any], dict[str, Any] | None]:
    invalid_syntax = _invalid_atom_syntax(binding)
    if invalid_syntax is not None:
        raise InvalidSurfaceQuantitativeSyntax(
            f"{binding.segment.path} [{binding.segment.locator}] "
            f"{binding.atom.text!r}: {invalid_syntax}"
        )
    curated = CURATED_INTERNAL_PROJECTIONS.get(binding.binding_id)
    if curated is not None:
        resolution = {
            "type": "claim_projection",
            "claim_id": curated["claim_id"],
            "projection": curated["projection"],
        }
        return resolution, None
    lineage = CURATED_LINEAGE_PROJECTIONS.get(binding.binding_id)
    if lineage is not None:
        return {
            "type": "claim_projection",
            "claim_id": lineage["claim_id"],
            "projection": lineage["projection"],
        }, None
    nonclaim = derive_nonclaim(binding)
    if nonclaim is not None:
        return nonclaim, None
    kind = _retained_kind(binding)
    claim_id = retained_claim_ids.get(binding.binding_id)
    if claim_id is None:
        raise ValueError(
            "initial retained-claim ID was not explicitly allocated for "
            f"{binding.binding_id}"
        )
    retained = build_retained_claim(root, binding, kind, claim_id)
    return {
        "type": "claim_projection",
        "claim_id": retained["claim_id"],
        "projection": {
            "operator": "equals",
            "pointer": "/value/surface_atom",
            "currency": binding.atom.normalized.get("currency", False),
            "percent": binding.atom.normalized.get("percent", False),
        },
    }, retained


def _binding_record(
    root: Path,
    binding: AtomBinding,
    *,
    retained_claim_ids: dict[str, str],
) -> tuple[dict[str, Any], dict[str, Any] | None]:
    resolution, retained = _expected_resolution(
        root,
        binding,
        retained_claim_ids=retained_claim_ids,
    )
    return {
        "binding_id": binding.binding_id,
        "path": binding.segment.path,
        "locator": binding.segment.locator,
        "structural_anchor_sha256": binding.segment.anchor_sha256,
        "segment_ordinal": binding.segment.segment_ordinal,
        "atom_ordinal": binding.atom_ordinal,
        "atom": {
            "text": binding.atom.text,
            "normalized": binding.atom.normalized,
        },
        "role": atom_role(binding),
        "resolution": resolution,
    }, retained


def propose_wording_rebind(
    registry: dict[str, Any],
    *,
    old_binding_id: str,
    replacement: AtomBinding,
) -> dict[str, Any]:
    """Return a review candidate for a wording-only claim-binding move.

    The operation is intentionally pure: it does not write a registry, refresh
    a surface digest, or update the hard-coded authorization digest.  Reviewers
    must separately inspect and authorize those changes.  A changed numeric
    atom is a material correction and is rejected here.
    """

    candidate = deepcopy(registry)
    bindings = candidate.get("bindings")
    claims = candidate.get("claims")
    if not isinstance(bindings, list) or not isinstance(claims, dict):
        raise ValueError("rebind candidate registry schema is malformed")
    matches = [
        binding
        for binding in bindings
        if isinstance(binding, dict)
        and binding.get("binding_id") == old_binding_id
    ]
    if len(matches) != 1:
        raise ValueError(
            f"wording rebind requires exactly one old binding: {old_binding_id}"
        )
    if replacement.binding_id == old_binding_id:
        raise ValueError(
            f"wording rebind must move to a distinct binding: {old_binding_id}"
        )
    if any(
        isinstance(binding, dict)
        and binding.get("binding_id") == replacement.binding_id
        and replacement.binding_id != old_binding_id
        for binding in bindings
    ):
        raise ValueError(
            f"wording rebind replacement ID already exists: "
            f"{replacement.binding_id}"
        )
    old = matches[0]
    old_atom = old.get("atom")
    resolution = old.get("resolution")
    if (
        isinstance(resolution, dict)
        and resolution.get("type") == "typed_non_claim"
    ):
        replacement_resolution = derive_nonclaim(replacement)
        if replacement_resolution is None:
            raise ValueError(
                "typed-nonclaim rebind is not licensed by an exact lexical rule"
            )
        bindings[bindings.index(old)] = _live_binding_record(
            replacement,
            replacement_resolution,
        )
        bindings.sort(key=lambda item: item["binding_id"])
        return candidate
    if (
        not isinstance(old_atom, dict)
        or old_atom.get("normalized") != replacement.atom.normalized
        or old.get("role") != atom_role(replacement)
    ):
        raise ValueError(
            "wording rebind changed the normalized atom or quantitative role; "
            "record a material correction lineage instead"
        )
    if (
        not isinstance(resolution, dict)
        or resolution.get("type") != "claim_projection"
        or not isinstance(resolution.get("claim_id"), str)
    ):
        raise ValueError("wording rebind requires a claim projection")
    claim_id = resolution["claim_id"]
    claim = claims.get(claim_id)
    if not isinstance(claim, dict):
        raise ValueError(f"wording rebind claim is missing: {claim_id}")
    surface_ids = claim.get("surface_binding_ids")
    revision = claim.get("revision")
    if (
        not isinstance(surface_ids, list)
        or surface_ids.count(old_binding_id) != 1
        or type(revision) is not int
        or revision < 1
    ):
        raise ValueError("wording rebind claim reciprocity/revision is malformed")

    replacement_record = {
        "binding_id": replacement.binding_id,
        "path": replacement.segment.path,
        "locator": replacement.segment.locator,
        "structural_anchor_sha256": replacement.segment.anchor_sha256,
        "segment_ordinal": replacement.segment.segment_ordinal,
        "atom_ordinal": replacement.atom_ordinal,
        "atom": {
            "text": replacement.atom.text,
            "normalized": replacement.atom.normalized,
        },
        "role": atom_role(replacement),
        "resolution": deepcopy(resolution),
    }
    bindings[bindings.index(old)] = replacement_record
    bindings.sort(key=lambda item: item["binding_id"])
    claim["surface_binding_ids"] = sorted(
        replacement.binding_id if item == old_binding_id else item
        for item in surface_ids
    )
    claim["revision"] = revision + 1
    return candidate


MIGRATION_SCHEMA_VERSION = "telos.claim_registry_migration.v2"


def _canonical_json_sha256(value: Any) -> str:
    encoded = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _git_blob_bytes(root: Path, commit: str, path: str) -> bytes:
    result = subprocess.run(
        ["git", "show", f"{commit}:{path}"],
        cwd=root,
        check=False,
        capture_output=True,
    )
    if result.returncode != 0:
        detail = result.stderr.decode("utf-8", errors="replace").strip()
        raise ValueError(f"cannot read prior registry Git blob: {detail}")
    return result.stdout


def _bindings_from_blob_bytes(
    path: str,
    blob: bytes,
) -> dict[str, AtomBinding]:
    """Reconstruct exact quantitative bindings from retained public bytes."""

    try:
        text = blob.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ValueError(
            f"retained public surface is not UTF-8: {path}"
        ) from exc
    if path.endswith(".json"):
        try:
            value = json.loads(
                text,
                object_pairs_hook=_object_no_duplicates,
                parse_constant=_reject_json_constant,
            )
        except (json.JSONDecodeError, DuplicateKeyError, ValueError) as exc:
            raise ValueError(
                f"retained public JSON surface is invalid: {path}: {exc}"
            ) from exc
        pieces = list(_json_leaf_segments(value))
    else:
        pieces = _split_text_segments(path, text)

    duplicate_count: defaultdict[str, int] = defaultdict(int)
    bindings: dict[str, AtomBinding] = {}
    for locator, segment_text in pieces:
        atoms = quantitative_atoms(segment_text)
        if not atoms:
            continue
        skeleton = _skeleton(segment_text, atoms)
        seed = f"{path}\0{normalize_space(locator)}\0{skeleton}"
        anchor = hashlib.sha256(seed.encode("utf-8")).hexdigest()
        ordinal = duplicate_count[anchor]
        duplicate_count[anchor] += 1
        segment = Segment(
            path=path,
            locator=normalize_space(locator),
            text=segment_text,
            skeleton=skeleton,
            segment_ordinal=ordinal,
            anchor_sha256=anchor,
            atoms=atoms,
        )
        for atom_ordinal, atom in enumerate(atoms):
            binding_id = (
                f"{path}:{anchor[:20]}:{ordinal}:{atom_ordinal}"
            )
            if binding_id in bindings:
                raise ValueError(
                    f"retained public binding is not unique: {binding_id}"
                )
            bindings[binding_id] = AtomBinding(
                binding_id=binding_id,
                segment=segment,
                atom_ordinal=atom_ordinal,
                atom=atom,
            )
    return bindings


def _prior_binding_historical_source(
    root: Path,
    prior_registry: dict[str, Any],
    prior_binding: dict[str, Any],
    evidence_commit: str,
) -> dict[str, Any]:
    """Bind a predecessor to its exact public segment at the sealed commit.

    This intentionally derives the segment from the evidenced Git tree rather
    than trusting a claim's source list.  Internally regenerated claims cite
    their scientific derivation inputs, not presentation segments, so their
    old public wording must remain recoverable through the prior binding record.
    """

    binding_id = prior_binding.get("binding_id")
    path = prior_binding.get("path")
    if (
        not isinstance(binding_id, str)
        or not isinstance(path, str)
        or _canonical_source_path(path) is None
        or re.fullmatch(r"[0-9a-f]{40}", evidence_commit) is None
    ):
        raise ValueError("material predecessor prior binding metadata is invalid")
    declared = prior_registry.get("declared_surfaces")
    declared_matches = [
        item
        for item in declared
        if isinstance(item, dict) and item.get("path") == path
    ] if isinstance(declared, list) else []
    if len(declared_matches) != 1:
        raise ValueError(
            f"material predecessor path is not one prior public surface: {path}"
        )
    declared_digest = declared_matches[0].get("sha256")
    if (
        not isinstance(declared_digest, str)
        or SHA256_RE.fullmatch(declared_digest) is None
    ):
        raise ValueError(
            f"material predecessor prior surface digest is invalid: {path}"
        )
    blob = _git_blob_bytes(root, evidence_commit, path)
    if hashlib.sha256(blob).hexdigest() != declared_digest:
        raise ValueError(
            f"material predecessor prior public surface differs: {path}"
        )
    retained = _bindings_from_blob_bytes(path, blob).get(binding_id)
    if retained is None:
        raise ValueError(
            f"material predecessor binding is absent at prior commit: {binding_id}"
        )
    structural_fields = {
        "binding_id": retained.binding_id,
        "path": retained.segment.path,
        "locator": retained.segment.locator,
        "structural_anchor_sha256": retained.segment.anchor_sha256,
        "segment_ordinal": retained.segment.segment_ordinal,
        "atom_ordinal": retained.atom_ordinal,
    }
    if any(
        prior_binding.get(field) != expected
        for field, expected in structural_fields.items()
    ):
        raise ValueError(
            f"material predecessor prior binding structure differs: {binding_id}"
        )
    expected_atom = {
        "text": retained.atom.text,
        "normalized": retained.atom.normalized,
    }
    if (
        prior_binding.get("atom") != expected_atom
        or prior_binding.get("role") != atom_role(retained)
    ):
        raise ValueError(
            f"material predecessor prior atom/role differs: {binding_id}"
        )
    return {
        "path": path,
        "sha256": hashlib.sha256(
            retained.segment.text.encode("utf-8")
        ).hexdigest(),
        "classification": "historical_git_blob",
        "seal_ids": [],
        "digest_scope": "normalized_surface_segment_at_commit",
        "reference_commit": evidence_commit,
        "binding_id": binding_id,
    }


def _expected_material_predecessor_sources(
    prior_claim: dict[str, Any],
    historical_sources: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    """Return the only licensed provenance transition for a predecessor."""

    prior_sources = prior_claim.get("sources")
    if (
        not isinstance(prior_sources, list)
        or any(not isinstance(source, dict) for source in prior_sources)
    ):
        raise ValueError("material predecessor prior sources are malformed")
    expected: list[dict[str, Any]] = []
    converted: set[str] = set()
    for source in prior_sources:
        binding_id = source.get("binding_id")
        if (
            source.get("digest_scope")
            == "normalized_surface_segment_utf8"
            and isinstance(binding_id, str)
            and binding_id in historical_sources
        ):
            historical = historical_sources[binding_id]
            expected_mutable = {
                "path": historical["path"],
                "sha256": historical["sha256"],
                "classification": "mutable",
                "seal_ids": [],
                "digest_scope": "normalized_surface_segment_utf8",
                "binding_id": binding_id,
            }
            if source != expected_mutable or binding_id in converted:
                raise ValueError(
                    "material predecessor prior segment source differs: "
                    f"{binding_id}"
                )
            converted.add(binding_id)
            continue
        expected.append(deepcopy(source))
    for binding_id in sorted(historical_sources):
        historical = historical_sources[binding_id]
        if historical in expected:
            raise ValueError(
                "material predecessor historical source already exists: "
                f"{binding_id}"
            )
        expected.append(deepcopy(historical))
    return expected


def _prior_registry_from_evidence(
    root: Path,
    evidence: Any,
    *,
    expected_active_gate: str,
) -> dict[str, Any]:
    required = {
        "commit",
        "registry_path",
        "registry_sha256",
        "coverage_report_path",
        "coverage_report_sha256",
        "report_seal_id",
    }
    if not isinstance(evidence, dict) or set(evidence) != required:
        raise ValueError("prior registry evidence fields differ")
    if any(not isinstance(evidence.get(field), str) for field in required):
        raise ValueError("prior registry evidence fields must be strings")
    commit = evidence["commit"]
    if re.fullmatch(r"[0-9a-f]{40}", commit) is None:
        raise ValueError("prior registry evidence commit is not a full Git ID")
    if evidence["registry_path"] != REGISTRY_PATH.as_posix():
        raise ValueError("prior registry evidence path differs")
    for field in ("registry_sha256", "coverage_report_sha256"):
        if SHA256_RE.fullmatch(evidence[field]) is None:
            raise ValueError(f"prior registry evidence {field} is invalid")
    registry_bytes = _git_blob_bytes(root, commit, evidence["registry_path"])
    if hashlib.sha256(registry_bytes).hexdigest() != evidence["registry_sha256"]:
        raise ValueError("prior registry Git blob digest differs")
    try:
        prior = json.loads(
            registry_bytes,
            object_pairs_hook=_object_no_duplicates,
            parse_constant=_reject_json_constant,
        )
    except (json.JSONDecodeError, DuplicateKeyError, ValueError) as exc:
        raise ValueError(f"prior registry Git blob is invalid JSON: {exc}") from exc
    if not isinstance(prior, dict):
        raise ValueError("prior registry Git blob is not an object")
    if prior.get("coverage_report_path") != evidence["coverage_report_path"]:
        raise ValueError("prior registry coverage-report path differs")

    report_bytes = _git_blob_bytes(
        root,
        commit,
        evidence["coverage_report_path"],
    )
    if hashlib.sha256(report_bytes).hexdigest() != evidence[
        "coverage_report_sha256"
    ]:
        raise ValueError("prior coverage-report Git blob digest differs")
    try:
        report = json.loads(
            report_bytes,
            object_pairs_hook=_object_no_duplicates,
            parse_constant=_reject_json_constant,
        )
    except (json.JSONDecodeError, DuplicateKeyError, ValueError) as exc:
        raise ValueError(
            f"prior coverage-report Git blob is invalid JSON: {exc}"
        ) from exc
    if not isinstance(report, dict) or report.get("registry_sha256") != evidence[
        "registry_sha256"
    ]:
        raise ValueError("prior coverage report does not bind the registry blob")
    if (
        prior.get("active_gate") != expected_active_gate
        or report.get("active_gate") != prior.get("active_gate")
    ):
        raise ValueError("prior registry/report active gate differs")
    required_acceptance = {
        "unclassified_count": 0,
        "conflicting_projection_count": 0,
        "binding_authority_passed": True,
        "internal_prerequisite_passed": True,
        "stale_superseded_assertion_count": 0,
    }
    acceptance_drift = {
        field: report.get(field)
        for field, expected in required_acceptance.items()
        if type(report.get(field)) is not type(expected)
        or report.get(field) != expected
    }
    if acceptance_drift:
        raise ValueError(
            "prior coverage report does not retain accepted C1 controls: "
            f"{acceptance_drift}"
        )
    verified_predecessors = report.get(
        "verified_material_predecessor_ids"
    )
    if (
        not isinstance(verified_predecessors, list)
        or any(
            not isinstance(claim_id, str) or not claim_id
            for claim_id in verified_predecessors
        )
        or verified_predecessors != sorted(set(verified_predecessors))
    ):
        raise ValueError(
            "prior coverage report verified predecessor IDs are invalid"
        )
    prior_claims = prior.get("claims")
    prior_bindings = prior.get("bindings")
    if not isinstance(prior_claims, dict) or not isinstance(
        prior_bindings, list
    ):
        if verified_predecessors:
            raise ValueError(
                "prior coverage report names predecessors in a malformed registry"
            )
        prior_claims = {}
        prior_bindings = []
    for claim_id in verified_predecessors:
        predecessor = prior_claims.get(claim_id)
        historical_sources = (
            predecessor.get("sources")
            if isinstance(predecessor, dict)
            else None
        )
        if (
            not isinstance(predecessor, dict)
            or not isinstance(predecessor.get("superseded_by"), str)
            or not isinstance(historical_sources, list)
            or not any(
                isinstance(source, dict)
                and source.get("classification") == "historical_git_blob"
                and source.get("digest_scope")
                == "normalized_surface_segment_at_commit"
                for source in historical_sources
            )
        ):
            raise ValueError(
                "prior coverage report verified predecessor lineage differs: "
                f"{claim_id}"
            )
        current_id = claim_id
        seen_lineage: set[str] = set()
        while True:
            if current_id in seen_lineage:
                raise ValueError(
                    "prior coverage report verified predecessor lineage cycles: "
                    f"{claim_id}"
                )
            seen_lineage.add(current_id)
            current_claim = prior_claims.get(current_id)
            if not isinstance(current_claim, dict):
                raise ValueError(
                    "prior coverage report verified predecessor lineage "
                    f"is missing: {claim_id}"
                )
            successor_id = current_claim.get("superseded_by")
            if successor_id is None:
                head_id = current_id
                head = current_claim
                break
            successor = (
                prior_claims.get(successor_id)
                if isinstance(successor_id, str)
                else None
            )
            if (
                not isinstance(successor_id, str)
                or not isinstance(successor, dict)
                or current_id not in successor.get("supersedes", [])
            ):
                raise ValueError(
                    "prior coverage report verified predecessor lineage "
                    f"is not reciprocal: {claim_id}"
                )
            current_id = successor_id
        head_binding_ids = head.get("surface_binding_ids")
        if (
            not isinstance(head_binding_ids, list)
            or not head_binding_ids
            or any(
                not any(
                    isinstance(binding, dict)
                    and binding.get("binding_id") == binding_id
                    and isinstance(binding.get("resolution"), dict)
                    and binding["resolution"].get("type")
                    == "claim_projection"
                    and binding["resolution"].get("claim_id") == head_id
                    for binding in prior_bindings
                )
                for binding_id in head_binding_ids
            )
        ):
            raise ValueError(
                "prior coverage report verified predecessor lineage head "
                f"is not authoritatively bound: {claim_id}"
            )
    prior_lineage_failures = _supersession_failures(
        prior_claims,
        verified_material_predecessor_ids=frozenset(
            verified_predecessors
        ),
    )
    if prior_lineage_failures:
        raise ValueError(
            "prior coverage report retained lineage is invalid: "
            + "; ".join(prior_lineage_failures)
        )
    seal_registry = read_json(root / SEAL_REGISTRY_PATH)
    member, sealed_digest = _seal_membership(
        root,
        seal_registry,
        evidence["report_seal_id"],
        evidence["coverage_report_path"],
    )
    if not member or sealed_digest != evidence["coverage_report_sha256"]:
        raise ValueError(
            "prior coverage report lacks exact retained seal membership: "
            f"{sealed_digest}"
        )
    return prior


def _prior_report_verified_predecessor_ids(
    root: Path,
    evidence: dict[str, Any],
) -> frozenset[str]:
    report_bytes = _git_blob_bytes(
        root,
        evidence["commit"],
        evidence["coverage_report_path"],
    )
    report = json.loads(
        report_bytes,
        object_pairs_hook=_object_no_duplicates,
        parse_constant=_reject_json_constant,
    )
    values = report["verified_material_predecessor_ids"]
    return frozenset(values)


def _live_binding_record(
    binding: AtomBinding,
    resolution: dict[str, Any],
) -> dict[str, Any]:
    return {
        "binding_id": binding.binding_id,
        "path": binding.segment.path,
        "locator": binding.segment.locator,
        "structural_anchor_sha256": binding.segment.anchor_sha256,
        "segment_ordinal": binding.segment.segment_ordinal,
        "atom_ordinal": binding.atom_ordinal,
        "atom": {
            "text": binding.atom.text,
            "normalized": binding.atom.normalized,
        },
        "role": atom_role(binding),
        "resolution": deepcopy(resolution),
    }


def build_migration_candidate(
    root: Path,
    prior_registry: dict[str, Any],
    plan: dict[str, Any],
    *,
    require_current_prior: bool = True,
) -> dict[str, Any]:
    """Build an explicit, non-writing future-gate migration candidate.

    Nothing is inferred for a new atom.  Wording-only moves must be named as
    old/new binding pairs; additions require an exact reviewed resolution;
    removals and any semantic claim replacement are explicit.  The returned
    candidate still requires the new gate's hard-coded authorization digest
    before it can validate or be written.
    """

    required_plan = {
        "schema_version",
        "prior_registry_canonical_sha256",
        "from_active_gate",
        "to_active_gate",
        "plan_path",
        "prior_registry_evidence",
        "rebindings",
        "material_binding_updates",
        "lineage_binding_reassignments",
        "removed_binding_ids",
        "new_binding_resolutions",
        "new_claims",
        "claim_updates",
    }
    if set(plan) != required_plan:
        raise ValueError("claim migration plan fields differ")
    if plan.get("schema_version") != MIGRATION_SCHEMA_VERSION:
        raise ValueError("claim migration plan schema differs")
    if (
        plan.get("prior_registry_canonical_sha256")
        != _canonical_json_sha256(prior_registry)
    ):
        raise ValueError("claim migration prior-registry digest differs")
    evidenced_prior = _prior_registry_from_evidence(
        root,
        plan.get("prior_registry_evidence"),
        expected_active_gate=plan.get("from_active_gate"),
    )
    if evidenced_prior != prior_registry:
        raise ValueError("claim migration prior registry differs from sealed evidence")
    if require_current_prior:
        current_prior = read_json(root / REGISTRY_PATH)
        if current_prior != prior_registry:
            raise ValueError(
                "claim migration prior registry is not the current authority"
            )
    prior_gate = prior_registry.get("active_gate")
    if plan.get("from_active_gate") != prior_gate:
        raise ValueError("claim migration source gate differs")
    current = read_json(root / "mission/current.json")
    target_gate = current.get("active_gate")
    if (
        not isinstance(target_gate, str)
        or plan.get("to_active_gate") != target_gate
    ):
        raise ValueError("claim migration target gate differs from current pointer")
    plan_path = plan.get("plan_path")
    expected_plan_parent = PurePosixPath(target_gate).parent / "proof"
    plan_candidate = (
        PurePosixPath(plan_path) if isinstance(plan_path, str) else None
    )
    if (
        not isinstance(plan_path, str)
        or _canonical_source_path(plan_path) is None
        or plan_candidate is None
        or plan_candidate.parent != expected_plan_parent
        or plan_candidate.name != "claim_registry_migration.json"
    ):
        raise ValueError("claim migration plan path is not target-gate scoped")

    prior_revision = prior_registry.get("revision")
    if type(prior_revision) is not int or prior_revision < 1:
        raise ValueError("claim migration prior revision is invalid")
    candidate = deepcopy(prior_registry)
    bindings = candidate.get("bindings")
    claims = candidate.get("claims")
    if not isinstance(bindings, list) or not isinstance(claims, dict):
        raise ValueError("claim migration prior registry is malformed")
    live_by_id = {
        binding.binding_id: binding for binding in extract_all_bindings(root)
    }

    rebindings = plan.get("rebindings")
    material_updates = plan.get("material_binding_updates")
    lineage_reassignments = plan.get("lineage_binding_reassignments")
    removed_ids = plan.get("removed_binding_ids")
    new_resolutions = plan.get("new_binding_resolutions")
    new_claims = plan.get("new_claims")
    claim_updates = plan.get("claim_updates")
    if (
        not isinstance(rebindings, list)
        or any(
            not isinstance(item, dict)
            or set(item) != {"old_binding_id", "new_binding_id"}
            or not isinstance(item.get("old_binding_id"), str)
            or not isinstance(item.get("new_binding_id"), str)
            for item in rebindings
        )
        or not isinstance(material_updates, list)
        or any(
            not isinstance(item, dict)
            or set(item) != {"binding_id", "new_resolution"}
            or not isinstance(item.get("binding_id"), str)
            or not isinstance(item.get("new_resolution"), dict)
            for item in material_updates
        )
        or not isinstance(lineage_reassignments, list)
        or any(
            not isinstance(item, dict)
            or set(item) != {"binding_id", "new_resolution"}
            or not isinstance(item.get("binding_id"), str)
            or not isinstance(item.get("new_resolution"), dict)
            for item in lineage_reassignments
        )
        or not isinstance(removed_ids, list)
        or any(not isinstance(item, str) for item in removed_ids)
        or len(removed_ids) != len(set(removed_ids))
        or not isinstance(new_resolutions, dict)
        or any(
            not isinstance(key, str) or not isinstance(value, dict)
            for key, value in new_resolutions.items()
        )
        or not isinstance(new_claims, dict)
        or any(
            not isinstance(key, str) or not isinstance(value, dict)
            for key, value in new_claims.items()
        )
        or not isinstance(claim_updates, dict)
        or any(
            not isinstance(key, str) or not isinstance(value, dict)
            for key, value in claim_updates.items()
        )
    ):
        raise ValueError("claim migration plan collection types are invalid")
    if not any(
        (
            rebindings,
            material_updates,
            lineage_reassignments,
            removed_ids,
            new_resolutions,
            new_claims,
            claim_updates,
        )
    ):
        raise ValueError("claim migration plan contains no reviewed transition")

    affected_claims: set[str] = set()
    claim_wording_rebindings: defaultdict[
        str, list[tuple[str, str]]
    ] = defaultdict(list)
    seen_old: set[str] = set()
    seen_new: set[str] = set()
    for item in rebindings:
        old_id = item["old_binding_id"]
        new_id = item["new_binding_id"]
        if old_id == new_id:
            raise ValueError(
                f"claim migration wording rebind is a no-op: {old_id}"
            )
        if old_id in seen_old or new_id in seen_new:
            raise ValueError("claim migration rebindings are not one-to-one")
        seen_old.add(old_id)
        seen_new.add(new_id)
        replacement = live_by_id.get(new_id)
        if replacement is None:
            raise ValueError(f"claim migration rebind target is not live: {new_id}")
        before = next(
            (
                binding
                for binding in candidate["bindings"]
                if isinstance(binding, dict)
                and binding.get("binding_id") == old_id
            ),
            None,
        )
        if not isinstance(before, dict):
            raise ValueError(f"claim migration old binding is absent: {old_id}")
        resolution = before.get("resolution")
        if isinstance(resolution, dict) and isinstance(
            resolution.get("claim_id"), str
        ):
            affected_claims.add(resolution["claim_id"])
            claim_wording_rebindings[resolution["claim_id"]].append(
                (old_id, new_id)
            )
        candidate = propose_wording_rebind(
            candidate,
            old_binding_id=old_id,
            replacement=replacement,
        )

    bindings = candidate["bindings"]
    claims = candidate["claims"]
    material_binding_ids: set[str] = set()
    material_historical_sources: defaultdict[
        str, dict[str, dict[str, Any]]
    ] = defaultdict(dict)
    material_successors: dict[str, str] = {}
    prior_bindings_by_id = {
        binding.get("binding_id"): binding
        for binding in prior_registry.get("bindings", [])
        if isinstance(binding, dict)
        and isinstance(binding.get("binding_id"), str)
    }
    for item in material_updates:
        binding_id = item["binding_id"]
        if binding_id in material_binding_ids:
            raise ValueError("claim migration material binding update is duplicated")
        material_binding_ids.add(binding_id)
        live = live_by_id.get(binding_id)
        old = next(
            (
                binding
                for binding in bindings
                if isinstance(binding, dict)
                and binding.get("binding_id") == binding_id
            ),
            None,
        )
        if live is None or not isinstance(old, dict):
            raise ValueError(
                f"claim migration material binding is not retained/live: "
                f"{binding_id}"
            )
        old_resolution = old.get("resolution")
        new_resolution = item["new_resolution"]
        old_claim_id = (
            old_resolution.get("claim_id")
            if isinstance(old_resolution, dict)
            and old_resolution.get("type") == "claim_projection"
            else None
        )
        new_claim_id = (
            new_resolution.get("claim_id")
            if new_resolution.get("type") == "claim_projection"
            else None
        )
        if (
            isinstance(old_resolution, dict)
            and old_resolution.get("type") == "typed_non_claim"
            and new_resolution.get("type") == "typed_non_claim"
        ):
            old_atom = old.get("atom")
            if (
                isinstance(old_atom, dict)
                and old_atom.get("normalized") == live.atom.normalized
                and old.get("role") == atom_role(live)
            ):
                raise ValueError(
                    f"material typed-nonclaim update is a no-op: {binding_id}"
                )
            expected_nonclaim = derive_nonclaim(live)
            if expected_nonclaim != new_resolution:
                raise ValueError(
                    "material typed-nonclaim update is not licensed by the "
                    f"live exact lexical rule: {binding_id}"
                )
            bindings[bindings.index(old)] = _live_binding_record(
                live,
                new_resolution,
            )
            continue
        if (
            not isinstance(old_claim_id, str)
            or not isinstance(new_claim_id, str)
            or old_claim_id == new_claim_id
            or new_claim_id not in new_claims
            or old_claim_id not in claim_updates
        ):
            raise ValueError(
                "material binding update requires distinct explicit "
                f"predecessor/successor claims: {binding_id}"
            )
        old_normalized = (
            old.get("atom", {}).get("normalized")
            if isinstance(old.get("atom"), dict)
            else None
        )
        if (
            old_normalized == live.atom.normalized
            and old.get("role") == atom_role(live)
        ):
            raise ValueError(
                f"material binding update did not change value/role: {binding_id}"
            )
        predecessor_update = claim_updates[old_claim_id]
        successor = new_claims[new_claim_id]
        if (
            predecessor_update.get("superseded_by") != new_claim_id
            or not isinstance(predecessor_update.get("status"), str)
            or predecessor_update.get("status")
            not in {"corrected", "retracted"}
            or old_claim_id not in successor.get("supersedes", [])
            or binding_id in predecessor_update.get("surface_binding_ids", [])
            or binding_id not in successor.get("surface_binding_ids", [])
        ):
            raise ValueError(
                f"material binding update lineage/reciprocity is incomplete: "
                f"{binding_id}"
            )
        prior_successor = material_successors.get(old_claim_id)
        if prior_successor is not None and prior_successor != new_claim_id:
            raise ValueError(
                "material predecessor has multiple correction successors: "
                f"{old_claim_id}"
            )
        material_successors[old_claim_id] = new_claim_id
        evidence = plan["prior_registry_evidence"]
        evidence_commit = (
            evidence.get("commit") if isinstance(evidence, dict) else None
        )
        prior_binding = prior_bindings_by_id.get(binding_id)
        if not isinstance(prior_binding, dict) or not isinstance(
            evidence_commit, str
        ):
            raise ValueError(
                "material binding predecessor lacks one exact prior binding: "
                f"{binding_id}"
            )
        expected_historical_source = _prior_binding_historical_source(
            root,
            prior_registry,
            prior_binding,
            evidence_commit,
        )
        material_historical_sources[old_claim_id][
            binding_id
        ] = expected_historical_source
        matched, detail = projection_matches(
            live,
            successor,
            new_resolution.get("projection")
            if isinstance(new_resolution.get("projection"), dict)
            else {},
        )
        if not matched:
            raise ValueError(
                f"material binding update successor projection conflicts: "
                f"{binding_id}: {detail}"
            )
        bindings[bindings.index(old)] = _live_binding_record(
            live,
            new_resolution,
        )
        affected_claims.update({old_claim_id, new_claim_id})

    lineage_binding_ids: set[str] = set()
    for item in lineage_reassignments:
        binding_id = item["binding_id"]
        if (
            binding_id in lineage_binding_ids
            or binding_id in material_binding_ids
        ):
            raise ValueError(
                "claim migration lineage binding reassignment is duplicated "
                f"or overlaps a material update: {binding_id}"
            )
        lineage_binding_ids.add(binding_id)
        live = live_by_id.get(binding_id)
        old = next(
            (
                binding
                for binding in bindings
                if isinstance(binding, dict)
                and binding.get("binding_id") == binding_id
            ),
            None,
        )
        if live is None or not isinstance(old, dict):
            raise ValueError(
                "claim migration lineage binding is not retained/live: "
                f"{binding_id}"
            )
        old_resolution = old.get("resolution")
        new_resolution = item["new_resolution"]
        old_claim_id = (
            old_resolution.get("claim_id")
            if isinstance(old_resolution, dict)
            and old_resolution.get("type") == "claim_projection"
            else None
        )
        new_claim_id = (
            new_resolution.get("claim_id")
            if new_resolution.get("type") == "claim_projection"
            else None
        )
        if (
            not isinstance(old_claim_id, str)
            or not isinstance(new_claim_id, str)
            or material_successors.get(old_claim_id) != new_claim_id
            or old_claim_id not in claim_updates
            or new_claim_id not in new_claims
        ):
            raise ValueError(
                "lineage binding reassignment must target the explicit "
                f"reciprocal material successor: {binding_id}"
            )
        if old != _live_binding_record(live, old_resolution):
            raise ValueError(
                "lineage binding reassignment changed atom or role: "
                f"{binding_id}"
            )
        predecessor_update = claim_updates[old_claim_id]
        successor = new_claims[new_claim_id]
        if (
            predecessor_update.get("superseded_by") != new_claim_id
            or old_claim_id not in successor.get("supersedes", [])
            or binding_id
            in predecessor_update.get("surface_binding_ids", [])
            or binding_id not in successor.get("surface_binding_ids", [])
        ):
            raise ValueError(
                "lineage binding reassignment reciprocity is incomplete: "
                f"{binding_id}"
            )
        matched, detail = projection_matches(
            live,
            successor,
            new_resolution.get("projection")
            if isinstance(new_resolution.get("projection"), dict)
            else {},
        )
        if not matched:
            raise ValueError(
                "lineage binding reassignment successor projection conflicts: "
                f"{binding_id}: {detail}"
            )
        evidence = plan["prior_registry_evidence"]
        evidence_commit = (
            evidence.get("commit") if isinstance(evidence, dict) else None
        )
        prior_binding = prior_bindings_by_id.get(binding_id)
        if not isinstance(prior_binding, dict) or not isinstance(
            evidence_commit, str
        ):
            raise ValueError(
                "lineage binding predecessor lacks one exact prior binding: "
                f"{binding_id}"
            )
        material_historical_sources[old_claim_id][
            binding_id
        ] = _prior_binding_historical_source(
            root,
            prior_registry,
            prior_binding,
            evidence_commit,
        )
        bindings[bindings.index(old)] = _live_binding_record(
            live,
            new_resolution,
        )
        affected_claims.update({old_claim_id, new_claim_id})

    for binding_id in removed_ids:
        matches = [
            binding
            for binding in bindings
            if isinstance(binding, dict)
            and binding.get("binding_id") == binding_id
        ]
        if len(matches) != 1 or binding_id in live_by_id:
            raise ValueError(
                "claim migration removal must name one non-live prior binding: "
                f"{binding_id}"
            )
        removed = matches[0]
        bindings.remove(removed)
        resolution = removed.get("resolution")
        claim_id = (
            resolution.get("claim_id")
            if isinstance(resolution, dict)
            and resolution.get("type") == "claim_projection"
            else None
        )
        if isinstance(claim_id, str):
            claim = claims.get(claim_id)
            surface_ids = (
                claim.get("surface_binding_ids")
                if isinstance(claim, dict)
                else None
            )
            if not isinstance(surface_ids, list) or binding_id not in surface_ids:
                raise ValueError(
                    f"claim migration removal reciprocity is malformed: {binding_id}"
                )
            surface_ids.remove(binding_id)
            affected_claims.add(claim_id)

    for claim_id, replacement in claim_updates.items():
        working_claim = claims.get(claim_id)
        prior_claim = prior_registry.get("claims", {}).get(claim_id)
        if not isinstance(working_claim, dict) or not isinstance(
            prior_claim, dict
        ):
            raise ValueError(
                f"claim migration update targets unknown claim: {claim_id}"
            )
        if (
            replacement.get("claim_id") != claim_id
            or type(replacement.get("revision")) is not int
            or replacement["revision"] != prior_claim.get("revision", 0) + 1
        ):
            raise ValueError(
                f"claim migration update must preserve ID and increment revision: "
                f"{claim_id}"
            )
        if (
            claim_id not in affected_claims
            and all(
                replacement.get(field) == prior_claim.get(field)
                for field in set(prior_claim) - {"revision"}
            )
            and set(replacement) == set(prior_claim)
        ):
            raise ValueError(
                f"claim migration update is a revision-only no-op: {claim_id}"
            )
        immutable_semantic_fields = {
            "kind",
            "unit",
            "cohort",
            "independence_boundary",
            "value",
            "excluded_inferences",
            "derivation",
            "supersedes",
        }
        changed_semantics = sorted(
            field
            for field in immutable_semantic_fields
            if replacement.get(field) != prior_claim.get(field)
        )
        prior_missingness = deepcopy(prior_claim.get("missingness"))
        replacement_missingness = deepcopy(replacement.get("missingness"))
        for missingness in (prior_missingness, replacement_missingness):
            if isinstance(missingness, dict):
                missingness.pop("binding_id", None)
        if prior_missingness != replacement_missingness:
            changed_semantics.append("missingness")
        if changed_semantics:
            raise ValueError(
                "claim migration cannot change material semantics in place; "
                f"create a new successor claim: {claim_id}: "
                f"{changed_semantics}"
            )
        historical_sources = material_historical_sources.get(claim_id)
        if historical_sources:
            expected_sources = _expected_material_predecessor_sources(
                prior_claim,
                historical_sources,
            )
        else:
            expected_sources = prior_claim.get("sources")
        if replacement.get("sources") != expected_sources:
            raise ValueError(
                "claim migration predecessor provenance transition differs: "
                f"{claim_id}"
            )
        status_changed = replacement.get("status") != prior_claim.get("status")
        successor_changed = (
            replacement.get("superseded_by")
            != prior_claim.get("superseded_by")
        )
        if status_changed or successor_changed:
            successor = replacement.get("superseded_by")
            successor_claim = (
                new_claims.get(successor)
                if isinstance(successor, str)
                else None
            )
            if (
                not isinstance(replacement.get("status"), str)
                or replacement.get("status")
                not in {"corrected", "retracted"}
                or not isinstance(successor_claim, dict)
                or claim_id not in successor_claim.get("supersedes", [])
                or material_successors.get(claim_id) != successor
            ):
                raise ValueError(
                    "claim migration status/successor change requires an "
                    "explicit reciprocal material transition: "
                    f"{claim_id}"
                )
        elif replacement.get("status") != prior_claim.get("status"):
            raise ValueError(
                f"claim migration status changed in place: {claim_id}"
            )
        claims[claim_id] = deepcopy(replacement)
        affected_claims.add(claim_id)

    for claim_id, claim in new_claims.items():
        if claim_id in claims or claim.get("claim_id") != claim_id:
            raise ValueError(
                f"claim migration new claim ID is duplicate or inconsistent: "
                f"{claim_id}"
            )
        if claim.get("revision") != 1:
            raise ValueError(
                f"claim migration new claim must begin at revision 1: {claim_id}"
            )
        claims[claim_id] = deepcopy(claim)

    current_binding_ids = {
        binding.get("binding_id")
        for binding in bindings
        if isinstance(binding, dict)
        and isinstance(binding.get("binding_id"), str)
    }
    for binding_id, resolution in new_resolutions.items():
        if binding_id in current_binding_ids or binding_id not in live_by_id:
            raise ValueError(
                f"claim migration new binding is duplicate or not live: {binding_id}"
            )
        record = _live_binding_record(live_by_id[binding_id], resolution)
        bindings.append(record)
        if resolution.get("type") == "claim_projection":
            claim_id = resolution.get("claim_id")
            claim = claims.get(claim_id) if isinstance(claim_id, str) else None
            if not isinstance(claim, dict):
                raise ValueError(
                    f"claim migration new binding references unknown claim: "
                    f"{binding_id}"
                )
            surface_ids = claim.get("surface_binding_ids")
            if not isinstance(surface_ids, list):
                raise ValueError(
                    f"claim migration target claim binding list is malformed: "
                    f"{claim_id}"
                )
            if binding_id not in surface_ids:
                surface_ids.append(binding_id)
            elif surface_ids.count(binding_id) != 1:
                raise ValueError(
                    "claim migration target claim repeats a new binding: "
                    f"{claim_id}: {binding_id}"
                )
            surface_ids.sort()
            affected_claims.add(claim_id)

    for predecessor_id in sorted(material_successors):
        stale_binding_ids = sorted(
            binding.get("binding_id")
            for binding in bindings
            if isinstance(binding, dict)
            and isinstance(binding.get("binding_id"), str)
            and binding["binding_id"] not in CURATED_LINEAGE_PROJECTIONS
            and isinstance(binding.get("resolution"), dict)
            and binding["resolution"].get("type") == "claim_projection"
            and binding["resolution"].get("claim_id") == predecessor_id
        )
        if stale_binding_ids:
            raise ValueError(
                "material correction leaves non-corrective predecessor "
                f"bindings live: {predecessor_id}: {stale_binding_ids}"
            )

    for claim_id in new_claims:
        claim = claims.get(claim_id)
        if not isinstance(claim, dict):
            raise ValueError(
                f"claim migration new claim is malformed: {claim_id}"
            )
        reverse = claim.get("surface_binding_ids")
        expected_reverse = sorted(
            binding.get("binding_id")
            for binding in bindings
            if isinstance(binding, dict)
            and isinstance(binding.get("resolution"), dict)
            and binding["resolution"].get("type") == "claim_projection"
            and binding["resolution"].get("claim_id") == claim_id
            and isinstance(binding.get("binding_id"), str)
        )
        if (
            not isinstance(reverse, list)
            or any(not isinstance(item, str) for item in reverse)
            or len(reverse) != len(set(reverse))
            or sorted(reverse) != expected_reverse
        ):
            raise ValueError(
                f"claim migration new claim reverse bindings differ: {claim_id}"
            )

    final_ids = {
        binding.get("binding_id")
        for binding in bindings
        if isinstance(binding, dict)
        and isinstance(binding.get("binding_id"), str)
    }
    if final_ids != set(live_by_id):
        raise ValueError(
            "claim migration does not exactly cover live bindings: "
            f"extra={sorted(final_ids - set(live_by_id))} "
            f"missing={sorted(set(live_by_id) - final_ids)}"
        )
    for binding in bindings:
        if not isinstance(binding, dict):
            raise ValueError("claim migration binding is not an object")
        binding_id = binding.get("binding_id")
        if not isinstance(binding_id, str):
            raise ValueError("claim migration binding ID is not a string")
        live = live_by_id[binding_id]
        expected_structural = _live_binding_record(
            live,
            binding.get("resolution")
            if isinstance(binding.get("resolution"), dict)
            else {},
        )
        if binding != expected_structural:
            raise ValueError(
                f"claim migration retained binding drifted without an explicit "
                f"rebind: {binding_id}"
            )

    # A mutable presentation file is source evidence for ordinary granular
    # retained claims. Refresh those source/digest fields only by rebuilding
    # the exact claim with its persisted ID and incrementing its revision.
    for claim_id in sorted(affected_claims):
        if claim_id in claim_updates or claim_id in new_claims:
            continue
        claim = claims.get(claim_id)
        prior_claim = prior_registry.get("claims", {}).get(claim_id)
        if not isinstance(claim, dict) or not isinstance(prior_claim, dict):
            raise ValueError(f"claim migration affected claim is malformed: {claim_id}")
        surface_ids = claim.get("surface_binding_ids")
        if (
            isinstance(claim.get("kind"), str)
            and claim.get("kind") in RETAINED_POLICY
            and claim_id != _SELECTOR_PREDECESSOR
            and isinstance(surface_ids, list)
            and len(surface_ids) == 1
        ):
            live = live_by_id[surface_ids[0]]
            rebuilt = build_retained_claim(
                root,
                live,
                claim["kind"],
                claim_id,
            )
            material_fields = {
                "claim_id",
                "kind",
                "unit",
                "cohort",
                "independence_boundary",
                "value",
                "excluded_inferences",
            }
            changed_fields = sorted(
                field
                for field in material_fields
                if rebuilt.get(field) != prior_claim.get(field)
            )
            prior_missingness = deepcopy(prior_claim.get("missingness"))
            rebuilt_missingness = deepcopy(rebuilt.get("missingness"))
            for missingness in (prior_missingness, rebuilt_missingness):
                if isinstance(missingness, dict):
                    missingness.pop("binding_id", None)
            if prior_missingness != rebuilt_missingness:
                changed_fields.append("missingness")
            prior_derivation = deepcopy(prior_claim.get("derivation"))
            rebuilt_derivation = deepcopy(rebuilt.get("derivation"))
            for derivation in (prior_derivation, rebuilt_derivation):
                if isinstance(derivation, dict):
                    derivation.pop("input_digest_sha256", None)
            if prior_derivation != rebuilt_derivation:
                changed_fields.append("derivation")
            if changed_fields:
                raise ValueError(
                    "claim migration retained wording rebind changed material "
                    f"claim fields: {claim_id}: {changed_fields}"
                )
            rebuilt["revision"] = prior_claim["revision"] + 1
            rebuilt["status"] = prior_claim["status"]
            rebuilt["supersedes"] = deepcopy(prior_claim["supersedes"])
            rebuilt["superseded_by"] = prior_claim["superseded_by"]
            claims[claim_id] = rebuilt
        elif claim.get("kind") == "internally_regenerated_empirical":
            rebuilt_internal = builder.build_internal_claims().get(claim_id)
            if not isinstance(rebuilt_internal, dict):
                raise ValueError(
                    f"claim migration cannot rebuild internal claim: {claim_id}"
                )
            expected_internal = deepcopy(rebuilt_internal)
            retained_internal = deepcopy(prior_claim)
            for compared in (expected_internal, retained_internal):
                compared["revision"] = 1
                compared["surface_binding_ids"] = []
            if expected_internal != retained_internal:
                raise ValueError(
                    "claim migration internal wording rebind changed material "
                    f"claim fields or provenance: {claim_id}"
                )
            claim["revision"] = prior_claim["revision"] + 1
            claim["surface_binding_ids"] = sorted(surface_ids)
        elif claim_id == _SELECTOR_PREDECESSOR:
            rebuilt_lineage = build_curated_lineage_claims(root)[claim_id]
            expected_sources = deepcopy(prior_claim.get("sources"))
            if not isinstance(expected_sources, list):
                raise ValueError(
                    "claim migration curated lineage sources are malformed"
                )
            for old_id, new_id in claim_wording_rebindings[claim_id]:
                matching_indices = [
                    index
                    for index, source in enumerate(expected_sources)
                    if isinstance(source, dict)
                    and source.get("digest_scope")
                    == "normalized_surface_segment_utf8"
                    and source.get("binding_id") == old_id
                ]
                if len(matching_indices) != 1:
                    raise ValueError(
                        "claim migration curated lineage wording source differs: "
                        f"{old_id}"
                    )
                replacement_binding = live_by_id[new_id]
                expected_sources[matching_indices[0]] = _surface_source(
                    root,
                    replacement_binding.segment.path,
                    binding=replacement_binding,
                )
            expected_sources = sorted(
                (
                    source
                    for source in expected_sources
                    if isinstance(source, dict)
                    and source.get("digest_scope")
                    == "normalized_surface_segment_utf8"
                ),
                key=lambda source: source["binding_id"],
            ) + [
                source
                for source in expected_sources
                if not (
                    isinstance(source, dict)
                    and source.get("digest_scope")
                    == "normalized_surface_segment_utf8"
                )
            ]
            if rebuilt_lineage.get("sources") != expected_sources:
                raise ValueError(
                    "claim migration curated lineage provenance changed "
                    "outside explicit wording rebindings"
                )
            material_fields = {
                "claim_id",
                "kind",
                "unit",
                "cohort",
                "independence_boundary",
                "value",
                "missingness",
                "excluded_inferences",
            }
            changed_fields = sorted(
                field
                for field in material_fields
                if rebuilt_lineage.get(field) != prior_claim.get(field)
            )
            prior_derivation = deepcopy(prior_claim.get("derivation"))
            rebuilt_derivation = deepcopy(rebuilt_lineage.get("derivation"))
            for derivation in (prior_derivation, rebuilt_derivation):
                if isinstance(derivation, dict):
                    derivation.pop("input_digest_sha256", None)
            if prior_derivation != rebuilt_derivation:
                changed_fields.append("derivation")
            if changed_fields:
                raise ValueError(
                    "claim migration curated lineage wording rebind changed "
                    f"material fields: {claim_id}: {changed_fields}"
                )
            rebuilt_lineage["revision"] = prior_claim["revision"] + 1
            rebuilt_lineage["surface_binding_ids"] = sorted(surface_ids)
            rebuilt_lineage["status"] = prior_claim["status"]
            rebuilt_lineage["supersedes"] = deepcopy(
                prior_claim["supersedes"]
            )
            rebuilt_lineage["superseded_by"] = prior_claim[
                "superseded_by"
            ]
            claims[claim_id] = rebuilt_lineage
        else:
            raise ValueError(
                "claim migration requires an explicit claim update for "
                f"multi-binding or unbound retained claim {claim_id}"
            )

    for claim_id in sorted(affected_claims):
        prior_claim = prior_registry.get("claims", {}).get(claim_id)
        migrated_claim = claims.get(claim_id)
        if not isinstance(prior_claim, dict):
            continue
        if (
            not isinstance(migrated_claim, dict)
            or type(prior_claim.get("revision")) is not int
            or migrated_claim.get("revision") != prior_claim["revision"] + 1
        ):
            raise ValueError(
                "claim migration must increment each affected existing claim "
                f"exactly once: {claim_id}"
            )

    candidate["revision"] = prior_revision + 1
    candidate["active_gate"] = target_gate
    candidate["coverage_report_path"] = report_path_for_gate(target_gate)
    surface_paths = declared_surface_paths(root)
    candidate["declared_surfaces"] = [
        {
            "path": path,
            "format": _surface_format(path),
            "sha256": sha256(root / path),
        }
        for path in surface_paths
    ]
    candidate["bindings"] = sorted(
        bindings,
        key=lambda item: item["binding_id"],
    )
    candidate["claims"] = {
        claim_id: claims[claim_id] for claim_id in sorted(claims)
    }
    candidate["migration"] = {
        "schema_version": MIGRATION_SCHEMA_VERSION,
        "plan_path": plan_path,
        "plan_canonical_sha256": _canonical_json_sha256(plan),
        "prior_registry_evidence": deepcopy(
            plan["prior_registry_evidence"]
        ),
    }
    return candidate


def binding_authorization_payload(
    root: Path = ROOT,
    *,
    registry: dict[str, Any] | None = None,
    active_gate: str | None = None,
) -> dict[str, Any]:
    resolved_registry = (
        read_json(root / REGISTRY_PATH) if registry is None else registry
    )
    if active_gate is None:
        active_gate = resolved_registry.get("active_gate")
    if not isinstance(active_gate, str):
        raise ValueError("binding authorization active_gate must be a string")

    claims = resolved_registry.get("claims")
    if not isinstance(claims, dict):
        raise ValueError("binding authorization claims must be an object")
    declared = resolved_registry.get("declared_surfaces")
    if not isinstance(declared, list):
        raise ValueError(
            "binding authorization declared_surfaces must be an array"
        )
    retained_surface_records: list[dict[str, str]] = []
    for item in declared:
        if not isinstance(item, dict):
            raise ValueError(
                "binding authorization surface entry must be an object"
            )
        path = item.get("path")
        digest = item.get("sha256")
        if not isinstance(path, str) or not isinstance(digest, str):
            raise ValueError(
                "binding authorization surface path/digest must be strings"
            )
        retained_surface_records.append({"path": path, "sha256": digest})
    live_surface_records: list[dict[str, str]] = []
    for path in declared_surface_paths(root):
        canonical = _canonical_source_path(path)
        if canonical is None:
            raise ValueError(
                f"binding authorization surface path is unsafe: {path!r}"
            )
        absolute, failure = _regular_repository_file(root, canonical)
        if failure is not None or absolute is None:
            raise ValueError(
                f"binding authorization surface is unsafe or missing: {failure}"
            )
        live_surface_records.append({"path": path, "sha256": sha256(absolute)})

    bindings = resolved_registry.get("bindings")
    if not isinstance(bindings, list):
        raise ValueError("binding authorization bindings must be an array")
    records: list[dict[str, Any]] = []
    for binding in bindings:
        if not isinstance(binding, dict):
            raise ValueError(
                "binding authorization binding entry must be an object"
            )
        atom = binding.get("atom")
        resolution = binding.get("resolution")
        if not isinstance(atom, dict) or not isinstance(resolution, dict):
            raise ValueError(
                "binding authorization atom/resolution must be objects"
            )
        claim_kind = None
        if resolution.get("type") == "claim_projection":
            claim_id = resolution.get("claim_id")
            claim = claims.get(claim_id) if isinstance(claim_id, str) else None
            if not isinstance(claim, dict):
                raise ValueError(
                    "binding authorization projection references an "
                    "unknown or malformed claim"
                )
            claim_kind = claim.get("kind")
            if not isinstance(claim_kind, str):
                raise ValueError(
                    "binding authorization claim kind must be a string"
                )
        records.append(
            {
                "binding_id": binding.get("binding_id"),
                "path": binding.get("path"),
                "locator": binding.get("locator"),
                "structural_anchor_sha256": binding.get(
                    "structural_anchor_sha256"
                ),
                "segment_ordinal": binding.get("segment_ordinal"),
                "atom_ordinal": binding.get("atom_ordinal"),
                "normalized_atom": atom.get("normalized"),
                "role": binding.get("role"),
                "resolution": resolution,
                "claim_kind": claim_kind,
            }
        )
    return {
        "schema_version": BINDING_AUTHORIZATION_SCHEMA_VERSION,
        "active_gate": active_gate,
        "registry_transition": {
            "schema_version": resolved_registry.get("schema_version"),
            "revision": resolved_registry.get("revision"),
            "coverage_report_path": resolved_registry.get(
                "coverage_report_path"
            ),
            "non_claim_categories": resolved_registry.get(
                "non_claim_categories"
            ),
            "claim_kinds": resolved_registry.get("claim_kinds"),
            "migration": resolved_registry.get("migration"),
        },
        "declared_surfaces": retained_surface_records,
        "live_surfaces": live_surface_records,
        "claims": {
            claim_id: claims[claim_id]
            for claim_id in sorted(claims)
        },
        "bindings": records,
    }


def binding_authorization_sha256(
    root: Path = ROOT,
    *,
    registry: dict[str, Any] | None = None,
    active_gate: str | None = None,
) -> str:
    payload = binding_authorization_payload(
        root,
        registry=registry,
        active_gate=active_gate,
    )
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _binding_authority_failures(
    root: Path,
    *,
    registry: dict[str, Any],
    active_gate: Any,
) -> tuple[list[str], str | None]:
    if not isinstance(active_gate, str):
        return ["binding authorization active gate is not a string"], None
    expected = AUTHORIZED_BINDING_INVENTORY_SHA256.get(active_gate)
    if expected is None:
        return [
            f"no reviewed binding authorization for active gate {active_gate!r}"
        ], None
    try:
        actual = binding_authorization_sha256(
            root,
            registry=registry,
            active_gate=active_gate,
        )
    except (OSError, TypeError, ValueError) as exc:
        return [f"cannot derive binding authorization: {exc}"], None
    if actual != expected:
        return [
            "live quantitative binding authorization digest differs: "
            f"expected={expected} actual={actual}"
        ], actual
    return [], actual


def report_path_for_gate(active_gate: str) -> str:
    if not isinstance(active_gate, str):
        raise ValueError(f"active gate is not a string: {active_gate!r}")
    gate = PurePosixPath(active_gate)
    if (
        gate.is_absolute()
        or _has_control_characters(active_gate)
        or "\\" in active_gate
        or gate.name != "HYPOTHESIS.md"
        or len(gate.parts) != 3
        or gate.parts[0] != "experiments"
        or re.fullmatch(
            r"iter\d+_[a-z0-9]+(?:_[a-z0-9]+)*",
            gate.parts[1],
        )
        is None
        or any(part in {"", ".", ".."} for part in gate.parts)
        or gate.as_posix() != active_gate
    ):
        raise ValueError(f"active gate is not a canonical experiment hypothesis: {active_gate}")
    return (gate.parent / "proof" / REPORT_NAME).as_posix()


def bootstrap_registry(
    root: Path = ROOT,
    *,
    internal_claims: dict[str, dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Build the one-time review candidate for a repository without a registry.

    Once ``mission/claim_registry.json`` exists, its stable claim IDs and
    reviewed resolutions are authority.  This initializer therefore refuses
    overwrite instead of treating current prose as permission to mint claims.
    """

    if (root / REGISTRY_PATH).exists():
        raise ValueError(
            "initial claim bootstrap refused: claim registry already exists"
        )

    current = read_json(root / "mission/current.json")
    active_gate = current["active_gate"]
    atom_bindings = extract_all_bindings(root)
    retained_claim_ids = _initial_retained_claim_ids(atom_bindings)

    claims: dict[str, dict[str, Any]]
    if internal_claims is not None:
        claims = deepcopy(internal_claims)
    elif root.resolve() == ROOT.resolve():
        claims = deepcopy(builder.build_internal_claims())
    else:
        claims = {}
    claims.update(build_curated_lineage_claims(root))
    bindings: list[dict[str, Any]] = []
    seen_curated: set[str] = set()
    seen_lineage: set[str] = set()
    for atom_binding in atom_bindings:
        binding_record, retained = _binding_record(
            root,
            atom_binding,
            retained_claim_ids=retained_claim_ids,
        )
        bindings.append(binding_record)
        resolution = binding_record["resolution"]
        if atom_binding.binding_id in CURATED_INTERNAL_PROJECTIONS:
            seen_curated.add(atom_binding.binding_id)
        if atom_binding.binding_id in CURATED_LINEAGE_PROJECTIONS:
            seen_lineage.add(atom_binding.binding_id)
        if retained is not None:
            claims[retained["claim_id"]] = retained
        elif resolution["type"] == "claim_projection":
            claim_id = resolution["claim_id"]
            if claim_id in claims:
                claims[claim_id]["surface_binding_ids"].append(
                    atom_binding.binding_id
                )
    missing_curated = set(CURATED_INTERNAL_PROJECTIONS) - seen_curated
    if missing_curated:
        raise ValueError(
            "curated bindings absent from current surfaces: "
            + ", ".join(sorted(missing_curated))
        )
    missing_lineage = set(CURATED_LINEAGE_PROJECTIONS) - seen_lineage
    if missing_lineage:
        raise ValueError(
            "curated lineage bindings absent from current surfaces: "
            + ", ".join(sorted(missing_lineage))
        )
    for claim in claims.values():
        claim["surface_binding_ids"] = sorted(claim["surface_binding_ids"])

    surface_paths = declared_surface_paths(root)
    return {
        "schema_version": SCHEMA_VERSION,
        "revision": 2,
        "active_gate": active_gate,
        "coverage_report_path": report_path_for_gate(active_gate),
        "migration": None,
        "declared_surfaces": [
            {
                "path": path,
                "format": (
                    "json"
                    if path.endswith(".json")
                    else "latex"
                    if path.endswith(".tex")
                    else "markdown"
                ),
                "sha256": sha256(root / path),
            }
            for path in surface_paths
        ],
        "non_claim_categories": sorted(ALLOWED_NONCLAIM_CATEGORIES),
        "claim_kinds": sorted(ALLOWED_CLAIM_KINDS),
        "claims": {key: claims[key] for key in sorted(claims)},
        "bindings": sorted(bindings, key=lambda item: item["binding_id"]),
    }


def _json_pointer(document: Any, pointer: str) -> Any:
    if not isinstance(pointer, str) or not pointer.startswith("/"):
        raise ValueError(f"invalid JSON pointer: {pointer!r}")
    current = document
    for raw_part in pointer.split("/")[1:]:
        part = raw_part.replace("~1", "/").replace("~0", "~")
        if isinstance(current, dict):
            if part not in current:
                raise KeyError(pointer)
            current = current[part]
        elif isinstance(current, list):
            current = current[int(part)]
        else:
            raise KeyError(pointer)
    return current


def _atom_scalar(normalized: dict[str, Any]) -> Decimal | None:
    numeric_type = normalized.get("numeric_type")
    if numeric_type == "integer":
        value = normalized.get("value")
        return Decimal(value) if type(value) is int else None
    if numeric_type == "scalar":
        try:
            value = normalized.get("value")
            return Decimal(value) if isinstance(value, str) else None
        except (InvalidOperation, TypeError):
            return None
    return None


def _canonical_scalar(value: Any) -> Decimal | None:
    if type(value) is int or type(value) is float:
        try:
            return Decimal(str(value))
        except InvalidOperation:
            return None
    return None


def projection_matches(
    binding: AtomBinding,
    claim: dict[str, Any],
    projection: dict[str, Any],
) -> tuple[bool, str]:
    operator = projection.get("operator")
    if not isinstance(operator, str) or operator not in PROJECTION_OPERATORS:
        return False, f"unsupported projection operator {operator!r}"

    expected_currency = projection.get("currency")
    expected_percent = projection.get("percent")
    if type(expected_currency) is not bool or type(expected_percent) is not bool:
        return False, "projection currency/percent flags must be booleans"
    actual_currency = binding.atom.normalized.get("currency", False)
    actual_percent = binding.atom.normalized.get("percent", False)
    if (
        actual_currency is not expected_currency
        or actual_percent is not expected_percent
    ):
        return (
            False,
            "atom unit flags differ: "
            f"currency={actual_currency!r}/{expected_currency!r} "
            f"percent={actual_percent!r}/{expected_percent!r}",
        )
    try:
        if operator == "equals":
            if set(projection) != {
                "operator",
                "pointer",
                "currency",
                "percent",
            }:
                return False, "equals projection fields differ"
            expected = _json_pointer(claim, projection["pointer"])
            if isinstance(expected, dict) and "numeric_type" in expected:
                return (
                    binding.atom.normalized == expected,
                    f"atom={binding.atom.normalized!r} pointer={expected!r}",
                )
            actual_scalar = _atom_scalar(binding.atom.normalized)
            expected_scalar = _canonical_scalar(expected)
            return (
                actual_scalar is not None and actual_scalar == expected_scalar,
                f"atom={actual_scalar!r} pointer={expected_scalar!r}",
            )
        if operator == "ratio":
            if set(projection) != {
                "operator",
                "numerator_pointer",
                "denominator_pointer",
                "currency",
                "percent",
            }:
                return False, "ratio projection fields differ"
            normalized = binding.atom.normalized
            if normalized.get("numeric_type") != "ratio":
                return False, f"atom is not a ratio: {normalized!r}"
            numerator = _canonical_scalar(
                _json_pointer(claim, projection["numerator_pointer"])
            )
            denominator = _canonical_scalar(
                _json_pointer(claim, projection["denominator_pointer"])
            )
            actual_numerator = Decimal(normalized["numerator"])
            actual_denominator = Decimal(normalized["denominator"])
            return (
                actual_numerator == numerator and actual_denominator == denominator,
                (
                    f"atom={actual_numerator}/{actual_denominator} "
                    f"pointer={numerator}/{denominator}"
                ),
            )
        if set(projection) != {
            "operator",
            "pointer",
            "decimal_places",
            "currency",
            "percent",
        }:
            return False, "rounded_decimal projection fields differ"
        places = projection["decimal_places"]
        if type(places) is not int or places < 0 or places > 18:
            return False, "rounded_decimal decimal_places invalid"
        actual = _atom_scalar(binding.atom.normalized)
        expected = _canonical_scalar(_json_pointer(claim, projection["pointer"]))
        if actual is None or expected is None:
            return False, "rounded_decimal requires numeric scalars"
        quantum = Decimal(1).scaleb(-places)
        return (
            actual == expected.quantize(quantum),
            f"atom={actual!r} rounded_pointer={expected.quantize(quantum)!r}",
        )
    except (IndexError, KeyError, TypeError, ValueError, InvalidOperation) as exc:
        return False, f"projection cannot resolve: {exc}"


def _validate_claim_matrix(
    claim_id: str,
    claim: dict[str, Any],
    failures: list[str],
) -> None:
    kind = claim.get("kind")
    status = claim.get("status")
    missingness = claim.get("missingness")
    derivation = claim.get("derivation")
    if not isinstance(missingness, dict) or not missingness:
        failures.append(f"claim {claim_id} has empty missingness")
        missingness = {}
    if not isinstance(missingness.get("reason"), str) or not (
        missingness.get("reason", "").strip()
    ):
        failures.append(f"claim {claim_id} missingness lacks a non-empty reason")
    surface_ids = claim.get("surface_binding_ids")
    missingness_binding = missingness.get("binding_id")
    if missingness_binding is not None and (
        not isinstance(surface_ids, list)
        or missingness_binding not in surface_ids
    ):
        failures.append(
            f"claim {claim_id} missingness binding is outside its surface bindings"
        )
    if not isinstance(derivation, dict):
        failures.append(f"claim {claim_id} derivation is not an object")
        return
    if not isinstance(derivation.get("argv"), list):
        failures.append(f"claim {claim_id} derivation argv is not an array")
    is_retained_predecessor = isinstance(claim.get("superseded_by"), str)
    if kind == "internally_regenerated_empirical":
        allowed_internal_statuses = (
            {"corrected", "retracted"}
            if is_retained_predecessor
            else ALLOWED_INTERNAL_STATUSES
        )
        if not isinstance(status, str) or status not in allowed_internal_statuses:
            failures.append(f"claim {claim_id} internal status is not allowed")
        if derivation.get("mode") != "validated_predecessor_projection":
            failures.append(f"claim {claim_id} internal derivation mode differs")
        if not derivation.get("argv"):
            failures.append(f"claim {claim_id} internal derivation argv is empty")
        if derivation.get("predecessor_validator_argv") != (
            builder.PREDECESSOR_VALIDATOR_ARGV
        ):
            failures.append(
                f"claim {claim_id} predecessor validator argv differs"
            )
        if not isinstance(derivation.get("dependency_contract"), str) or not (
            derivation["dependency_contract"].strip()
        ):
            failures.append(
                f"claim {claim_id} predecessor dependency contract is empty"
            )
        return
    policy = RETAINED_POLICY.get(kind) if isinstance(kind, str) else None
    if policy is None:
        failures.append(f"claim {claim_id} has unsupported kind {kind!r}")
        return
    allowed_statuses = (
        {"corrected", "retracted"}
        if is_retained_predecessor
        else {
            "historical"
            if kind == "historical_empirical"
            else policy.get("status")
        }
    )
    if not isinstance(status, str) or status not in allowed_statuses:
        failures.append(
            f"claim {claim_id} in-place status promotion or drift: "
            f"expected={sorted(allowed_statuses)!r} actual={status!r}"
        )
    if derivation.get("mode") != policy["derivation_mode"]:
        failures.append(f"claim {claim_id} derivation-mode matrix violation")
    if derivation.get("argv") != []:
        failures.append(f"claim {claim_id} retained derivation argv must be empty")
    if (
        not is_retained_predecessor
        and isinstance(surface_ids, list)
        and len(surface_ids) == 1
        and missingness_binding != surface_ids[0]
    ):
        failures.append(
            f"claim {claim_id} retained missingness binding differs"
        )
    if kind in {"external_citation", "historical_empirical"} and not (
        is_retained_predecessor
    ):
        value = claim.get("value")
        if (
            not isinstance(value, dict)
            or value.get("semantic_metadata_resolution")
            != UNRESOLVED_RETAINED_SEMANTIC_STATE
            or claim.get("unit") != UNRESOLVED_RETAINED_UNIT
            or claim.get("cohort") != UNRESOLVED_RETAINED_COHORT
            or claim.get("independence_boundary")
            != UNRESOLVED_RETAINED_INDEPENDENCE
            or claim.get("excluded_inferences")
            != UNRESOLVED_RETAINED_EXCLUSIONS
        ):
            failures.append(
                f"claim {claim_id} unresolved retained semantic contract differs"
            )
    missingness_mode = missingness.get("mode")
    if (
        not isinstance(missingness_mode, str)
        or missingness_mode not in policy["missingness_modes"]
    ):
        failures.append(f"claim {claim_id} missingness-mode matrix violation")


def _validate_claim_schema(
    claim_id: str,
    claim: Any,
    failures: list[str],
) -> None:
    if not isinstance(claim, dict):
        failures.append(f"claim {claim_id} is not an object")
        return
    required = {
        "claim_id",
        "revision",
        "status",
        "kind",
        "unit",
        "cohort",
        "independence_boundary",
        "value",
        "missingness",
        "excluded_inferences",
        "derivation",
        "sources",
        "surface_binding_ids",
        "supersedes",
        "superseded_by",
    }
    if set(claim) != required:
        failures.append(
            f"claim {claim_id} fields differ: "
            f"missing={sorted(required - set(claim))} "
            f"extra={sorted(set(claim) - required)}"
        )
        return
    if claim.get("claim_id") != claim_id:
        failures.append(f"claim map key/id mismatch for {claim_id}")
    if type(claim.get("revision")) is not int or claim["revision"] < 1:
        failures.append(f"claim {claim_id} revision must be a positive integer")
    claim_kind = claim.get("kind")
    if (
        not isinstance(claim_kind, str)
        or claim_kind not in ALLOWED_CLAIM_KINDS
    ):
        failures.append(f"claim {claim_id} has unsupported kind")
    for field in ("unit", "cohort", "independence_boundary"):
        if not isinstance(claim.get(field), str) or not claim[field].strip():
            failures.append(f"claim {claim_id} {field} must be non-empty")
    excluded = claim.get("excluded_inferences")
    if not isinstance(excluded, list) or not excluded or any(
        not isinstance(item, str) or not item.strip() for item in excluded
    ):
        failures.append(f"claim {claim_id} excluded_inferences must be non-empty")
    surface_ids = claim.get("surface_binding_ids")
    valid_surface_ids = (
        isinstance(surface_ids, list)
        and all(
            isinstance(binding_id, str) and bool(binding_id)
            for binding_id in surface_ids
        )
        and len(surface_ids) == len(set(surface_ids))
    )
    if not valid_surface_ids:
        failures.append(
            f"claim {claim_id} surface bindings must be unique strings"
        )
    supersedes = claim.get("supersedes")
    valid_supersedes = (
        isinstance(supersedes, list)
        and all(
            isinstance(predecessor, str) and bool(predecessor)
            for predecessor in supersedes
        )
        and len(supersedes) == len(set(supersedes))
    )
    if not valid_supersedes:
        failures.append(
            f"claim {claim_id} supersedes must be unique strings"
        )
    successor = claim.get("superseded_by")
    if successor is not None and (
        not isinstance(successor, str) or not successor
    ):
        failures.append(
            f"claim {claim_id} superseded_by must be null or a string"
        )
    _validate_claim_matrix(claim_id, claim, failures)


def _supersession_failures(
    claims: dict[str, Any],
    *,
    verified_material_predecessor_ids: frozenset[str] = frozenset(),
) -> list[str]:
    failures: list[str] = []
    graph: dict[str, list[str]] = {}
    for claim_id, claim in claims.items():
        if not isinstance(claim, dict):
            continue
        supersedes = claim.get("supersedes", [])
        if not isinstance(supersedes, list):
            continue
        graph[claim_id] = [
            predecessor
            for predecessor in supersedes
            if isinstance(predecessor, str)
        ]
        for predecessor in graph[claim_id]:
            if predecessor not in claims:
                failures.append(
                    f"claim {claim_id} supersedes unknown claim {predecessor}"
                )
            elif not isinstance(claims[predecessor], dict):
                failures.append(
                    f"claim {claim_id} supersession target "
                    f"{predecessor} is not an object"
                )
            elif claims[predecessor].get("superseded_by") != claim_id:
                failures.append(
                    f"claim {claim_id}/{predecessor} supersession is not reciprocal"
                )
        successor = claim.get("superseded_by")
        if isinstance(successor, str):
            if successor not in claims:
                failures.append(
                    f"claim {claim_id} has unknown successor {successor}"
                )
            elif not isinstance(claims[successor], dict):
                failures.append(
                    f"claim {claim_id} successor {successor} is not an object"
                )
            else:
                successor_predecessors = claims[successor].get("supersedes")
                if (
                    not isinstance(successor_predecessors, list)
                    or claim_id not in successor_predecessors
                ):
                    failures.append(
                        f"claim {claim_id}/{successor} supersession "
                        "is not reciprocal"
                    )

    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(claim_id: str) -> None:
        if claim_id in visiting:
            failures.append(f"claim supersession cycle includes {claim_id}")
            return
        if claim_id in visited:
            return
        visiting.add(claim_id)
        for predecessor in graph.get(claim_id, []):
            visit(predecessor)
        visiting.remove(claim_id)
        visited.add(claim_id)

    for claim_id in graph:
        visit(claim_id)

    # Every material-correction component has one authoritative head.  Older
    # corrected claims may remain visibly cited in corrective context, but
    # they must carry immutable evidence and cannot become a second live head.
    undirected: defaultdict[str, set[str]] = defaultdict(set)
    lineage_nodes: set[str] = set()
    for successor, predecessors in graph.items():
        for predecessor in predecessors:
            if predecessor not in claims:
                continue
            lineage_nodes.update({successor, predecessor})
            undirected[successor].add(predecessor)
            undirected[predecessor].add(successor)
    seen_components: set[str] = set()
    for seed in sorted(lineage_nodes):
        if seed in seen_components:
            continue
        component: set[str] = set()
        pending = [seed]
        while pending:
            current = pending.pop()
            if current in component:
                continue
            component.add(current)
            pending.extend(undirected[current] - component)
        seen_components.update(component)
        heads = [
            claim_id
            for claim_id in component
            if isinstance(claims.get(claim_id), dict)
            and claims[claim_id].get("superseded_by") is None
        ]
        if len(heads) != 1:
            failures.append(
                "claim supersession component must have exactly one head: "
                f"component={sorted(component)} heads={sorted(heads)}"
            )
            continue
        head = heads[0]
        head_claim = claims[head]
        head_bindings = head_claim.get("surface_binding_ids")
        if (
            not isinstance(head_bindings, list)
            or not head_bindings
        ):
            if (
                head_claim.get("status") != "retracted"
                or head not in AUTHORIZED_UNBOUND_RETRACTED_HEADS
            ):
                failures.append(
                    "claim supersession head is unbound without explicit "
                    f"retraction authority: {head}"
                )

        reachable: set[str] = set()
        stack = [head]
        while stack:
            current = stack.pop()
            if current in reachable:
                continue
            reachable.add(current)
            current_claim = claims.get(current)
            predecessors = (
                current_claim.get("supersedes", [])
                if isinstance(current_claim, dict)
                else []
            )
            if isinstance(predecessors, list):
                stack.extend(
                    predecessor
                    for predecessor in predecessors
                    if isinstance(predecessor, str)
                )
        if reachable != component:
            failures.append(
                "claim supersession component has unreachable lineage: "
                f"head={head} unreachable={sorted(component - reachable)}"
            )

        for claim_id in component - {head}:
            claim = claims.get(claim_id)
            if not isinstance(claim, dict):
                continue
            status = claim.get("status")
            if (
                not isinstance(status, str)
                or status not in {"corrected", "retracted"}
            ):
                failures.append(
                    f"superseded claim {claim_id} must be corrected or retracted"
                )
            sources = claim.get("sources")
            has_immutable_evidence = isinstance(sources, list) and any(
                isinstance(source, dict)
                and source.get("classification") == "sealed"
                and isinstance(source.get("seal_ids"), list)
                and bool(source["seal_ids"])
                for source in sources
            )
            if (
                not has_immutable_evidence
                and claim_id not in verified_material_predecessor_ids
            ):
                failures.append(
                    f"superseded claim {claim_id} lacks immutable sealed evidence"
                )

    # A claim with no public binding is dead unless a live/retracted lineage
    # head reaches it.
    for claim_id, claim in claims.items():
        if not isinstance(claim, dict):
            continue
        surface_ids = claim.get("surface_binding_ids")
        if (
            isinstance(surface_ids, list)
            and not surface_ids
            and claim_id not in lineage_nodes
        ):
            failures.append(
                f"unbound claim is not reachable from a lineage head: {claim_id}"
            )
        if (
            isinstance(claim.get("status"), str)
            and claim.get("status") in {"corrected", "retracted"}
            and claim_id not in lineage_nodes
        ):
            failures.append(
                f"corrected/retracted claim lacks material-change lineage: {claim_id}"
            )
    return failures


def _git_blob_sha256(root: Path, commit: str, path: str) -> str | None:
    result = subprocess.run(
        ["git", "show", f"{commit}:{path}"],
        cwd=root,
        check=False,
        capture_output=True,
    )
    if result.returncode != 0:
        return None
    return hashlib.sha256(result.stdout).hexdigest()


def _seal_membership(
    root: Path,
    seal_registry: dict[str, Any],
    seal_id: str,
    path: str,
) -> tuple[bool, str]:
    raw_records = seal_registry.get("records")
    if not isinstance(raw_records, list):
        return False, "seal registry records is not an array"
    if any(not isinstance(record, dict) for record in raw_records):
        return False, "seal registry contains a non-object record"
    records = [
        record
        for record in raw_records
        if record.get("seal_id") == seal_id
    ]
    if len(records) != 1:
        return False, f"seal ID {seal_id!r} is not unique"
    record = records[0]
    record_type = record.get("record_type")
    if record_type not in {
        "retrospective_path_snapshot",
        "successor_path_snapshot",
    }:
        return False, f"seal {seal_id!r} does not expose protected path membership"
    reference = record.get("reference_commit")
    if not isinstance(reference, str):
        return False, f"seal {seal_id!r} lacks reference_commit"
    protected_sets = record.get("protected_sets")
    if not isinstance(protected_sets, list):
        return False, f"seal {seal_id!r} protected_sets is not an array"
    if any(not isinstance(protected_set, dict) for protected_set in protected_sets):
        return False, f"seal {seal_id!r} contains a non-object protected set"
    selected = False
    for protected_set in protected_sets:
        selector = protected_set.get("selector")
        if not isinstance(selector, dict):
            return False, f"seal {seal_id!r} has a malformed selector"
        if selector.get("kind") == "tree":
            tree = selector.get("path")
            if not isinstance(tree, str):
                return False, f"seal {seal_id!r} tree selector path is invalid"
            if path == tree or path.startswith(f"{tree}/"):
                selected = True
        elif (
            record_type == "retrospective_path_snapshot"
            and selector.get("kind") == "path_list"
        ):
            paths = selector.get("paths")
            if not isinstance(paths, list) or any(
                not isinstance(item, str) for item in paths
            ):
                return False, f"seal {seal_id!r} path-list selector is invalid"
            if path in paths:
                selected = True
        else:
            return False, f"seal {seal_id!r} selector kind is invalid"
    if not selected:
        return False, f"path {path!r} is outside seal {seal_id!r} selectors"
    blob_digest = _git_blob_sha256(root, reference, path)
    if blob_digest is None:
        return (
            False,
            f"path {path!r} is not a Git blob at seal reference {reference}",
        )
    return True, blob_digest


def _canonical_source_path(path: str) -> PurePosixPath | None:
    candidate = PurePosixPath(path)
    if (
        not path
        or _has_control_characters(path)
        or "\\" in path
        or candidate.is_absolute()
        or candidate.as_posix() != path
        or candidate.as_posix() == "."
        or any(part in {"", ".", ".."} for part in candidate.parts)
    ):
        return None
    return candidate


def _regular_repository_file(
    root: Path,
    relative: PurePosixPath,
) -> tuple[Path | None, str | None]:
    current = root
    for index, part in enumerate(relative.parts):
        current = current / part
        try:
            metadata = current.lstat()
        except OSError as exc:
            return None, f"{relative.as_posix()}: {exc}"
        if stat.S_ISLNK(metadata.st_mode):
            return None, f"{relative.as_posix()}: symlink component {part!r}"
        terminal = index == len(relative.parts) - 1
        if terminal:
            if not stat.S_ISREG(metadata.st_mode):
                return None, f"{relative.as_posix()}: terminal path is not a file"
        elif not stat.S_ISDIR(metadata.st_mode):
            return None, f"{relative.as_posix()}: parent component is not a directory"
    return current, None


def _validate_sources(
    root: Path,
    claims: dict[str, Any],
    failures: list[str],
    *,
    check_source_digests: bool,
    check_seals: bool,
    actual_bindings_by_id: dict[str, AtomBinding] | None = None,
) -> None:
    segment_digest_cache: dict[str, dict[str, str]] = {}
    git_segment_digest_cache: dict[tuple[str, str], dict[str, str]] = {}

    def segment_digests(path: str) -> dict[str, str]:
        cached = segment_digest_cache.get(path)
        if cached is not None:
            return cached
        built: dict[str, str] = {}
        for segment in extract_segments(root, path):
            digest = hashlib.sha256(segment.text.encode("utf-8")).hexdigest()
            for atom_ordinal, _ in enumerate(segment.atoms):
                binding_id = (
                    f"{path}:{segment.anchor_sha256[:20]}:"
                    f"{segment.segment_ordinal}:{atom_ordinal}"
                )
                built[binding_id] = digest
        segment_digest_cache[path] = built
        return built

    def git_segment_digests(commit: str, path: str) -> dict[str, str]:
        cache_key = (commit, path)
        cached = git_segment_digest_cache.get(cache_key)
        if cached is not None:
            return cached
        blob = _git_blob_bytes(root, commit, path)
        if path.endswith(".json"):
            value = json.loads(
                blob.decode("utf-8"),
                object_pairs_hook=_object_no_duplicates,
                parse_constant=_reject_json_constant,
            )
            pieces = list(_json_leaf_segments(value))
        else:
            pieces = _split_text_segments(path, blob.decode("utf-8"))
        duplicate_count: defaultdict[str, int] = defaultdict(int)
        built: dict[str, str] = {}
        for locator, text in pieces:
            atoms = quantitative_atoms(text)
            if not atoms:
                continue
            skeleton = _skeleton(text, atoms)
            seed = (
                f"{path}\0{normalize_space(locator)}\0{skeleton}"
            )
            anchor = hashlib.sha256(seed.encode("utf-8")).hexdigest()
            ordinal = duplicate_count[anchor]
            duplicate_count[anchor] += 1
            digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
            for atom_ordinal, _ in enumerate(atoms):
                binding_id = (
                    f"{path}:{anchor[:20]}:{ordinal}:{atom_ordinal}"
                )
                built[binding_id] = digest
        git_segment_digest_cache[cache_key] = built
        return built

    try:
        seal_registry = read_json(root / SEAL_REGISTRY_PATH)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        if check_seals:
            failures.append(f"seal registry unreadable for claim attribution: {exc}")
        seal_registry = {}
    for claim_id, claim in claims.items():
        if not isinstance(claim, dict):
            continue
        sources = claim.get("sources")
        if not isinstance(sources, list) or not sources:
            failures.append(f"claim {claim_id} must record at least one source")
            continue
        mutable_segment_source_ids: list[str] = []
        for source in sources:
            if not isinstance(source, dict):
                failures.append(f"claim {claim_id} source is not an object")
                continue
            file_source_fields = {
                "path",
                "sha256",
                "classification",
                "seal_ids",
            }
            segment_source_fields = {
                *file_source_fields,
                "digest_scope",
                "binding_id",
            }
            git_file_source_fields = {
                *file_source_fields,
                "digest_scope",
                "reference_commit",
            }
            git_segment_source_fields = {
                *git_file_source_fields,
                "binding_id",
            }
            if frozenset(source) not in {
                frozenset(file_source_fields),
                frozenset(segment_source_fields),
                frozenset(git_file_source_fields),
                frozenset(git_segment_source_fields),
            }:
                failures.append(f"claim {claim_id} source fields differ")
                continue
            path = source.get("path")
            classification = source.get("classification")
            seal_ids = source.get("seal_ids")
            digest = source.get("sha256")
            digest_scope = source.get("digest_scope", "file_bytes")
            binding_id = source.get("binding_id")
            reference_commit = source.get("reference_commit")
            if not isinstance(digest_scope, str):
                failures.append(
                    f"claim {claim_id} source digest_scope is not a string"
                )
                digest_scope = ""
            if not isinstance(path, str):
                failures.append(f"claim {claim_id} source path is invalid")
                continue
            canonical_path = _canonical_source_path(path)
            if canonical_path is None:
                failures.append(
                    f"claim {claim_id} source path is not canonical "
                    f"repository-relative POSIX: {path!r}"
                )
            if (
                not isinstance(classification, str)
                or classification not in {
                    "historical_git_blob",
                    "mutable",
                    "sealed",
                }
            ):
                failures.append(f"claim {claim_id} source classification invalid")
            if not isinstance(digest, str) or SHA256_RE.fullmatch(digest) is None:
                failures.append(f"claim {claim_id} source sha256 is invalid")
            valid_seal_ids = (
                isinstance(seal_ids, list)
                and all(
                    isinstance(seal_id, str) and bool(seal_id)
                    for seal_id in seal_ids
                )
                and len(seal_ids) == len(set(seal_ids))
            )
            if not valid_seal_ids:
                failures.append(f"claim {claim_id} source seal_ids invalid")
                seal_ids = []
            if classification == "mutable" and seal_ids:
                failures.append(f"claim {claim_id} mutable source has seal IDs")
            if classification == "sealed" and not seal_ids:
                failures.append(f"claim {claim_id} sealed source lacks a seal ID")
            if classification == "historical_git_blob" and seal_ids:
                failures.append(
                    f"claim {claim_id} historical Git source has seal IDs"
                )
            if digest_scope == "normalized_surface_segment_utf8":
                if isinstance(binding_id, str):
                    mutable_segment_source_ids.append(binding_id)
                if (
                    classification != "mutable"
                    or seal_ids
                    or not isinstance(binding_id, str)
                ):
                    failures.append(
                        f"claim {claim_id} segment source metadata invalid"
                    )
                if check_source_digests and canonical_path is not None:
                    try:
                        if actual_bindings_by_id is not None:
                            live_binding = (
                                actual_bindings_by_id.get(binding_id)
                                if isinstance(binding_id, str)
                                else None
                            )
                            segment_digest = (
                                hashlib.sha256(
                                    live_binding.segment.text.encode("utf-8")
                                ).hexdigest()
                                if live_binding is not None
                                and live_binding.segment.path == path
                                else None
                            )
                        else:
                            segment_digest = segment_digests(path).get(binding_id)
                    except (OSError, json.JSONDecodeError, ValueError) as exc:
                        failures.append(
                            f"claim {claim_id} segment source cannot resolve: "
                            f"{exc}"
                        )
                        segment_digest = None
                    if segment_digest is None:
                        failures.append(
                            f"claim {claim_id} segment source binding is not "
                            f"unique/live: {binding_id}"
                        )
                    elif digest != segment_digest:
                        failures.append(
                            f"claim {claim_id} segment source digest drift: "
                            f"{binding_id}"
                        )
            elif digest_scope != "file_bytes":
                if digest_scope in {
                    "git_blob_at_commit",
                    "normalized_surface_segment_at_commit",
                }:
                    if (
                        classification != "historical_git_blob"
                        or not isinstance(reference_commit, str)
                        or re.fullmatch(
                            r"[0-9a-f]{40}",
                            reference_commit,
                        )
                        is None
                    ):
                        failures.append(
                            f"claim {claim_id} historical Git source metadata "
                            "invalid"
                        )
                    elif check_source_digests:
                        try:
                            if digest_scope == "git_blob_at_commit":
                                actual_git_digest = _git_blob_sha256(
                                    root,
                                    reference_commit,
                                    path,
                                )
                            elif not isinstance(binding_id, str):
                                actual_git_digest = None
                            else:
                                actual_git_digest = git_segment_digests(
                                    reference_commit,
                                    path,
                                ).get(binding_id)
                        except (
                            OSError,
                            UnicodeDecodeError,
                            json.JSONDecodeError,
                            ValueError,
                        ) as exc:
                            failures.append(
                                f"claim {claim_id} historical Git source "
                                f"cannot resolve: {exc}"
                            )
                            actual_git_digest = None
                        if actual_git_digest is None:
                            failures.append(
                                f"claim {claim_id} historical Git source is "
                                f"missing: {path}"
                            )
                        elif digest != actual_git_digest:
                            failures.append(
                                f"claim {claim_id} historical Git source "
                                f"digest drift: {path}"
                            )
                else:
                    failures.append(
                        f"claim {claim_id} source digest_scope is invalid"
                    )
            elif binding_id is not None:
                failures.append(
                    f"claim {claim_id} file source must not name a binding"
                )
            elif check_source_digests and canonical_path is not None:
                absolute, path_failure = _regular_repository_file(
                    root,
                    canonical_path,
                )
                if path_failure is not None:
                    failures.append(
                        f"claim {claim_id} source path is unsafe or missing: "
                        f"{path_failure}"
                    )
                elif absolute is not None and digest != sha256(absolute):
                    failures.append(f"claim {claim_id} source digest drift: {path}")
            if (
                check_seals
                and canonical_path is not None
                and digest_scope == "file_bytes"
            ):
                for seal_id in seal_ids:
                    member, detail = _seal_membership(
                        root,
                        seal_registry,
                        seal_id,
                        path,
                    )
                    if not member:
                        failures.append(
                            f"claim {claim_id} false seal attribution: {detail}"
                        )
                        continue
                    if source.get("sha256") != detail:
                        failures.append(
                            f"claim {claim_id} sealed source digest differs "
                            f"from {seal_id}: {path}"
                        )
        surface_ids = claim.get("surface_binding_ids")
        if (
            isinstance(claim.get("kind"), str)
            and claim.get("kind") in RETAINED_POLICY
            and isinstance(surface_ids, list)
            and surface_ids
            and all(isinstance(item, str) for item in surface_ids)
            and sorted(mutable_segment_source_ids) != sorted(surface_ids)
        ):
            failures.append(
                f"claim {claim_id} mutable segment sources do not exactly "
                "match its surface bindings"
            )


def _surface_format(path: str) -> str:
    if path.endswith(".json"):
        return "json"
    if path.endswith(".tex"):
        return "latex"
    return "markdown"


def _validate_declared_surfaces(
    root: Path,
    declared: list[Any],
    surface_paths: tuple[str, ...],
    failures: list[str],
) -> dict[str, str]:
    digests: dict[str, str] = {}
    declared_paths = [
        item.get("path") for item in declared if isinstance(item, dict)
    ]
    if declared_paths != list(surface_paths):
        failures.append("declared public surface inventory differs")

    for index, item in enumerate(declared):
        if not isinstance(item, dict):
            failures.append("declared surface entry is not an object")
            continue
        if set(item) != {"path", "format", "sha256"}:
            failures.append("declared surface fields differ")
        path = item.get("path")
        expected_path = (
            surface_paths[index] if index < len(surface_paths) else None
        )
        if not isinstance(path, str) or path != expected_path:
            failures.append(
                f"declared public surface path is not authorized at "
                f"index {index}: {path!r}"
            )
            continue
        canonical = _canonical_source_path(path)
        if canonical is None:
            failures.append(
                f"declared public surface path is not canonical: {path!r}"
            )
            continue
        expected_format = _surface_format(path)
        if item.get("format") != expected_format:
            failures.append(
                f"declared public surface format differs: {path}"
            )
        retained_digest = item.get("sha256")
        if (
            not isinstance(retained_digest, str)
            or SHA256_RE.fullmatch(retained_digest) is None
        ):
            failures.append(
                f"declared public surface sha256 is invalid: {path}"
            )
        absolute, path_failure = _regular_repository_file(root, canonical)
        if path_failure is not None:
            failures.append(
                f"declared public surface is unsafe or missing: {path_failure}"
            )
            continue
        if absolute is None:
            failures.append(f"declared public surface missing: {path}")
            continue
        actual_digest = sha256(absolute)
        digests[path] = actual_digest
        if retained_digest != actual_digest:
            failures.append(f"declared public surface digest drift: {path}")
    return digests


def _safe_output_destination(
    root: Path,
    relative_path: str,
) -> tuple[Path | None, str | None]:
    canonical = _canonical_source_path(relative_path)
    if canonical is None:
        return None, f"output path is not canonical: {relative_path!r}"
    destination = root.joinpath(*canonical.parts)
    current = root
    for part in canonical.parts[:-1]:
        current = current / part
        try:
            metadata = current.lstat()
        except OSError as exc:
            return None, f"output parent is missing: {current}: {exc}"
        if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISDIR(metadata.st_mode):
            return None, f"output parent is not a real directory: {current}"
    try:
        terminal = destination.lstat()
    except FileNotFoundError:
        terminal = None
    except OSError as exc:
        return None, f"cannot inspect output path {destination}: {exc}"
    if terminal is not None and (
        stat.S_ISLNK(terminal.st_mode) or not stat.S_ISREG(terminal.st_mode)
    ):
        return None, f"output path is not a real regular file: {destination}"
    return destination, None


def _report_seal_id(
    root: Path,
    report_path: str,
) -> str | None:
    try:
        seal_registry = read_json(root / SEAL_REGISTRY_PATH)
    except (OSError, json.JSONDecodeError, ValueError):
        return "unreadable-seal-registry"
    records = seal_registry.get("records")
    if not isinstance(records, list):
        return "invalid-seal-registry"
    for record in records:
        if not isinstance(record, dict):
            continue
        seal_id = record.get("seal_id")
        if not isinstance(seal_id, str):
            continue
        member, _ = _seal_membership(
            root,
            seal_registry,
            seal_id,
            report_path,
        )
        if member:
            return seal_id
    return None


def _preflight_bootstrap_outputs(
    root: Path,
    *,
    active_gate: str,
) -> tuple[list[str], Path | None, Path | None]:
    failures: list[str] = []
    try:
        report_relative = report_path_for_gate(active_gate)
    except ValueError as exc:
        return [f"bootstrap active gate is unsafe: {exc}"], None, None

    gate_file, gate_failure = _regular_repository_file(
        root,
        PurePosixPath(active_gate),
    )
    if gate_failure is not None or gate_file is None:
        failures.append(
            "active gate must be a materialized real hypothesis file: "
            f"{gate_failure}"
        )

    registry_path, registry_failure = _safe_output_destination(
        root,
        REGISTRY_PATH.as_posix(),
    )
    if registry_failure is not None:
        failures.append(registry_failure)
    report_path, report_failure = _safe_output_destination(
        root,
        report_relative,
    )
    if report_failure is not None:
        failures.append(report_failure)
    if registry_path is not None and registry_path.exists():
        failures.append(
            "initial claim bootstrap refused: claim registry already exists"
        )
    if report_path is not None and report_path.exists():
        failures.append(
            "initial claim bootstrap refused: active-gate report already exists"
        )

    seal_id = _report_seal_id(root, report_relative)
    if seal_id is not None:
        failures.append(
            f"refusing to rewrite sealed claim report {report_relative}: "
            f"{seal_id}"
        )
    return failures, registry_path, report_path


def _migration_assessment(
    root: Path,
    registry: dict[str, Any],
) -> tuple[list[str], frozenset[str]]:
    migration = registry.get("migration")
    if migration is None:
        return [], frozenset()
    required = {
        "schema_version",
        "plan_path",
        "plan_canonical_sha256",
        "prior_registry_evidence",
    }
    if not isinstance(migration, dict) or set(migration) != required:
        return ["claim registry migration metadata fields differ"], frozenset()
    if migration.get("schema_version") != MIGRATION_SCHEMA_VERSION:
        return ["claim registry migration metadata schema differs"], frozenset()
    plan_path = migration.get("plan_path")
    if not isinstance(plan_path, str):
        return ["claim registry migration plan path is not a string"], frozenset()
    canonical = _canonical_source_path(plan_path)
    if canonical is None:
        return ["claim registry migration plan path is unsafe"], frozenset()
    absolute, path_failure = _regular_repository_file(root, canonical)
    if path_failure is not None or absolute is None:
        return (
            [
                f"claim registry migration plan is unsafe or missing: "
                f"{path_failure}"
            ],
            frozenset(),
        )
    try:
        plan = read_json(absolute)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        return [f"claim registry migration plan is unreadable: {exc}"], frozenset()
    if _canonical_json_sha256(plan) != migration.get(
        "plan_canonical_sha256"
    ):
        return ["claim registry migration plan digest differs"], frozenset()
    if plan.get("prior_registry_evidence") != migration.get(
        "prior_registry_evidence"
    ):
        return [
            "claim registry migration prior evidence differs from plan"
        ], frozenset()
    try:
        prior = _prior_registry_from_evidence(
            root,
            migration["prior_registry_evidence"],
            expected_active_gate=plan.get("from_active_gate"),
        )
        expected = build_migration_candidate(
            root,
            prior,
            plan,
            require_current_prior=False,
        )
    except (OSError, TypeError, ValueError) as exc:
        return [f"claim registry migration cannot replay: {exc}"], frozenset()
    if _canonical_json_sha256(registry) != _canonical_json_sha256(expected):
        return ["claim registry migration replay differs exactly"], frozenset()

    verified: set[str] = set()
    prior_bindings = {
        binding.get("binding_id"): binding
        for binding in prior.get("bindings", [])
        if isinstance(binding, dict)
        and isinstance(binding.get("binding_id"), str)
    }
    claims = registry.get("claims")
    material_updates = plan.get("material_binding_updates")
    evidence = plan.get("prior_registry_evidence")
    evidence_commit = evidence.get("commit") if isinstance(evidence, dict) else None
    if not isinstance(claims, dict) or not isinstance(material_updates, list):
        return ["claim registry migration replay structure differs"], frozenset()
    try:
        inherited_verified = _prior_report_verified_predecessor_ids(
            root,
            migration["prior_registry_evidence"],
        )
    except (
        KeyError,
        OSError,
        TypeError,
        json.JSONDecodeError,
        ValueError,
    ) as exc:
        return [
            f"claim registry prior verified predecessor set is unreadable: {exc}"
        ], frozenset()
    prior_claims = prior.get("claims")
    if not isinstance(prior_claims, dict):
        return ["claim registry prior claims are malformed"], frozenset()
    for update in material_updates:
        if not isinstance(update, dict):
            continue
        binding_id = update.get("binding_id")
        prior_binding = (
            prior_bindings.get(binding_id)
            if isinstance(binding_id, str)
            else None
        )
        prior_resolution = (
            prior_binding.get("resolution")
            if isinstance(prior_binding, dict)
            else None
        )
        old_claim_id = (
            prior_resolution.get("claim_id")
            if isinstance(prior_resolution, dict)
            and prior_resolution.get("type") == "claim_projection"
            else None
        )
        if not isinstance(old_claim_id, str):
            continue
        predecessor = claims.get(old_claim_id)
        sources = (
            predecessor.get("sources")
            if isinstance(predecessor, dict)
            else None
        )
        if not isinstance(evidence_commit, str):
            return [
                "claim registry material predecessor evidence differs: "
                f"{old_claim_id}"
            ], frozenset()
        try:
            exact_historical = _prior_binding_historical_source(
                root,
                prior,
                prior_binding,
                evidence_commit,
            )
        except (OSError, TypeError, ValueError) as exc:
            return [
                "claim registry material predecessor prior source differs: "
                f"{old_claim_id}: {exc}"
            ], frozenset()
        if not isinstance(sources, list) or exact_historical not in sources:
            return [
                "claim registry material predecessor historical source differs: "
                f"{old_claim_id}"
            ], frozenset()
        verified.add(old_claim_id)
    for claim_id in sorted(inherited_verified):
        prior_predecessor = prior_claims.get(claim_id)
        current_predecessor = claims.get(claim_id)
        successor_id = (
            prior_predecessor.get("superseded_by")
            if isinstance(prior_predecessor, dict)
            else None
        )
        prior_successor = (
            prior_claims.get(successor_id)
            if isinstance(successor_id, str)
            else None
        )
        current_successor = (
            claims.get(successor_id)
            if isinstance(successor_id, str)
            else None
        )
        if (
            not isinstance(prior_predecessor, dict)
            or current_predecessor != prior_predecessor
            or not isinstance(prior_successor, dict)
            or not isinstance(current_successor, dict)
            or claim_id not in prior_successor.get("supersedes", [])
            or claim_id not in current_successor.get("supersedes", [])
        ):
            return [
                "claim registry inherited verified predecessor/lineage "
                f"drifted: {claim_id}"
            ], frozenset()
        verified.add(claim_id)
    return [], frozenset(verified)


def _migration_failures(
    root: Path,
    registry: dict[str, Any],
) -> list[str]:
    failures, _ = _migration_assessment(root, registry)
    return failures


def validate(
    *,
    root: Path = ROOT,
    registry_relative: Path = REGISTRY_PATH,
    check_internal: bool = True,
    check_source_digests: bool = True,
    check_seals: bool = True,
    check_report: bool = True,
) -> tuple[list[str], dict[str, Any]]:
    failures: list[str] = []
    conflict_ids: set[str] = set()
    internal_prerequisite_passed = False
    internal_live_regenerated_count = 0
    verified_material_predecessor_ids: frozenset[str] = frozenset()
    try:
        registry = read_json(root / registry_relative)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        return [f"claim registry unreadable: {exc}"], {}

    required_top = {
        "schema_version",
        "revision",
        "active_gate",
        "coverage_report_path",
        "declared_surfaces",
        "non_claim_categories",
        "claim_kinds",
        "migration",
        "claims",
        "bindings",
    }
    if set(registry) != required_top:
        failures.append("claim registry top-level fields differ")
    if registry.get("schema_version") != SCHEMA_VERSION:
        failures.append("claim registry schema differs")
    if type(registry.get("revision")) is not int or registry["revision"] < 1:
        failures.append("claim registry revision must be a positive integer")
    registry_revision = registry.get("revision")
    if registry_revision == 2 and registry.get("migration") is not None:
        failures.append("initial claim registry must not carry migration metadata")
    if type(registry_revision) is int and registry_revision > 2 and not isinstance(
        registry.get("migration"), dict
    ):
        failures.append(
            "successor claim registry lacks retained migration metadata"
        )
    migration_failures, verified_material_predecessor_ids = (
        _migration_assessment(root, registry)
    )
    failures.extend(migration_failures)
    if registry.get("non_claim_categories") != sorted(
        ALLOWED_NONCLAIM_CATEGORIES
    ):
        failures.append("claim registry nonclaim category set differs")
    if registry.get("claim_kinds") != sorted(ALLOWED_CLAIM_KINDS):
        failures.append("claim registry claim-kind set differs")

    try:
        current = read_json(root / "mission/current.json")
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        failures.append(f"current pointer unreadable: {exc}")
        current = {}
    active_gate = registry.get("active_gate")
    if active_gate != current.get("active_gate"):
        failures.append(
            "existing-but-stale active gate: claim registry and current pointer disagree"
        )
    try:
        expected_report_path = report_path_for_gate(active_gate)
    except (TypeError, ValueError) as exc:
        failures.append(f"claim coverage report lifecycle invalid: {exc}")
        expected_report_path = None
    if registry.get("coverage_report_path") != expected_report_path:
        failures.append(
            "claim coverage report path is not versioned under the active gate"
        )

    declared = registry.get("declared_surfaces")
    if not isinstance(declared, list):
        failures.append("declared_surfaces must be an array")
        declared = []
    try:
        surface_paths = declared_surface_paths(root)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        failures.append(f"declared public surface pointer invalid: {exc}")
        surface_paths = ()
    surface_digests = _validate_declared_surfaces(
        root,
        declared,
        surface_paths,
        failures,
    )

    try:
        actual_bindings = extract_all_bindings(root)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        failures.append(f"cannot extract public quantitative atoms: {exc}")
        actual_bindings = []
    actual_by_id = {item.binding_id: item for item in actual_bindings}
    if len(actual_by_id) != len(actual_bindings):
        failures.append("extracted binding IDs are not unique")
    authority_failures, binding_authorization_digest = (
        _binding_authority_failures(
            root,
            registry=registry,
            active_gate=active_gate,
        )
    )
    failures.extend(authority_failures)
    binding_authority_passed = not authority_failures

    binding_list = registry.get("bindings")
    if not isinstance(binding_list, list):
        failures.append("bindings must be an array")
        binding_list = []
    registered_by_id: dict[str, dict[str, Any]] = {}
    binding_required = {
        "binding_id",
        "path",
        "locator",
        "structural_anchor_sha256",
        "segment_ordinal",
        "atom_ordinal",
        "atom",
        "role",
        "resolution",
    }
    for binding in binding_list:
        if not isinstance(binding, dict):
            failures.append("binding entry is not an object")
            continue
        if set(binding) != binding_required:
            failures.append(f"binding fields differ: {binding.get('binding_id')}")
        binding_id = binding.get("binding_id")
        if not isinstance(binding_id, str):
            failures.append("binding lacks a string binding_id")
            continue
        if binding_id in registered_by_id:
            failures.append(f"duplicate binding ID: {binding_id}")
        registered_by_id[binding_id] = binding
    registered_ids_in_order = [
        binding.get("binding_id")
        for binding in binding_list
        if isinstance(binding, dict)
        and isinstance(binding.get("binding_id"), str)
    ]
    if registered_ids_in_order != sorted(registered_ids_in_order):
        failures.append("binding inventory is not in canonical binding-ID order")

    unclassified_ids = sorted(set(actual_by_id) - set(registered_by_id))
    for binding_id in unclassified_ids:
        binding = actual_by_id[binding_id]
        failures.append(
            f"unclassified quantitative atom: {binding.segment.path} "
            f"[{binding.segment.locator}] {binding.atom.text!r}"
        )
    missing_ids = sorted(set(registered_by_id) - set(actual_by_id))
    for binding_id in missing_ids:
        registered = registered_by_id[binding_id]
        qualifier = (
            "removed missingness binding"
            if registered.get("role") == "explicit_missingness"
            else "registered quantitative binding missing"
        )
        failures.append(f"{qualifier}: {binding_id}")

    claims = registry.get("claims")
    if not isinstance(claims, dict):
        failures.append("claims must be an object")
        claims = {}

    forward: defaultdict[str, list[str]] = defaultdict(list)
    classified_nonclaim_count = 0
    public_binding_count = 0
    for binding_id in sorted(set(actual_by_id) & set(registered_by_id)):
        actual = actual_by_id[binding_id]
        registered = registered_by_id[binding_id]
        public_binding_count += 1
        invalid_syntax = _invalid_atom_syntax(actual)
        if invalid_syntax is not None:
            failures.append(
                "invalid public quantitative syntax: "
                f"{actual.segment.path} [{actual.segment.locator}] "
                f"{actual.atom.text!r}: {invalid_syntax}"
            )
            conflict_ids.add(binding_id)
            continue
        structural_fields = {
            "binding_id": actual.binding_id,
            "path": actual.segment.path,
            "locator": actual.segment.locator,
            "structural_anchor_sha256": actual.segment.anchor_sha256,
            "segment_ordinal": actual.segment.segment_ordinal,
            "atom_ordinal": actual.atom_ordinal,
            "atom": {
                "text": actual.atom.text,
                "normalized": actual.atom.normalized,
            },
            "role": atom_role(actual),
        }
        actual_structural = {
            key: registered.get(key) for key in structural_fields
        }
        if actual_structural != structural_fields:
            failures.append(f"binding atom/anchor conflict: {binding_id}")
            conflict_ids.add(binding_id)

        registered_resolution = registered.get("resolution")
        resolution = (
            registered_resolution
            if isinstance(registered_resolution, dict)
            else {}
        )
        resolution_type = resolution.get("type")
        if resolution_type == "typed_non_claim":
            classified_nonclaim_count += 1
            category = resolution.get("category")
            if (
                not isinstance(category, str)
                or category not in ALLOWED_NONCLAIM_CATEGORIES
            ):
                failures.append(f"unknown nonclaim category: {binding_id}")
            lexical_resolution = derive_nonclaim(actual)
            if lexical_resolution != resolution:
                failures.append(
                    f"typed nonclaim is not licensed by its exact lexical "
                    f"rule: {binding_id}: expected={lexical_resolution!r} "
                    f"registered={resolution!r}"
                )
                conflict_ids.add(binding_id)
        elif resolution_type == "claim_projection":
            claim_id = resolution.get("claim_id")
            if not isinstance(claim_id, str) or claim_id not in claims:
                failures.append(f"claim projection is unbound: {binding_id}")
            else:
                forward[claim_id].append(binding_id)
                projection = resolution.get("projection")
                if not isinstance(projection, dict):
                    failures.append(f"claim projection is malformed: {binding_id}")
                    conflict_ids.add(binding_id)
                else:
                    matched, detail = projection_matches(
                        actual,
                        claims[claim_id],
                        projection,
                    )
                    if not matched:
                        failures.append(
                            f"conflicting claim projection: {binding_id}: {detail}"
                        )
                        conflict_ids.add(binding_id)
        else:
            failures.append(f"unknown binding resolution: {binding_id}")
            conflict_ids.add(binding_id)

    for claim_id, claim in claims.items():
        _validate_claim_schema(claim_id, claim, failures)
        if isinstance(claim, dict):
            reverse = claim.get("surface_binding_ids")
            if isinstance(reverse, list) and all(
                isinstance(binding_id, str) for binding_id in reverse
            ):
                expected_reverse = sorted(forward.get(claim_id, []))
                if sorted(reverse) != expected_reverse:
                    failures.append(
                        f"binding/claim reciprocity conflict for {claim_id}: "
                        f"claim={sorted(reverse)!r} bindings={expected_reverse!r}"
                    )
                missingness = claim.get("missingness")
                missingness_binding = (
                    missingness.get("binding_id")
                    if isinstance(missingness, dict)
                    else None
                )
                if (
                    missingness_binding is not None
                    and missingness_binding not in reverse
                ):
                    failures.append(
                        f"claim {claim_id} missingness binding is outside "
                        "its surface bindings"
                    )
                if (
                    isinstance(claim.get("kind"), str)
                    and claim.get("kind") in RETAINED_POLICY
                    and claim.get("superseded_by") is None
                    and len(reverse) == 1
                ):
                    binding_id = reverse[0]
                    if missingness_binding != binding_id:
                        failures.append(
                            f"claim {claim_id} missingness binding does not "
                            "match its sole surface binding"
                        )
                    elif (
                        isinstance(missingness, dict)
                        and missingness.get("mode") == "surface_explicit"
                    ):
                        registered_binding = registered_by_id.get(binding_id)
                        atom = (
                            registered_binding.get("atom")
                            if isinstance(registered_binding, dict)
                            else None
                        )
                        normalized = (
                            atom.get("normalized")
                            if isinstance(atom, dict)
                            else None
                        )
                        if (
                            not isinstance(registered_binding, dict)
                            or registered_binding.get("role")
                            != "explicit_missingness"
                            or missingness.get("normalized_value") != normalized
                        ):
                            failures.append(
                                f"claim {claim_id} explicit missingness "
                                "role/value differs from its surface atom"
                            )
    for claim_id in forward:
        if claim_id not in claims:
            failures.append(f"binding references absent claim: {claim_id}")
    failures.extend(
        _supersession_failures(
            claims,
            verified_material_predecessor_ids=(
                verified_material_predecessor_ids
            ),
        )
    )

    _validate_sources(
        root,
        claims,
        failures,
        check_source_digests=check_source_digests,
        check_seals=check_seals,
        actual_bindings_by_id=actual_by_id,
    )

    if check_internal and root.resolve() == ROOT.resolve():
        try:
            expected_internal = builder.build_internal_claims()
        except Exception as exc:
            failures.append(f"cannot rebuild internal claims: {exc}")
            expected_internal = {}
        prerequisite_failures = validate_internal_prerequisites(
            root,
            expected_internal,
        )
        failures.extend(prerequisite_failures)
        internal_prerequisite_passed = not prerequisite_failures
        for claim_id, expected in expected_internal.items():
            actual = claims.get(claim_id)
            if not isinstance(actual, dict):
                failures.append(f"internally regenerated claim missing: {claim_id}")
                continue
            if actual.get("superseded_by") is not None:
                failures.append(
                    f"current internal claim is already superseded: {claim_id}"
                )
                continue
            expected = deepcopy(expected)
            expected["surface_binding_ids"] = sorted(forward.get(claim_id, []))
            if type(actual.get("revision")) is int:
                expected["revision"] = actual["revision"]
            for mismatch in compare_json(
                actual,
                expected,
                path=f"claims.{claim_id}",
            ):
                failures.append(f"internal claim mismatch: {mismatch}")
        live_internal_ids = {
            claim_id
            for claim_id, claim in claims.items()
            if isinstance(claim, dict)
            and claim.get("kind") == "internally_regenerated_empirical"
            and claim.get("superseded_by") is None
        }
        if live_internal_ids != set(expected_internal):
            failures.append(
                "live internally regenerated claim inventory differs: "
                f"{sorted(live_internal_ids ^ set(expected_internal))}"
            )
        if internal_prerequisite_passed:
            internal_live_regenerated_count = len(live_internal_ids)

    registered_role_by_id = {
        binding_id: binding.get("role")
        for binding_id, binding in registered_by_id.items()
    }
    corrected_reference_bindings = sorted(
        binding_id
        for binding_id, role in registered_role_by_id.items()
        if role == "corrective_historical_reference"
    )
    stale_superseded_assertions = sorted(
        binding_id
        for claim in claims.values()
        if isinstance(claim, dict)
        and claim.get("superseded_by") is not None
        for binding_id in (
            claim.get("surface_binding_ids")
            if isinstance(claim.get("surface_binding_ids"), list)
            else []
        )
        if isinstance(binding_id, str)
        and registered_role_by_id.get(binding_id)
        != "corrective_historical_reference"
    )
    if stale_superseded_assertions:
        failures.append(
            "superseded claims remain visible as unqualified assertions: "
            + ", ".join(stale_superseded_assertions)
        )
    superseded_claims_still_visible = [
        {
            "claim_id": claim_id,
            "binding_ids": sorted(
                binding_id
                for binding_id in claim.get("surface_binding_ids", [])
                if isinstance(binding_id, str)
            ),
        }
        for claim_id, claim in sorted(claims.items())
        if isinstance(claim, dict)
        and claim.get("superseded_by") is not None
        and isinstance(claim.get("surface_binding_ids"), list)
        and bool(claim["surface_binding_ids"])
    ]

    kind_counts = Counter(
        claim.get("kind")
        for claim in claims.values()
        if isinstance(claim, dict) and isinstance(claim.get("kind"), str)
    )
    unresolved_by_kind = Counter(
        claim.get("kind")
        for claim in claims.values()
        if isinstance(claim, dict)
        and isinstance(claim.get("kind"), str)
        and isinstance(claim.get("value"), dict)
        and claim["value"].get("semantic_metadata_resolution")
        == UNRESOLVED_RETAINED_SEMANTIC_STATE
    )
    unresolved_retained_count = sum(unresolved_by_kind.values())
    report = {
        "schema_version": REPORT_SCHEMA_VERSION,
        "registry_schema_version": SCHEMA_VERSION,
        "active_gate": active_gate,
        "registry_sha256": sha256(root / registry_relative),
        "registered_claim_count": len(claims),
        "public_binding_count": public_binding_count,
        "classified_non_claim_count": classified_nonclaim_count,
        "unclassified_count": len(unclassified_ids),
        "conflicting_projection_count": len(conflict_ids),
        "binding_authority_passed": binding_authority_passed,
        "binding_authorization_sha256": binding_authorization_digest,
        "internal_prerequisite_passed": internal_prerequisite_passed,
        "internally_regenerated_count": (
            internal_live_regenerated_count
            if internal_prerequisite_passed
            else 0
        ),
        "external_citation_count": kind_counts["external_citation"],
        "historical_semantic_metadata_unresolved_count": (
            unresolved_by_kind["historical_empirical"]
        ),
        "external_semantic_metadata_unresolved_count": (
            unresolved_by_kind["external_citation"]
        ),
        "retained_semantic_metadata_unresolved_count": (
            unresolved_retained_count
        ),
        "coverage_interpretation": (
            "Quantitative-token visibility and binding coverage do not "
            "constitute semantic adjudication of unresolved retained claims."
        ),
        "claim_kind_counts": {
            kind: kind_counts[kind] for kind in sorted(ALLOWED_CLAIM_KINDS)
        },
        "corrective_historical_reference_count": len(
            corrected_reference_bindings
        ),
        "stale_superseded_assertion_count": len(
            stale_superseded_assertions
        ),
        "verified_material_predecessor_ids": sorted(
            verified_material_predecessor_ids
        ),
        "superseded_claims_still_visible": (
            superseded_claims_still_visible
        ),
        "preregistered_surface_paths": [
            "README.md",
            "paper/telos.tex",
            surface_paths[3] if len(surface_paths) > 3 else None,
            "mission/current.json",
        ],
        "supplemental_hardening_surface_paths": [
            "paper/README.md",
            surface_paths[4] if len(surface_paths) > 4 else None,
        ],
        "surface_digests": {
            path: surface_digests[path]
            for path in surface_paths
            if path in surface_digests
        },
    }
    if check_report and expected_report_path is not None:
        retained_report: dict[str, Any] | None = None
        canonical_report = _canonical_source_path(expected_report_path)
        report_file, report_failure = (
            _regular_repository_file(root, canonical_report)
            if canonical_report is not None
            else (None, "coverage report path is unsafe")
        )
        if report_failure is not None or report_file is None:
            failures.append(
                "retained claim coverage report unsafe or missing: "
                f"{report_failure}"
            )
        else:
            try:
                retained_report = read_json(report_file)
            except (OSError, json.JSONDecodeError, ValueError) as exc:
                failures.append(
                    f"retained claim coverage report unreadable: {exc}"
                )
                retained_report = None
        if report_file is not None and retained_report is not None:
            for mismatch in compare_json(
                retained_report,
                report,
                path="claim_coverage_report",
            ):
                failures.append(
                    f"retained claim coverage report mismatch: {mismatch}"
                )
    return failures, report


def _stage_bytes(directory: Path, prefix: str, content: bytes) -> Path:
    descriptor, name = tempfile.mkstemp(
        dir=directory,
        prefix=prefix,
        suffix=".tmp",
    )
    try:
        with os.fdopen(descriptor, "wb") as handle:
            os.fchmod(handle.fileno(), 0o644)
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
    except Exception:
        Path(name).unlink(missing_ok=True)
        raise
    return Path(name)


def _write_bootstrap_and_report(
    root: Path = ROOT,
) -> tuple[list[str], dict[str, Any]]:
    try:
        current = read_json(root / "mission/current.json")
        active_gate = current.get("active_gate")
        if not isinstance(active_gate, str):
            raise ValueError("mission/current.json active_gate must be a string")
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        return [f"cannot preflight claim bootstrap: {exc}"], {}

    preflight, registry_path, report_path = _preflight_bootstrap_outputs(
        root,
        active_gate=active_gate,
    )
    if preflight or registry_path is None or report_path is None:
        return preflight, {}

    try:
        registry = bootstrap_registry(root)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        return [f"cannot build authorized claim registry: {exc}"], {}
    registry_bytes = (
        json.dumps(registry, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")

    staged_registry: Path | None = None
    staged_report: Path | None = None
    try:
        staged_registry = _stage_bytes(
            registry_path.parent,
            ".claim-registry-",
            registry_bytes,
        )
        failures, report = validate(
            root=root,
            registry_relative=staged_registry,
            check_internal=root.resolve() == ROOT.resolve(),
            check_source_digests=True,
            check_seals=root.resolve() == ROOT.resolve(),
            check_report=False,
        )
        if failures:
            return failures, report
        report_bytes = (
            json.dumps(report, indent=2, sort_keys=True) + "\n"
        ).encode("utf-8")
        staged_report = _stage_bytes(
            report_path.parent,
            ".claim-report-",
            report_bytes,
        )

        repeated_preflight, repeated_registry, repeated_report = (
            _preflight_bootstrap_outputs(root, active_gate=active_gate)
        )
        if (
            repeated_preflight
            or repeated_registry != registry_path
            or repeated_report != report_path
        ):
            return repeated_preflight or [
                "claim bootstrap output paths changed during validation"
            ], report

        report_linked = False
        try:
            # Hard-link publication is an exclusive create on the same
            # filesystem.  Unlike os.replace, it cannot overwrite a registry
            # or report created by another process after the last preflight.
            os.link(staged_report, report_path)
            report_linked = True
            os.link(staged_registry, registry_path)
        except OSError as exc:
            if report_linked:
                try:
                    report_stat = report_path.stat(follow_symlinks=False)
                    staged_stat = staged_report.stat(follow_symlinks=False)
                    if (
                        report_stat.st_dev == staged_stat.st_dev
                        and report_stat.st_ino == staged_stat.st_ino
                    ):
                        report_path.unlink()
                except OSError as rollback_exc:
                    return [
                        f"claim bootstrap exclusive create failed: {exc}; "
                        f"owned report cleanup also failed: {rollback_exc}"
                    ], report
            return [f"claim bootstrap exclusive create failed: {exc}"], report
        staged_report.unlink()
        staged_report = None
        staged_registry.unlink()
        staged_registry = None
        return [], report
    finally:
        if staged_registry is not None:
            staged_registry.unlink(missing_ok=True)
        if staged_report is not None:
            staged_report.unlink(missing_ok=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--print-bootstrap",
        action="store_true",
        help="print a reviewed registry candidate; validation never refreshes it",
    )
    parser.add_argument(
        "--write-bootstrap",
        action="store_true",
        help="write the reviewed registry and its active-gate-versioned report",
    )
    parser.add_argument(
        "--print-report",
        action="store_true",
        help="print the recomputed coverage report after validation",
    )
    args = parser.parse_args()
    if args.print_bootstrap:
        print(json.dumps(bootstrap_registry(), indent=2, sort_keys=True))
        return 0
    if args.write_bootstrap:
        failures, report = _write_bootstrap_and_report()
        if failures:
            print("claim registry bootstrap: FAIL", file=sys.stderr)
            for failure in failures:
                print(f"  - {failure}", file=sys.stderr)
            return 1
        print(
            f"wrote {REGISTRY_PATH} and "
            f"{report_path_for_gate(report['active_gate'])}"
        )
        return 0
    failures, report = validate()
    if failures:
        print("claim registry: FAIL", file=sys.stderr)
        for failure in failures:
            print(f"  - {failure}", file=sys.stderr)
        return 1
    if args.print_report:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(
            "claim registry: "
            f"{report['registered_claim_count']} claims; "
            f"{report['public_binding_count']} public bindings; "
            f"{report['classified_non_claim_count']} typed nonclaims; "
            f"{report['unclassified_count']} unclassified; "
            f"{report['conflicting_projection_count']} conflicts"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
