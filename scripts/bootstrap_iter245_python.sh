#!/usr/bin/env bash
set -euo pipefail
if (( BASH_VERSINFO[0] > 4 || (BASH_VERSINFO[0] == 4 && BASH_VERSINFO[1] >= 4) )); then
  shopt -s inherit_errexit
fi

IFS=$'\n\t'
umask 077

EXTRACTOR_SHA256=2cf5ffa33ea82367f62d5e96d34a42f6aacac522520f918d51c735409f0be374

deny() {
  printf 'iter245 offline verified Python bootstrap denied: %s\n' "$1" >&2
  exit 2
}

file_mode() {
  /usr/bin/stat -Lc '%a' -- "$1"
}

file_uid() {
  /usr/bin/stat -Lc '%u' -- "$1"
}

has_group_or_world_write() {
  local mode permission
  mode=$(file_mode "$1")
  permission=$((8#$mode))
  (( (permission & 0022) != 0 ))
}

validate_command_output_file() {
  local path=$1
  local current_uid

  current_uid=$(/usr/bin/id -u)
  [[ $path == /* ]] || deny command_output_path_not_absolute
  [[ -f $path && ! -L $path ]] || deny command_output_path_not_regular
  [[ $(file_uid "$path") == "$current_uid" ]] \
    || deny command_output_path_foreign_owned
  ! has_group_or_world_write "$path" || deny command_output_path_writable
}

validate_system_python() {
  local requested=/usr/bin/python3
  local resolved

  [[ -e $requested ]] || deny system_python_absent
  resolved=$(/usr/bin/realpath -- "$requested")
  [[ $resolved == /usr/bin/* ]] || deny system_python_outside_usr_bin
  [[ -f $resolved && ! -L $resolved && -x $resolved ]] \
    || deny system_python_not_regular_executable
  [[ $(file_uid "$resolved") == 0 ]] || deny system_python_not_root_owned
  ! has_group_or_world_write "$resolved" || deny system_python_writable
  printf '%s\n' "$resolved"
}

run_authenticated_extractor() {
  local system_python=$1
  local extractor=$2
  shift 2

  /usr/bin/env -i HOME=/nonexistent LANG=C.UTF-8 LC_ALL=C.UTF-8 \
    PATH=/usr/bin:/bin \
    "$system_python" -I -P -B -S -c '
import hashlib
import os
import stat
import sys

source = sys.argv[1]
expected = sys.argv[2]
arguments = sys.argv[3:]
nofollow = getattr(os, "O_NOFOLLOW", 0)
if not nofollow:
    raise SystemExit("authenticated extractor denied: no O_NOFOLLOW")
descriptor = os.open(source, os.O_RDONLY | nofollow)
with os.fdopen(descriptor, "rb", buffering=0) as stream:
    metadata = os.fstat(stream.fileno())
    raw = stream.read()
if (
    not stat.S_ISREG(metadata.st_mode)
    or metadata.st_uid != os.geteuid()
    or stat.S_IMODE(metadata.st_mode) & 0o022
):
    raise SystemExit("authenticated extractor denied: source identity")
if hashlib.sha256(raw).hexdigest() != expected:
    raise SystemExit("authenticated extractor denied: source digest")
sys.argv = [source, *arguments]
namespace = {
    "__name__": "__main__",
    "__file__": source,
    "__package__": None,
    "__cached__": None,
}
exec(compile(raw, source, "exec"), namespace)
' "$extractor" "$EXTRACTOR_SHA256" "$@"
}

resolve_asset() {
  local matrix_version=$1

  case "$matrix_version" in
    3.11)
      EXACT_VERSION=3.11.15
      RELEASE_TAG=3.11.15-27649667267
      ASSET_ID=449621339
      ASSET_NAME=python-3.11.15-linux-24.04-x64.tar.gz
      ASSET_SIZE=92521776
      ASSET_SHA256=a972aa7e44f1596aa63274a9ac58dbc2349c321f3f78b1c0fc5a60d5d69a6402
      ;;
    3.12)
      EXACT_VERSION=3.12.13
      RELEASE_TAG=3.12.13-27650778726
      ASSET_ID=449635535
      ASSET_NAME=python-3.12.13-linux-24.04-x64.tar.gz
      ASSET_SIZE=94990593
      ASSET_SHA256=ce7d511228f095b5ea1ad5568543388870f5964688303f9ddc24ba06c336bfba
      ;;
    *)
      deny unsupported_matrix_version
      ;;
  esac
  ARCHIVE_URL="https://github.com/actions/python-versions/releases/download/${RELEASE_TAG}/${ASSET_NAME}"
}

print_contract() {
  resolve_asset "$1"
  printf '%s\t%s\t%s\t%s\t%s\t%s\n' \
    "$EXACT_VERSION" "$RELEASE_TAG" "$ASSET_ID" "$ASSET_NAME" \
    "$ASSET_SIZE" "$ASSET_SHA256"
}

verify_archive() {
  local archive=$1
  local size digest

  [[ -f $archive && ! -L $archive ]] || deny archive_not_regular
  [[ $(file_uid "$archive") == "$(/usr/bin/id -u)" ]] \
    || deny archive_foreign_owned
  size=$(/usr/bin/stat -Lc '%s' -- "$archive")
  [[ $size == "$ASSET_SIZE" ]] || deny archive_size_mismatch
  digest=$(/usr/bin/sha256sum -- "$archive")
  digest=${digest%% *}
  [[ $digest == "$ASSET_SHA256" ]] || deny archive_sha256_mismatch
}

validate_downloaded_python() {
  local root=$1
  local link="$root/bin/python3"
  local executable current_uid

  [[ -e $link ]] || deny downloaded_python_absent
  executable=$(/usr/bin/realpath -- "$link")
  case "$executable" in
    "$root"/*) ;;
    *) deny downloaded_python_escapes_root ;;
  esac
  [[ -f $executable && ! -L $executable && -x $executable ]] \
    || deny downloaded_python_not_regular_executable
  current_uid=$(/usr/bin/id -u)
  [[ $(file_uid "$executable") == "$current_uid" ]] \
    || deny downloaded_python_foreign_owned
  ! has_group_or_world_write "$executable" || deny downloaded_python_writable
  printf '%s\n' "$executable"
}

bootstrap_python() {
  local matrix_version=$1
  local script_dir repository_root bootstrap_root archive python_root
  local download_observation redirect_count effective_url system_python
  local downloaded_python isolated_tmp

  [[ $(/usr/bin/uname -s) == Linux && $(/usr/bin/uname -m) == x86_64 ]] \
    || deny unsupported_platform
  resolve_asset "$matrix_version"
  validate_command_output_file "${GITHUB_PATH:-}"
  validate_command_output_file "${GITHUB_ENV:-}"
  if ! system_python=$(validate_system_python); then
    deny system_python_validation_failed
  fi

  script_dir=${BASH_SOURCE[0]%/*}
  repository_root=$(cd -- "$script_dir/.." && pwd -P)
  [[ -f $repository_root/scripts/extract_iter245_python.py ]] \
    || deny extractor_absent

  bootstrap_root=$(/usr/bin/mktemp -d /tmp/telos-iter245-python.XXXXXX)
  /usr/bin/chmod 0700 "$bootstrap_root"
  archive="$bootstrap_root/$ASSET_NAME"
  python_root="$bootstrap_root/python"
  isolated_tmp="$bootstrap_root/tmp"
  /usr/bin/mkdir -m 0700 "$python_root"
  /usr/bin/mkdir -m 0700 "$isolated_tmp"

  if ! download_observation=$(
    /usr/bin/env -i HOME=/nonexistent LANG=C.UTF-8 LC_ALL=C.UTF-8 \
      PATH=/usr/bin:/bin \
      /usr/bin/curl \
        --disable \
        --fail \
        --silent \
        --show-error \
        --location \
        --max-redirs 1 \
        --proto '=https' \
        --proto-redir '=https' \
        --connect-timeout 20 \
        --max-time 1200 \
        --output "$archive" \
        --write-out '%{num_redirects}\t%{url_effective}' \
        "$ARCHIVE_URL"
  ); then
    deny download_failed
  fi
  IFS=$'\t' read -r redirect_count effective_url <<< "$download_observation"
  [[ $redirect_count == 1 ]] || deny download_redirect_count
  case "$effective_url" in
    https://release-assets.githubusercontent.com/*) ;;
    *) deny download_final_host ;;
  esac
  verify_archive "$archive"

  run_authenticated_extractor \
    "$system_python" \
    "$repository_root/scripts/extract_iter245_python.py" \
    --archive "$archive" \
    --archive-size "$ASSET_SIZE" \
    --archive-sha256 "$ASSET_SHA256" \
    --destination "$python_root" \
    --python-version "$EXACT_VERSION"
  /usr/bin/unlink -- "$archive"

  [[ -f $python_root/setup.sh && ! -L $python_root/setup.sh \
    && ! -x $python_root/setup.sh ]] || deny upstream_setup_not_inert
  if ! downloaded_python=$(validate_downloaded_python "$python_root"); then
    deny downloaded_python_validation_failed
  fi

  /usr/bin/env -i HOME=/nonexistent LANG=C.UTF-8 LC_ALL=C.UTF-8 \
    PATH="$python_root/bin:/usr/bin:/bin" \
    LD_LIBRARY_PATH="$python_root/lib" \
    TMPDIR="$isolated_tmp" \
    "$downloaded_python" -I -P -B -S -c '
import json
from pathlib import Path
import sys
import sysconfig

root = Path(sys.argv[1]).resolve(strict=True)
expected = tuple(int(part) for part in sys.argv[2].split("."))

def contained(value):
    candidate = Path(value).resolve(strict=False)
    candidate.relative_to(root)
    return candidate

assert sys.version_info[:3] == expected
assert sys.flags.isolated == 1
assert sys.flags.ignore_environment == 1
assert sys.flags.no_user_site == 1
assert sys.flags.safe_path
assert contained(sys.executable).is_file()
for prefix in (sys.prefix, sys.exec_prefix, sys.base_prefix, sys.base_exec_prefix):
    contained(prefix)
for entry in sys.path:
    if entry:
        contained(entry)
paths = sysconfig.get_paths()
for name in ("data", "include", "platinclude", "platlib", "purelib", "scripts", "stdlib"):
    contained(paths[name])
mapped_libpython = []
for line in Path("/proc/self/maps").read_text(encoding="utf-8").splitlines():
    fields = line.split(maxsplit=5)
    if len(fields) == 6 and fields[5].startswith("/") and "libpython" in Path(fields[5]).name:
        library = contained(fields[5])
        mode = library.stat().st_mode & 0o7777
        assert mode & 0o022 == 0
        mapped_libpython.append(str(library.relative_to(root)))
assert mapped_libpython
sys.path.insert(0, str(contained(paths["purelib"])))
import pip
contained(pip.__file__)
print("iter245 first Python observation=" + json.dumps({
    "flags": {
        "ignore_environment": sys.flags.ignore_environment,
        "isolated": sys.flags.isolated,
        "no_user_site": sys.flags.no_user_site,
        "safe_path": bool(sys.flags.safe_path),
    },
    "libpython_contained": True,
    "pip_contained": True,
    "prefixes_contained": True,
    "version": ".".join(str(part) for part in sys.version_info[:3]),
}, sort_keys=True, separators=(",", ":")))
' "$python_root" "$EXACT_VERSION"
  /usr/bin/env -i HOME=/nonexistent LANG=C.UTF-8 LC_ALL=C.UTF-8 \
    PATH="$python_root/bin:/usr/bin:/bin" \
    LD_LIBRARY_PATH="$python_root/lib" \
    TMPDIR="$isolated_tmp" \
    "$downloaded_python" -I -P -B -m pip --version >/dev/null

  run_authenticated_extractor \
    "$system_python" \
    "$repository_root/scripts/extract_iter245_python.py" \
    --validate-tree "$python_root" \
    --python-version "$EXACT_VERSION"

  printf '%s\n' "$python_root/bin" >> "$GITHUB_PATH"
  {
    printf 'pythonLocation=%s\n' "$python_root"
    printf 'Python_ROOT_DIR=%s\n' "$python_root"
    printf 'Python3_ROOT_DIR=%s\n' "$python_root"
    printf 'PKG_CONFIG_PATH=%s\n' "$python_root/lib/pkgconfig"
    printf 'LD_LIBRARY_PATH=%s\n' "$python_root/lib"
    printf 'LD_AUDIT=\n'
    printf 'LD_PRELOAD=\n'
    printf 'PYTHONHOME=\n'
    printf 'PYTHONPATH=\n'
    printf 'PIP_CONFIG_FILE=/dev/null\n'
    printf 'PIP_DISABLE_PIP_VERSION_CHECK=1\n'
    printf 'PIP_EXTRA_INDEX_URL=\n'
    printf 'PIP_NO_INPUT=1\n'
    printf 'PIP_TRUSTED_HOST=\n'
    printf 'OPENAI_API_KEY=\n'
    printf 'ANTHROPIC_API_KEY=\n'
    printf 'GOOGLE_API_KEY=\n'
  } >> "$GITHUB_ENV"

  printf '%s\n' \
    "iter245 offline verified Python bootstrap observation={\"byte_count\":$ASSET_SIZE,\"final_host\":\"release-assets.githubusercontent.com\",\"matrix\":\"$matrix_version\",\"python\":\"$EXACT_VERSION\",\"redirect_count\":$redirect_count,\"registered_asset_id\":$ASSET_ID,\"sha256\":\"$ASSET_SHA256\",\"tree_group_or_world_writable\":false,\"upstream_setup_executed\":false}"
}

main() {
  case "${1:-}" in
    --contract)
      [[ $# == 2 ]] || deny contract_arity
      print_contract "$2"
      ;;
    --bootstrap)
      [[ $# == 2 ]] || deny bootstrap_arity
      bootstrap_python "$2"
      ;;
    *)
      deny unsupported_operation
      ;;
  esac
}

if [[ ${BASH_SOURCE[0]} == "$0" ]]; then
  main "$@"
fi
