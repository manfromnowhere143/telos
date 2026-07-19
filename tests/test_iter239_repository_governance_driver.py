"""Adversarial tests for iter239's bounded GitHub governance driver."""

from __future__ import annotations

from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]


def load_driver():
    path = ROOT / "scripts/configure_repository_governance.py"
    spec = importlib.util.spec_from_file_location(
        "configure_repository_governance",
        path,
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class FakeTransport:
    def __init__(self, responses) -> None:
        self.responses = list(responses)
        self.calls: list[tuple[str, str, dict[str, str], bytes | None, int]] = []

    def __call__(self, method, target, headers, body, timeout):
        self.calls.append((method, target, dict(headers), body, timeout))
        response = self.responses.pop(0)
        if isinstance(response, BaseException):
            raise response
        return response


def response(driver, status: int, value) -> object:
    raw = b"" if value is None else json.dumps(value).encode()
    return driver.RawResponse(status, {}, raw)


def test_strict_server_json_rejects_duplicates_and_nonfinite() -> None:
    driver = load_driver()
    with pytest.raises(driver.GovernanceMutationError, match="duplicate JSON"):
        driver.strict_json_document(b'{"a":1,"a":2}', label="duplicate")
    for token in (b"NaN", b"Infinity", b"-Infinity"):
        with pytest.raises(
            driver.GovernanceMutationError,
            match="non-finite",
        ):
            driver.strict_json_document(
                b'{"value":' + token + b"}",
                label="nonfinite",
            )


@pytest.mark.parametrize(
    "target",
    [
        "https://api.github.com/repos/manfromnowhere143/telos/rulesets",
        "//api.github.com/repos/manfromnowhere143/telos/rulesets",
        "/repos/other/telos/rulesets",
        "/repos/manfromnowhere143/telos/../other",
        "/repos/manfromnowhere143/telos//rulesets",
        "/repos/manfromnowhere143/telos/rulesets#fragment",
    ],
)
def test_target_validation_rejects_cross_origin_and_noncanonical(
    target: str,
) -> None:
    driver = load_driver()
    with pytest.raises(driver.GovernanceMutationError):
        driver._validate_api_target(target)


def test_exact_repository_api_target_is_allowed() -> None:
    driver = load_driver()
    driver._validate_api_target(
        "/repos/manfromnowhere143/telos"
    )


def test_read_only_client_rejects_every_write() -> None:
    driver = load_driver()
    transport = FakeTransport([])
    client = driver.GitHubClient(
        token="token",
        request_function=transport,
        allow_post=False,
    )
    for method in ("POST", "PATCH", "PUT", "DELETE"):
        with pytest.raises(driver.GovernanceMutationError):
            client.request(
                method,
                "/repos/manfromnowhere143/telos/rulesets",
                document=(
                    driver.guard.EXPECTED_REQUEST_BODY
                    if method == "POST"
                    else None
                ),
            )
    assert transport.calls == []
    assert all(value == 0 for value in client.counts.values())


def test_mutation_client_allows_only_exact_one_post() -> None:
    driver = load_driver()
    created = {
        "id": 239,
        "name": driver.guard.RULESET_NAME,
    }
    transport = FakeTransport([response(driver, 201, created)])
    client = driver.GitHubClient(
        token="token",
        request_function=transport,
        allow_post=True,
    )
    status, parsed, _raw = client.post_ruleset(
        deepcopy(driver.guard.EXPECTED_REQUEST_BODY)
    )
    assert status == 201
    assert parsed == created
    assert client.counts["POST"] == 1
    with pytest.raises(driver.GovernanceMutationError, match="second POST"):
        client.post_ruleset(deepcopy(driver.guard.EXPECTED_REQUEST_BODY))
    assert len(transport.calls) == 1


def test_post_rejects_wrong_endpoint_body_query_and_redirect() -> None:
    driver = load_driver()
    client = driver.GitHubClient(
        token="token",
        request_function=FakeTransport([]),
        allow_post=True,
    )
    wrong = deepcopy(driver.guard.EXPECTED_REQUEST_BODY)
    wrong["enforcement"] = "evaluate"
    with pytest.raises(driver.GovernanceMutationError, match="body differs"):
        client.post_ruleset(wrong)
    type_mutated = deepcopy(driver.guard.EXPECTED_REQUEST_BODY)
    type_mutated["rules"][2]["parameters"][
        "required_approving_review_count"
    ] = False
    with pytest.raises(driver.GovernanceMutationError, match="body differs"):
        client.post_ruleset(type_mutated)
    with pytest.raises(driver.GovernanceMutationError, match="endpoint differs"):
        client.request(
            "POST",
            "/repos/manfromnowhere143/telos/branches",
            document=deepcopy(driver.guard.EXPECTED_REQUEST_BODY),
            expected_statuses=(201,),
        )
    with pytest.raises(driver.GovernanceMutationError, match="cannot use a query"):
        client.request(
            "POST",
            "/repos/manfromnowhere143/telos/rulesets",
            parameters={"page": 1},
            document=deepcopy(driver.guard.EXPECTED_REQUEST_BODY),
            expected_statuses=(201,),
        )
    assert client.counts["POST"] == 0

    transport = FakeTransport([response(driver, 302, {"moved": True})])
    client = driver.GitHubClient(
        token="token",
        request_function=transport,
        allow_post=True,
    )
    with pytest.raises(driver.AmbiguousPostError, match="redirect"):
        client.post_ruleset(deepcopy(driver.guard.EXPECTED_REQUEST_BODY))
    assert client.counts["POST"] == 1


def test_post_transport_failure_is_ambiguous_and_never_retried() -> None:
    driver = load_driver()
    transport = FakeTransport([TimeoutError("secret detail")])
    client = driver.GitHubClient(
        token="token",
        request_function=transport,
        allow_post=True,
    )
    with pytest.raises(driver.AmbiguousPostError) as captured:
        client.post_ruleset(deepcopy(driver.guard.EXPECTED_REQUEST_BODY))
    assert "secret detail" not in str(captured.value)
    assert len(transport.calls) == 1
    assert client.counts["POST"] == 1
    with pytest.raises(driver.GovernanceMutationError, match="second POST"):
        client.post_ruleset(deepcopy(driver.guard.EXPECTED_REQUEST_BODY))


@pytest.mark.parametrize(
    ("status", "raw"),
    [
        (201, b""),
        (201, b'{"id":1,"id":2}'),
        (201, b"{"),
        (200, b'{"id":1}'),
        (202, b'{"id":1}'),
        (408, b'{"message":"timeout"}'),
        (429, b'{"message":"limited"}'),
        (500, b'{"message":"failure"}'),
    ],
)
def test_every_nonexact_post_response_is_ambiguous(
    status: int,
    raw: bytes,
) -> None:
    driver = load_driver()
    transport = FakeTransport([driver.RawResponse(status, {}, raw)])
    client = driver.GitHubClient(
        token="token",
        request_function=transport,
        allow_post=True,
    )
    with pytest.raises(driver.AmbiguousPostError) as captured:
        client.post_ruleset(deepcopy(driver.guard.EXPECTED_REQUEST_BODY))
    assert captured.value.http_status == status
    assert len(transport.calls) == 1
    assert client.counts["POST"] == 1
    with pytest.raises(driver.GovernanceMutationError, match="second POST"):
        client.post_ruleset(deepcopy(driver.guard.EXPECTED_REQUEST_BODY))


def test_get_budget_refuses_before_transport() -> None:
    driver = load_driver()
    transport = FakeTransport(
        [
            response(driver, 200, {"ok": True}),
            response(driver, 200, {"should": "remain unused"}),
        ]
    )
    budgets = dict(driver.TRANSACTION_METHOD_BUDGETS)
    budgets["GET"] = 1
    client = driver.GitHubClient(
        token="token",
        request_function=transport,
        allow_post=False,
        method_budgets=budgets,
    )
    client.get("/repos/manfromnowhere143/telos/branches/master")
    with pytest.raises(driver.GovernanceMutationError, match="budget is exhausted"):
        client.get("/repos/manfromnowhere143/telos/rulesets")
    assert len(transport.calls) == 1
    assert client.counts["GET"] == 1


def test_get_rejects_redirect_without_following() -> None:
    driver = load_driver()
    transport = FakeTransport([response(driver, 301, None)])
    client = driver.GitHubClient(
        token="token",
        request_function=transport,
        allow_post=False,
    )
    with pytest.raises(driver.GovernanceMutationError, match="redirect"):
        client.get("/repos/manfromnowhere143/telos/rulesets")
    assert len(transport.calls) == 1


def test_headers_pin_api_and_do_not_put_token_in_target() -> None:
    driver = load_driver()
    transport = FakeTransport([response(driver, 200, [])])
    client = driver.GitHubClient(
        token="top-secret-token",
        request_function=transport,
        allow_post=False,
    )
    status, value = client.get(
        "/repos/manfromnowhere143/telos/rulesets",
        parameters={"per_page": 100, "page": 1},
    )
    assert status == 200
    assert value == []
    method, target, headers, body, timeout = transport.calls[0]
    assert method == "GET"
    assert target.endswith("?page=1&per_page=100")
    assert "top-secret-token" not in target
    assert headers["Authorization"] == "Bearer top-secret-token"
    assert headers["X-GitHub-Api-Version"] == driver.guard.API_VERSION
    assert body is None
    assert timeout == driver.TIMEOUT_SECONDS


def test_paginated_get_follows_validated_link_and_rejects_duplicates() -> None:
    driver = load_driver()
    path = "/repos/manfromnowhere143/telos/rulesets"
    next_url = (
        "https://api.github.com"
        f"{path}?page=2&per_page=100"
    )
    transport = FakeTransport(
        [
            driver.RawResponse(
                200,
                {"link": f'<{next_url}>; rel="next"'},
                b'[{"id":1}]',
            ),
            driver.RawResponse(200, {}, b'[{"id":2}]'),
        ]
    )
    client = driver.GitHubClient(
        token="token",
        request_function=transport,
        allow_post=False,
    )
    values, trace = driver.get_paginated(
        client,
        path,
        identity=lambda row: row["id"],
    )
    assert values == [{"id": 1}, {"id": 2}]
    assert trace.http_statuses == [200, 200]
    assert trace.page_count == 2

    duplicate_transport = FakeTransport(
        [
            driver.RawResponse(
                200,
                {"link": f'<{next_url}>; rel="next"'},
                b'[{"id":1}]',
            ),
            driver.RawResponse(200, {}, b'[{"id":1}]'),
        ]
    )
    duplicate_client = driver.GitHubClient(
        token="token",
        request_function=duplicate_transport,
        allow_post=False,
    )
    with pytest.raises(driver.GovernanceMutationError, match="duplicate"):
        driver.get_paginated(
            duplicate_client,
            path,
            identity=lambda row: row["id"],
        )


def test_paginated_get_rejects_ambiguous_or_contradictory_terminal_page() -> None:
    driver = load_driver()
    path = "/repos/manfromnowhere143/telos/rulesets"
    full_page = json.dumps(
        [{"id": index} for index in range(100)]
    ).encode()
    client = driver.GitHubClient(
        token="token",
        request_function=FakeTransport(
            [driver.RawResponse(200, {}, full_page)]
        ),
        allow_post=False,
    )
    with pytest.raises(driver.GovernanceMutationError, match="ambiguous"):
        driver.get_paginated(
            client,
            path,
            identity=lambda row: row["id"],
        )

    last_url = (
        "https://api.github.com"
        f"{path}?page=2&per_page=100"
    )
    contradictory = driver.GitHubClient(
        token="token",
        request_function=FakeTransport(
            [
                driver.RawResponse(
                    200,
                    {"link": f'<{last_url}>; rel="last"'},
                    b"[]",
                )
            ]
        ),
        allow_post=False,
    )
    with pytest.raises(driver.GovernanceMutationError, match="omits"):
        driver.get_paginated(
            contradictory,
            path,
            identity=lambda row: row["id"],
        )


def test_capture_checks_rejects_extra_same_event_run_without_jobs() -> None:
    driver = load_driver()
    head = "a" * 40
    workflow_runs = [
        {
            "check_suite_id": 100 + index,
            "event": "pull_request",
            "head_sha": head,
            "id": 200 + index,
            "path": driver.guard.WORKFLOW_RELATIVE.as_posix(),
            "run_attempt": 1,
            "workflow_id": driver.guard.WORKFLOW_ID,
        }
        for index in range(2)
    ]
    transport = FakeTransport(
        [
            response(
                driver,
                200,
                {
                    "total_count": 2,
                    "workflow_runs": workflow_runs,
                },
            )
        ]
    )
    client = driver.GitHubClient(
        token="token",
        request_function=transport,
        allow_post=False,
    )
    with pytest.raises(driver.GovernanceMutationError, match="exactly one"):
        driver.capture_checks(
            client,
            source_commit=head,
            include_push=False,
        )
    assert len(transport.calls) == 1


def test_materialize_once_is_canonical_fsynced_and_no_overwrite(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    driver = load_driver()
    monkeypatch.setattr(driver, "ROOT", tmp_path)
    destination = tmp_path / "proof/evidence.json"
    document = {"z": 2, "a": 1}
    fsync_targets: list[int] = []
    real_fsync = driver.os.fsync

    def capture_fsync(descriptor: int) -> None:
        fsync_targets.append(descriptor)
        real_fsync(descriptor)

    monkeypatch.setattr(driver.os, "fsync", capture_fsync)
    raw = driver.materialize_once(destination, document)
    assert raw == driver.guard.canonical_json_bytes(document)
    assert destination.read_bytes() == raw
    assert destination.stat().st_mode & 0o777 == 0o644
    assert len(fsync_targets) == 2
    with pytest.raises(driver.GovernanceMutationError, match="overwrite"):
        driver.materialize_once(destination, document)


def test_materialize_once_rejects_symlink_parent(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    driver = load_driver()
    outside = tmp_path / "outside"
    outside.mkdir()
    (tmp_path / "proof").symlink_to(outside, target_is_directory=True)
    monkeypatch.setattr(driver, "ROOT", tmp_path)
    with pytest.raises(driver.GovernanceMutationError, match="symlink"):
        driver.materialize_once(tmp_path / "proof/evidence.json", {"a": 1})


def test_receipt_counts_include_exact_zero_semantic_mutations() -> None:
    driver = load_driver()
    transport = FakeTransport([response(driver, 200, {})])
    client = driver.GitHubClient(
        token="token",
        request_function=transport,
        allow_post=False,
    )
    client.get("/repos/manfromnowhere143/telos/branches/master")
    counts = client.receipt_counts()
    assert counts["GET"] == 1
    assert counts["POST"] == 0
    for operation in driver.guard.SEMANTIC_MUTATIONS:
        assert counts[operation] == 0
