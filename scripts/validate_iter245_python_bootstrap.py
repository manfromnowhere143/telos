#!/usr/bin/env python3
"""Fail closed on the exact Iter245 offline Python bootstrap contract."""

from __future__ import annotations

import ast
import hashlib
from pathlib import Path
import re
import stat
import sys

import yaml


ROOT = Path(__file__).resolve().parents[1]
BOOTSTRAP = ROOT / "scripts/bootstrap_iter245_python.sh"
EXTRACTOR = ROOT / "scripts/extract_iter245_python.py"
VALIDATOR = Path(__file__).resolve()
WORKFLOW = ROOT / ".github/workflows/ci.yml"
BOOTSTRAP_SHA256 = "e4c7320047bf66e75709649ceaa29239e206ca5a7fe85b63456ed46788af1638"
EXTRACTOR_SHA256 = "2cf5ffa33ea82367f62d5e96d34a42f6aacac522520f918d51c735409f0be374"
CHECKOUT = "actions/checkout@9c091bb21b7c1c1d1991bb908d89e4e9dddfe3e0"
INSTALL_RUN = (
    'wheelhouse="$(mktemp -d /tmp/telos-ci-wheelhouse.XXXXXX)"\n'
    "export PIP_DISABLE_PIP_VERSION_CHECK=1\n"
    "python3 -I -P -m pip --isolated --disable-pip-version-check download \\\n"
    "  --index-url https://pypi.org/simple --no-deps \\\n"
    "  --no-cache-dir --require-hashes --only-binary=:all: \\\n"
    '  --dest "$wheelhouse" -r requirements-ci.txt\n'
    "python3 -I -P -m pip --isolated --disable-pip-version-check install \\\n"
    '  --no-index --find-links "$wheelhouse" \\\n'
    "  --no-deps \\\n"
    "  --no-cache-dir --require-hashes --only-binary=:all: \\\n"
    "  -r requirements-ci.txt\n"
)
TEST_RUN = "python3 -I scripts/run_iter241_pytest.py --run"
ASSETS = (
    {
        "matrix": "3.11",
        "version": "3.11.15",
        "tag": "3.11.15-27649667267",
        "asset_id": "449621339",
        "name": "python-3.11.15-linux-24.04-x64.tar.gz",
        "size": "92521776",
        "sha256": "a972aa7e44f1596aa63274a9ac58dbc2349c321f3f78b1c0fc5a60d5d69a6402",
    },
    {
        "matrix": "3.12",
        "version": "3.12.13",
        "tag": "3.12.13-27650778726",
        "asset_id": "449635535",
        "name": "python-3.12.13-linux-24.04-x64.tar.gz",
        "size": "94990593",
        "sha256": "ce7d511228f095b5ea1ad5568543388870f5964688303f9ddc24ba06c336bfba",
    },
)
PYTHON_COMMAND = re.compile(r"(?<![A-Za-z0-9_])(?:python(?:3(?:\.\d+)*)?|pip(?:3)?)\b")


def expected_bootstrap_run(validator_raw: bytes) -> str:
    validator_sha256 = hashlib.sha256(validator_raw).hexdigest()
    bindings = (
        (BOOTSTRAP_SHA256, "scripts/bootstrap_iter245_python.sh"),
        (EXTRACTOR_SHA256, "scripts/extract_iter245_python.py"),
        (validator_sha256, "scripts/validate_iter245_python_bootstrap.py"),
    )
    lines = [
        f"/usr/bin/printf '%s  %s\\n' '{digest}' '{path}' | /usr/bin/sha256sum --check --strict -"
        for digest, path in bindings
    ]
    lines.append(
        '/usr/bin/bash scripts/bootstrap_iter245_python.sh --bootstrap "${{ matrix.python-version }}"'
    )
    return "\n".join(lines) + "\n"


class StrictLoader(yaml.BaseLoader):
    """Preserve scalar spellings and reject duplicate YAML mappings."""

    def construct_mapping(self, node: yaml.MappingNode, deep: bool = False) -> dict:
        if not isinstance(node, yaml.MappingNode):
            raise yaml.constructor.ConstructorError(
                None, None, "expected a mapping", node.start_mark
            )
        result: dict = {}
        for key_node, value_node in node.value:
            key = self.construct_object(key_node, deep=deep)
            if key in result:
                raise yaml.constructor.ConstructorError(
                    "while constructing a mapping",
                    node.start_mark,
                    f"duplicate key {key!r}",
                    key_node.start_mark,
                )
            result[key] = self.construct_object(value_node, deep=deep)
        return result


def _source_errors(
    raw: bytes,
    *,
    expected_sha256: str,
    mode: int,
    label: str,
) -> tuple[list[str], str | None]:
    errors: list[str] = []
    if hashlib.sha256(raw).hexdigest() != expected_sha256:
        errors.append(f"{label} digest differs")
    if not stat.S_ISREG(mode) or mode & stat.S_IXUSR == 0 or mode & 0o022:
        errors.append(f"{label} mode is not owner-executable and non-writable")
    try:
        return errors, raw.decode("utf-8")
    except UnicodeDecodeError:
        return [*errors, f"{label} is not UTF-8"], None


def bootstrap_errors(raw: bytes, *, mode: int = 0o100755) -> list[str]:
    errors, text = _source_errors(
        raw,
        expected_sha256=BOOTSTRAP_SHA256,
        mode=mode,
        label="bootstrap",
    )
    if text is None:
        return errors
    if text.count(f"EXTRACTOR_SHA256={EXTRACTOR_SHA256}") != 1:
        errors.append("bootstrap authenticated extractor digest differs")
    for asset in ASSETS:
        assignments = (
            f"EXACT_VERSION={asset['version']}",
            f"RELEASE_TAG={asset['tag']}",
            f"ASSET_ID={asset['asset_id']}",
            f"ASSET_NAME={asset['name']}",
            f"ASSET_SIZE={asset['size']}",
            f"ASSET_SHA256={asset['sha256']}",
        )
        for assignment in assignments:
            if text.count(assignment) != 1:
                errors.append(f"bootstrap asset {asset['matrix']} assignment differs: {assignment}")
    required = (
        "set -euo pipefail",
        "shopt -s inherit_errexit",
        "umask 077",
        "exit 2",
        "--disable",
        "--max-redirs 1",
        "--proto '=https'",
        "--proto-redir '=https'",
        "https://release-assets.githubusercontent.com/*",
        'verify_archive "$archive"',
        "if ! system_python=$(validate_system_python); then",
        "if ! download_observation=$(",
        "if ! downloaded_python=$(validate_downloaded_python",
        "descriptor = os.open(source, os.O_RDONLY | nofollow)",
        "metadata = os.fstat(stream.fileno())",
        "hashlib.sha256(raw).hexdigest() != expected",
        'exec(compile(raw, source, "exec"), namespace)',
        "run_authenticated_extractor \\",
        '--archive-size "$ASSET_SIZE"',
        '--archive-sha256 "$ASSET_SHA256"',
        '--validate-tree "$python_root"',
        '--python-version "$EXACT_VERSION"',
        '/usr/bin/unlink -- "$archive"',
        'LD_LIBRARY_PATH="$python_root/lib"',
        '"$downloaded_python" -I -P -B -S -c',
        'Path("/proc/self/maps")',
        "import pip",
        '"$downloaded_python" -I -P -B -m pip --version',
        "printf 'LD_AUDIT=\\n'",
        "printf 'LD_PRELOAD=\\n'",
        "printf 'PIP_CONFIG_FILE=/dev/null\\n'",
        "printf 'PIP_DISABLE_PIP_VERSION_CHECK=1\\n'",
        "printf 'PIP_EXTRA_INDEX_URL=\\n'",
        "printf 'PIP_NO_INPUT=1\\n'",
        "printf 'PIP_TRUSTED_HOST=\\n'",
        "printf 'OPENAI_API_KEY=\\n'",
        "printf 'ANTHROPIC_API_KEY=\\n'",
        "printf 'GOOGLE_API_KEY=\\n'",
        "registered_asset_id",
        "redirect_count",
        "final_host",
        'tree_group_or_world_writable\\":false',
        'upstream_setup_executed\\":false',
    )
    for fragment in required:
        if fragment not in text:
            errors.append(f"bootstrap control absent: {fragment}")
    if text.count("/usr/bin/env -i ") != 4:
        errors.append("bootstrap environment isolation count differs")
    if text.count('LD_LIBRARY_PATH="$python_root/lib"') != 2:
        errors.append("bootstrap loader binding count differs")
    try:
        body = text.split("bootstrap_python() {", 1)[1].split("\n}\n\nmain()", 1)[0]
    except IndexError:
        return [*errors, "bootstrap function boundary differs"]
    extractor_calls = [
        match.start() for match in re.finditer(r"(?m)^  run_authenticated_extractor \\\s*$", body)
    ]
    if len(extractor_calls) != 2:
        errors.append("bootstrap authenticated extractor call count differs")
        extractor_calls = [-1, -1]
    ordered = (
        "if ! download_observation=$(",
        'verify_archive "$archive"',
        extractor_calls[0],
        '/usr/bin/unlink -- "$archive"',
        "if ! downloaded_python=$(validate_downloaded_python",
        '"$downloaded_python" -I -P -B -S -c',
        '"$downloaded_python" -I -P -B -m pip --version',
        extractor_calls[1],
        '--validate-tree "$python_root"',
        'printf \'%s\\n\' "$python_root/bin" >> "$GITHUB_PATH"',
    )
    positions = [item if isinstance(item, int) else body.find(item) for item in ordered]
    if any(position < 0 for position in positions) or positions != sorted(positions):
        errors.append("bootstrap verification/extraction/execution order differs")
    for forbidden in (
        "--retry",
        "retry-all-errors",
        "actions/setup-python",
        "ensurepip",
        "pip install",
        "curl |",
        "eval ",
        "ldd ",
        'bash "$setup',
        'source "$setup',
        '\\"asset_id\\":',
    ):
        if forbidden in text:
            errors.append(f"bootstrap contains forbidden authority: {forbidden}")
    return errors


def extractor_errors(raw: bytes, *, mode: int = 0o100755) -> list[str]:
    errors, text = _source_errors(
        raw,
        expected_sha256=EXTRACTOR_SHA256,
        mode=mode,
        label="extractor",
    )
    if text is None:
        return errors
    try:
        ast.parse(text)
    except SyntaxError as exc:
        return [*errors, f"extractor syntax failed: {exc}"]
    required = (
        'if name == ".":',
        'if not name.startswith("./") or name.startswith("././"):',
        "duplicate_member_path",
        "hardlink_member",
        "special_member",
        "unknown_member_type",
        "member.type in {tarfile.REGTYPE, tarfile.AREGTYPE}",
        "symlink_target_non_canonical",
        "symlink_cycle",
        "symlink_target_absent",
        "member_parent_not_directory",
        "pax_global_metadata",
        "pax_metadata_member",
        "sparse_member",
        "archive_root_record_count",
        "archive_descriptor_identity",
        "archive_descriptor_digest",
        "descriptor = os.open(archive_path, os.O_RDONLY | nofollow)",
        'with os.fdopen(descriptor, "rb", buffering=0) as raw_archive:',
        "_hash_open_file(raw_archive)",
        "os.O_EXCL | nofollow",
        'tarfile.open(fileobj=raw_archive, mode="r|gz")',
        "archive_changed_during_extraction",
        "_clear_destination(root)",
        "validate_extracted_tree(root, python_version=python_version)",
        "0o700",
        "return 0o600",
        'Path("/usr/bin/readelf")',
        'if tags.get("RPATH"):',
        'for tag in ("AUDIT", "DEPAUDIT", "FILTER", "AUXILIARY")',
        'tags.get("RUNPATH")',
        "python_elf_needed_differs",
        "/lib64/ld-linux-x86-64.so.2",
        "contained_libpython_mode_or_owner",
    )
    for fragment in required:
        if fragment not in text:
            errors.append(f"extractor control absent: {fragment}")
    if text.count("tarfile.open(fileobj=raw_archive") != 2:
        errors.append("extractor authenticated descriptor parse count differs")
    for forbidden in (
        ".extract(",
        ".extractall(",
        "unpack_archive(",
        "os.system(",
        "shell=True",
        "patchelf",
        "archive_path.open(",
        'Path("/opt/hostedtoolcache")',
    ):
        if forbidden in text:
            errors.append(f"extractor contains forbidden authority: {forbidden}")
    return errors


def workflow_errors(raw: bytes, *, validator_raw: bytes | None = None) -> list[str]:
    errors: list[str] = []
    if validator_raw is None:
        validator_raw = VALIDATOR.read_bytes()
    try:
        document = yaml.load(raw.decode("utf-8"), Loader=StrictLoader)
    except (UnicodeDecodeError, yaml.YAMLError) as exc:
        return [*errors, f"workflow parse failed: {exc}"]
    if not isinstance(document, dict):
        return [*errors, "workflow root differs"]
    if document.get("on") != {"push": "", "pull_request": ""}:
        errors.append("workflow triggers differ")
    if document.get("permissions") != {"contents": "read"}:
        errors.append("workflow permissions differ")
    jobs = document.get("jobs")
    if not isinstance(jobs, dict) or set(jobs) != {"verify"}:
        return [*errors, "workflow job set differs"]
    verify = jobs.get("verify") if isinstance(jobs, dict) else None
    if not isinstance(verify, dict):
        return [*errors, "workflow verify job is absent"]
    if verify.get("name") != "verify ${{ github.event_name }} py${{ matrix.python-version }}":
        errors.append("workflow job name differs")
    if verify.get("runs-on") != "ubuntu-24.04":
        errors.append("workflow runner differs")
    if verify.get("timeout-minutes") != "60":
        errors.append("workflow timeout differs")
    if any(key in verify for key in ("if", "continue-on-error", "env")):
        errors.append("workflow job failure or environment authority differs")
    if verify.get("strategy") != {
        "fail-fast": "false",
        "matrix": {"python-version": ["3.11", "3.12"]},
    }:
        errors.append("workflow Python matrix differs")
    steps = verify.get("steps")
    if not isinstance(steps, list):
        return [*errors, "workflow verify steps are absent"]
    if any(not isinstance(step, dict) for step in steps):
        return [*errors, "workflow step representation differs"]
    if any(
        any(key in step for key in ("if", "continue-on-error", "env", "shell", "working-directory"))
        for step in steps
    ):
        errors.append("workflow step failure or environment semantics differ")
    action_steps = [
        (index, step) for index, step in enumerate(steps) if isinstance(step.get("uses"), str)
    ]
    if len(action_steps) != 1 or action_steps[0][0] != 0:
        errors.append("workflow action set or order differs")
    elif action_steps[0][1].get("uses") != CHECKOUT or action_steps[0][1].get("with") != {
        "fetch-depth": "0",
        "persist-credentials": "false",
    }:
        errors.append("workflow checkout boundary differs")
    bootstrap_indexes = [
        index
        for index, step in enumerate(steps)
        if isinstance(step, dict) and step.get("name") == "Bootstrap offline verified Python"
    ]
    if len(bootstrap_indexes) != 1:
        return [*errors, "workflow bootstrap is absent or duplicated"]
    bootstrap_index = bootstrap_indexes[0]
    if bootstrap_index != 1:
        errors.append("workflow bootstrap position differs")
    if steps[bootstrap_index].get("run") != expected_bootstrap_run(validator_raw):
        errors.append("workflow bootstrap command differs")
    for step in steps[:bootstrap_index]:
        run = step.get("run") if isinstance(step, dict) else None
        if isinstance(run, str) and PYTHON_COMMAND.search(run):
            errors.append("workflow executes Python or pip before bootstrap")
    install_indexes = [
        index
        for index, step in enumerate(steps)
        if isinstance(step, dict) and step.get("name") == "Install verification tools"
    ]
    if len(install_indexes) != 1:
        errors.append("workflow hash-locked install is absent or duplicated")
        install_index = -1
    else:
        install_index = install_indexes[0]
    if install_index < 0 or steps[install_index].get("run") != INSTALL_RUN:
        errors.append("workflow hash-locked install command differs")
    test_indexes = [
        index
        for index, step in enumerate(steps)
        if isinstance(step, dict) and step.get("name") == "Tests"
    ]
    if len(test_indexes) != 1:
        errors.append("workflow authenticated tests are absent or duplicated")
        test_index = -1
    else:
        test_index = test_indexes[0]
    if test_index < 0 or steps[test_index].get("run") != TEST_RUN:
        errors.append("workflow authenticated test command differs")
    guard_indexes = [
        index
        for index, step in enumerate(steps)
        if isinstance(step, dict)
        and step.get("name") == "Iter245 offline verified Python bootstrap guard"
    ]
    if len(guard_indexes) != 1:
        errors.append("workflow Iter245 guard is absent or duplicated")
        guard_index = -1
    else:
        guard_index = guard_indexes[0]
    if guard_index < 0 or steps[guard_index].get("run") != (
        "python3 scripts/validate_iter245_python_bootstrap.py"
    ):
        errors.append("workflow Iter245 guard command differs")
    if not (
        bootstrap_index < install_index < test_index < guard_index
        if min(install_index, test_index, guard_index) >= 0
        else False
    ):
        errors.append("workflow critical-step order differs")
    lowered = raw.lower()
    for authority in (
        b"${{ secrets.",
        b"${{ github.token }}",
        b"gh_token",
        b"github_token",
    ):
        if authority in lowered:
            errors.append(f"workflow credential authority present: {authority.decode()}")
    return errors


def validation_errors(
    bootstrap_raw: bytes,
    extractor_raw: bytes,
    workflow_raw: bytes,
    *,
    validator_raw: bytes | None = None,
    bootstrap_mode: int = 0o100755,
    extractor_mode: int = 0o100755,
    validator_mode: int = 0o100644,
) -> list[str]:
    if validator_raw is None:
        validator_raw = VALIDATOR.read_bytes()
    validator_errors = []
    if not stat.S_ISREG(validator_mode) or validator_mode & 0o022:
        validator_errors.append("validator mode is not a non-writable regular file")
    return [
        *bootstrap_errors(bootstrap_raw, mode=bootstrap_mode),
        *extractor_errors(extractor_raw, mode=extractor_mode),
        *validator_errors,
        *workflow_errors(workflow_raw, validator_raw=validator_raw),
    ]


def main() -> int:
    errors = validation_errors(
        BOOTSTRAP.read_bytes(),
        EXTRACTOR.read_bytes(),
        WORKFLOW.read_bytes(),
        validator_raw=VALIDATOR.read_bytes(),
        bootstrap_mode=BOOTSTRAP.stat().st_mode,
        extractor_mode=EXTRACTOR.stat().st_mode,
        validator_mode=VALIDATOR.stat().st_mode,
    )
    if errors:
        print("Iter245 offline verified Python bootstrap guard failed:", file=sys.stderr)
        for error in errors:
            print(f" - {error}", file=sys.stderr)
        return 1
    print(
        "Iter245 offline verified Python source/contract guard: exact asset "
        "bindings, fail-closed archive and ELF controls, workflow order, and "
        "authenticated source binding pass; hosted execution is unverified here"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
