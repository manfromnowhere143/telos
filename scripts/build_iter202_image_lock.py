#!/usr/bin/env python3
"""Resolve and offline-validate the immutable iter202 SWE-bench image lock.

Resolution performs read-only Docker Registry HTTP requests.  ``--check`` is
deliberately offline: it binds the committed lock to the exact frozen target
bytes, target order, deterministic tag mapping, manifest digests, image IDs,
and immutable pull references without consulting a mutable registry tag.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import sys
from typing import Any
import urllib.parse
import urllib.request


ROOT = Path(__file__).resolve().parents[1]
TARGETS = (
    ROOT
    / "experiments/iter202_natural_rate_scaled/proof/raw/solve_targets.json"
)
OUT = ROOT / "experiments/iter202_natural_rate_scaled/proof/raw/image_lock.json"

SCHEMA = "telos.iter202.image_lock.v1"
TARGET_SCHEMA = "telos.iter202.solve_targets.v1"
EXPECTED_COUNT = 53
EXPECTED_LOCK_SHA256 = "3ca640a16d48a244ab5fe3496ef7a7224016d4b63f5481eacec321b6cd97f5fd"
REGISTRY = "registry-1.docker.io"
AUTH = "auth.docker.io"
NAMESPACE = "swebench"
TAG_NAME = "latest"
DIGEST_RE = re.compile(r"sha256:[0-9a-f]{64}")
INSTANCE_RE = re.compile(r"[A-Za-z0-9_.-]+__[A-Za-z0-9_.-]+")
MANIFEST_MEDIA_TYPES = {
    "application/vnd.docker.distribution.manifest.v2+json",
    "application/vnd.oci.image.manifest.v1+json",
}
INDEX_MEDIA_TYPES = {
    "application/vnd.docker.distribution.manifest.list.v2+json",
    "application/vnd.oci.image.index.v1+json",
}
ACCEPT = ", ".join(
    [
        "application/vnd.oci.image.index.v1+json",
        "application/vnd.docker.distribution.manifest.list.v2+json",
        "application/vnd.oci.image.manifest.v1+json",
        "application/vnd.docker.distribution.manifest.v2+json",
    ]
)

TOP_KEYS = {"schema_version", "source_targets", "registry", "count", "images"}
SOURCE_KEYS = {
    "path",
    "sha256",
    "schema_version",
    "count",
    "ordered_instance_ids_sha256",
}
REGISTRY_KEYS = {
    "host",
    "namespace",
    "tag",
    "platform",
    "resolution_protocol",
}
IMAGE_KEYS = {
    "instance_id",
    "tag",
    "tag_manifest_digest",
    "manifest_digest",
    "manifest_media_type",
    "image_id",
    "reference",
}


class LockError(ValueError):
    """The frozen target set, registry response, or image lock is invalid."""


def _no_duplicate_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise LockError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _reject_nonfinite_constant(value: str) -> None:
    raise LockError(f"non-standard JSON numeric constant: {value}")


def load_json_strict(raw: bytes, label: str) -> dict[str, Any]:
    try:
        value = json.loads(
            raw,
            object_pairs_hook=_no_duplicate_object,
            parse_constant=_reject_nonfinite_constant,
        )
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise LockError(f"{label} is not valid UTF-8 JSON: {exc}") from exc
    if not isinstance(value, dict):
        raise LockError(f"{label} must be a JSON object")
    return value


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def ordered_ids_sha256(ids: list[str]) -> str:
    payload = json.dumps(ids, ensure_ascii=False, separators=(",", ":")).encode()
    return sha256(payload)


def image_repository(instance_id: str) -> str:
    if not INSTANCE_RE.fullmatch(instance_id):
        raise LockError(f"unsafe iter202 instance id: {instance_id!r}")
    suffix = instance_id.lower().replace("__", "_1776_")
    return f"{NAMESPACE}/sweb.eval.x86_64.{suffix}"


def image_tag(instance_id: str) -> str:
    return f"{image_repository(instance_id)}:{TAG_NAME}"


def _target_ids(raw: bytes) -> list[str]:
    data = load_json_strict(raw, "iter202 solve targets")
    targets = data.get("targets")
    if (
        data.get("schema_version") != TARGET_SCHEMA
        or data.get("count") != EXPECTED_COUNT
        or not isinstance(targets, list)
        or len(targets) != EXPECTED_COUNT
    ):
        raise LockError("iter202 solve targets do not match the frozen schema/count")
    ids: list[str] = []
    for index, row in enumerate(targets):
        if not isinstance(row, dict) or set(row) != {"instance_id", "repo"}:
            raise LockError(f"iter202 target row {index} has malformed or extra fields")
        iid = row.get("instance_id")
        repo = row.get("repo")
        if not isinstance(iid, str) or not isinstance(repo, str) or not repo:
            raise LockError(f"iter202 target row {index} has invalid values")
        image_repository(iid)
        ids.append(iid)
    if len(ids) != len(set(ids)):
        raise LockError("iter202 solve targets contain duplicate instance ids")
    return ids


def _token(repository: str, timeout: float) -> str:
    query = urllib.parse.urlencode(
        {
            "service": "registry.docker.io",
            "scope": f"repository:{repository}:pull",
        }
    )
    request = urllib.request.Request(f"https://{AUTH}/token?{query}")
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            body = load_json_strict(response.read(), f"token response for {repository}")
    except OSError as exc:
        raise LockError(f"cannot obtain read-only registry token for {repository}: {exc}") from exc
    token = body.get("token")
    if not isinstance(token, str) or not token:
        raise LockError(f"registry token response is malformed for {repository}")
    return token


def _manifest(
    repository: str, reference: str, token: str, timeout: float
) -> tuple[str, str, dict[str, Any]]:
    request = urllib.request.Request(
        f"https://{REGISTRY}/v2/{repository}/manifests/{reference}",
        headers={"Accept": ACCEPT, "Authorization": f"Bearer {token}"},
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
            header_digest = response.headers.get("Docker-Content-Digest", "")
            content_type = response.headers.get_content_type()
    except OSError as exc:
        raise LockError(
            f"cannot resolve read-only registry manifest {repository}:{reference}: {exc}"
        ) from exc
    computed_digest = f"sha256:{sha256(raw)}"
    if header_digest != computed_digest or not DIGEST_RE.fullmatch(header_digest):
        raise LockError(
            f"registry digest/header mismatch for {repository}:{reference}"
        )
    body = load_json_strict(raw, f"manifest {repository}:{reference}")
    media_type = body.get("mediaType", content_type)
    if not isinstance(media_type, str) or content_type != media_type:
        raise LockError(f"registry manifest media type mismatch for {repository}:{reference}")
    return header_digest, media_type, body


def resolve_image(instance_id: str, timeout: float = 30.0) -> dict[str, str]:
    repository = image_repository(instance_id)
    tag = image_tag(instance_id)
    token = _token(repository, timeout)
    tag_digest, media_type, body = _manifest(repository, TAG_NAME, token, timeout)
    manifest_digest = tag_digest

    if media_type in INDEX_MEDIA_TYPES:
        manifests = body.get("manifests")
        if not isinstance(manifests, list):
            raise LockError(f"manifest index is malformed for {tag}")
        candidates = [
            row
            for row in manifests
            if isinstance(row, dict)
            and isinstance(row.get("platform"), dict)
            and row["platform"].get("os") == "linux"
            and row["platform"].get("architecture") == "amd64"
            and row["platform"].get("variant") in (None, "")
            and DIGEST_RE.fullmatch(str(row.get("digest", "")))
        ]
        if len(candidates) != 1:
            raise LockError(f"expected exactly one linux/amd64 manifest for {tag}")
        manifest_digest = candidates[0]["digest"]
        resolved_digest, media_type, body = _manifest(
            repository, manifest_digest, token, timeout
        )
        if resolved_digest != manifest_digest:
            raise LockError(f"selected platform digest changed while resolving {tag}")

    if media_type not in MANIFEST_MEDIA_TYPES:
        raise LockError(f"unsupported runnable manifest type for {tag}: {media_type!r}")
    config = body.get("config")
    image_id = config.get("digest") if isinstance(config, dict) else None
    if not isinstance(image_id, str) or not DIGEST_RE.fullmatch(image_id):
        raise LockError(f"runnable manifest has no valid image config digest for {tag}")
    reference = f"{repository}@{manifest_digest}"
    return {
        "instance_id": instance_id,
        "tag": tag,
        "tag_manifest_digest": tag_digest,
        "manifest_digest": manifest_digest,
        "manifest_media_type": media_type,
        "image_id": image_id,
        "reference": reference,
    }


def build_lock(target_raw: bytes, timeout: float = 30.0) -> dict[str, Any]:
    ids = _target_ids(target_raw)
    images = []
    for index, iid in enumerate(ids, 1):
        print(f"resolving immutable image {index}/{len(ids)}: {iid}", file=sys.stderr)
        images.append(resolve_image(iid, timeout))
    return {
        "schema_version": SCHEMA,
        "source_targets": {
            "path": str(TARGETS.relative_to(ROOT)),
            "sha256": sha256(target_raw),
            "schema_version": TARGET_SCHEMA,
            "count": len(ids),
            "ordered_instance_ids_sha256": ordered_ids_sha256(ids),
        },
        "registry": {
            "host": REGISTRY,
            "namespace": NAMESPACE,
            "tag": TAG_NAME,
            "platform": "linux/amd64",
            "resolution_protocol": "docker-registry-http-api-v2-read-only",
        },
        "count": len(images),
        "images": images,
    }


def validate_lock(lock: dict[str, Any], target_raw: bytes) -> list[str]:
    errors: list[str] = []

    def exact_keys(value: Any, expected: set[str], label: str) -> bool:
        if not isinstance(value, dict):
            errors.append(f"{label} must be an object")
            return False
        if set(value) != expected:
            errors.append(f"{label} fields mismatch: expected {sorted(expected)}")
            return False
        return True

    try:
        ids = _target_ids(target_raw)
    except LockError as exc:
        return [str(exc)]

    if not exact_keys(lock, TOP_KEYS, "image lock"):
        return errors
    if lock.get("schema_version") != SCHEMA:
        errors.append("image lock schema_version mismatch")
    source = lock.get("source_targets")
    if exact_keys(source, SOURCE_KEYS, "image lock source_targets"):
        expected_source = {
            "path": str(TARGETS.relative_to(ROOT)),
            "sha256": sha256(target_raw),
            "schema_version": TARGET_SCHEMA,
            "count": len(ids),
            "ordered_instance_ids_sha256": ordered_ids_sha256(ids),
        }
        if source != expected_source:
            errors.append("image lock source_targets binding mismatch")
    registry = lock.get("registry")
    if exact_keys(registry, REGISTRY_KEYS, "image lock registry"):
        expected_registry = {
            "host": REGISTRY,
            "namespace": NAMESPACE,
            "tag": TAG_NAME,
            "platform": "linux/amd64",
            "resolution_protocol": "docker-registry-http-api-v2-read-only",
        }
        if registry != expected_registry:
            errors.append("image lock registry policy mismatch")
    if lock.get("count") != len(ids):
        errors.append("image lock count mismatch")
    images = lock.get("images")
    if not isinstance(images, list) or len(images) != len(ids):
        errors.append("image lock images must exactly cover the frozen target count")
        return errors

    seen_refs: set[str] = set()
    for index, (iid, row) in enumerate(zip(ids, images, strict=True)):
        label = f"image lock row {index}"
        if not exact_keys(row, IMAGE_KEYS, label):
            continue
        repository = image_repository(iid)
        tag = image_tag(iid)
        manifest_digest = row.get("manifest_digest")
        tag_digest = row.get("tag_manifest_digest")
        image_id = row.get("image_id")
        reference = row.get("reference")
        if row.get("instance_id") != iid:
            errors.append(f"{label} instance/order mismatch")
        if row.get("tag") != tag:
            errors.append(f"{label} deterministic tag mismatch")
        if not isinstance(tag_digest, str) or not DIGEST_RE.fullmatch(tag_digest):
            errors.append(f"{label} tag manifest digest is invalid")
        if not isinstance(manifest_digest, str) or not DIGEST_RE.fullmatch(manifest_digest):
            errors.append(f"{label} runnable manifest digest is invalid")
        if not isinstance(image_id, str) or not DIGEST_RE.fullmatch(image_id):
            errors.append(f"{label} image ID is invalid")
        if row.get("manifest_media_type") not in MANIFEST_MEDIA_TYPES:
            errors.append(f"{label} runnable manifest media type is invalid")
        expected_ref = (
            f"{repository}@{manifest_digest}"
            if isinstance(manifest_digest, str)
            else None
        )
        if reference != expected_ref or reference == "UNAVAILABLE":
            errors.append(f"{label} immutable reference mismatch")
        if isinstance(reference, str):
            if reference in seen_refs:
                errors.append(f"{label} duplicates an immutable image reference")
            seen_refs.add(reference)
    return errors


def validate_committed_lock_bytes(lock_raw: bytes, target_raw: bytes) -> list[str]:
    """Validate the reviewed lock bytes, including their pinned aggregate digest."""

    errors: list[str] = []
    if sha256(lock_raw) != EXPECTED_LOCK_SHA256:
        errors.append("committed iter202 image lock aggregate sha256 mismatch")
    try:
        lock = load_json_strict(lock_raw, "iter202 image lock")
    except LockError as exc:
        errors.append(str(exc))
        return errors
    errors.extend(validate_lock(lock, target_raw))
    return errors


def render(lock: dict[str, Any]) -> bytes:
    return (json.dumps(lock, indent=2, sort_keys=False) + "\n").encode()


def main() -> int:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true", help="offline lock validation")
    mode.add_argument("--resolve", action="store_true", help="resolve current read-only tags")
    parser.add_argument("--write", action="store_true", help="write the resolved lock")
    parser.add_argument("--timeout", type=float, default=30.0)
    args = parser.parse_args()
    if args.write and not args.resolve:
        parser.error("--write requires --resolve")
    if not TARGETS.is_file():
        print(f"missing frozen iter202 targets: {TARGETS.relative_to(ROOT)}", file=sys.stderr)
        return 2
    target_raw = TARGETS.read_bytes()

    try:
        if args.check:
            if not OUT.is_file():
                raise LockError(f"missing iter202 image lock: {OUT.relative_to(ROOT)}")
            lock_raw = OUT.read_bytes()
            lock = load_json_strict(lock_raw, "iter202 image lock")
            errors = validate_committed_lock_bytes(lock_raw, target_raw)
            if errors:
                for error in errors:
                    print(error, file=sys.stderr)
                return 1
            print(
                "iter202 image lock valid offline: "
                f"{lock['count']} targets, sha256={sha256(lock_raw)}"
            )
            return 0

        lock = build_lock(target_raw, args.timeout)
        errors = validate_lock(lock, target_raw)
        if errors:
            raise LockError("resolved lock failed validation: " + "; ".join(errors))
        payload = render(lock)
        if args.write:
            OUT.parent.mkdir(parents=True, exist_ok=True)
            OUT.write_bytes(payload)
            print(
                f"wrote {len(lock['images'])} immutable images to "
                f"{OUT.relative_to(ROOT)}; sha256={sha256(payload)}"
            )
        else:
            sys.stdout.buffer.write(payload)
        return 0
    except LockError as exc:
        print(f"iter202 image lock error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
