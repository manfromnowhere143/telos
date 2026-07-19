#!/usr/bin/env python3
"""Reject bit-exact comparisons of libm-derived evidence across active Python code.

The validator covers both historical failure shapes:

* iter219 assigned a Wilson interval and later compared it to a stored JSON field
  with ``==``;
* iter236 serialized a result containing ``sqrt``/``erfc`` outputs and compared the
  complete artifact text with ``!=``.

The scan is deliberately structural.  It follows simple assignment taint and the
local call graph, and it scans every Python file under ``scripts/`` and ``telos/``
instead of naming either historical guard.
"""

from __future__ import annotations

import ast
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ACTIVE_SOURCE_DIRS = ("scripts", "telos")

# CPython delegates these transcendental operations to the platform math library.
# Exact integer operations such as comb(), and comparison helpers such as isclose(),
# are intentionally absent.
LIBM_FUNCTIONS = frozenset(
    {
        "acos",
        "acosh",
        "asin",
        "asinh",
        "atan",
        "atan2",
        "atanh",
        "cbrt",
        "cos",
        "cosh",
        "erf",
        "erfc",
        "exp",
        "exp2",
        "expm1",
        "gamma",
        "hypot",
        "lgamma",
        "log",
        "log10",
        "log1p",
        "log2",
        "pow",
        "sin",
        "sinh",
        "sqrt",
        "tan",
        "tanh",
    }
)
WILSON_FUNCTIONS = frozenset({"wilson", "wilson_interval"})
NORMAL_DIST_METHODS = frozenset({"cdf", "inv_cdf", "overlap", "pdf"})
ARTIFACT_READ_METHODS = frozenset({"read", "read_bytes", "read_text"})
TOLERANT_COMPARISON_CALLS = frozenset(
    {"allclose", "compare_json", "intervals_match", "isclose"}
)
EXACT_OPERATORS = (ast.Eq, ast.NotEq)
Scope = ast.Module | ast.FunctionDef | ast.AsyncFunctionDef


@dataclass(frozen=True, order=True)
class Violation:
    """One exact-comparison violation found in a Python source file."""

    path: str
    line: int
    code: str
    detail: str

    def render(self) -> str:
        return f"{self.path}:{self.line}: {self.code} {self.detail}"


@dataclass(frozen=True)
class ImportAliases:
    """Aliases needed to recognize libm calls after import renaming."""

    math_modules: frozenset[str]
    risky_callables: frozenset[str]
    statistics_modules: frozenset[str]
    normal_dist_classes: frozenset[str]


def _dotted_name(node: ast.expr) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        prefix = _dotted_name(node.value)
        return f"{prefix}.{node.attr}" if prefix else node.attr
    return None


def _call_leaf(call: ast.Call) -> str | None:
    name = _dotted_name(call.func)
    return name.rsplit(".", 1)[-1] if name else None


def _import_aliases(tree: ast.AST) -> ImportAliases:
    math_modules = {"math"}
    risky_callables = set(WILSON_FUNCTIONS)
    statistics_modules = {"statistics"}
    normal_dist_classes = {"NormalDist"}

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                bound = alias.asname or alias.name.split(".", 1)[0]
                if alias.name == "math":
                    math_modules.add(bound)
                elif alias.name == "statistics":
                    statistics_modules.add(bound)
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            for alias in node.names:
                bound = alias.asname or alias.name
                if module == "math" and alias.name in LIBM_FUNCTIONS:
                    risky_callables.add(bound)
                elif module == "statistics" and alias.name == "NormalDist":
                    normal_dist_classes.add(bound)
                elif alias.name in WILSON_FUNCTIONS:
                    risky_callables.add(bound)

    return ImportAliases(
        math_modules=frozenset(math_modules),
        risky_callables=frozenset(risky_callables),
        statistics_modules=frozenset(statistics_modules),
        normal_dist_classes=frozenset(normal_dist_classes),
    )


def _is_direct_libm_call(call: ast.Call, aliases: ImportAliases) -> bool:
    name = _dotted_name(call.func)
    leaf = _call_leaf(call)
    if name is None or leaf is None:
        # ``NormalDist().inv_cdf(...)`` has a call, rather than a dotted name,
        # as the Attribute base.
        return isinstance(call.func, ast.Attribute) and call.func.attr in NORMAL_DIST_METHODS
    if name in aliases.risky_callables or leaf in WILSON_FUNCTIONS:
        return True
    if "." in name:
        first = name.split(".", 1)[0]
        if first in aliases.math_modules and leaf in LIBM_FUNCTIONS:
            return True
        if first in aliases.statistics_modules and leaf in NORMAL_DIST_METHODS:
            return True
    return leaf in aliases.normal_dist_classes


def _local_function_risk(
    tree: ast.AST,
    aliases: ImportAliases,
) -> frozenset[str]:
    functions = {
        node.name: node
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }
    risky = {
        name
        for name, function in functions.items()
        if any(
            _is_direct_libm_call(node, aliases)
            for node in ast.walk(function)
            if isinstance(node, ast.Call)
        )
    }

    changed = True
    while changed:
        changed = False
        for name, function in functions.items():
            if name in risky:
                continue
            if any(
                _call_leaf(node) in risky
                for node in ast.walk(function)
                if isinstance(node, ast.Call)
            ):
                risky.add(name)
                changed = True
    return frozenset(risky)


def _parents(tree: ast.AST) -> dict[ast.AST, ast.AST]:
    return {
        child: parent
        for parent in ast.walk(tree)
        for child in ast.iter_child_nodes(parent)
    }


def _scope_for(node: ast.AST, tree: ast.Module, parents: dict[ast.AST, ast.AST]) -> Scope:
    current = node
    while current in parents:
        current = parents[current]
        if isinstance(current, (ast.FunctionDef, ast.AsyncFunctionDef)):
            return current
    return tree


def _assigned_names(target: ast.expr) -> set[str]:
    if isinstance(target, ast.Name):
        return {target.id}
    if isinstance(target, (ast.List, ast.Tuple)):
        return set().union(*(_assigned_names(item) for item in target.elts))
    return set()


def _unshielded_walk(expression: ast.AST) -> Iterator[ast.AST]:
    """Walk an expression without tainting the result of an approved comparator."""

    stack = [expression]
    while stack:
        node = stack.pop()
        yield node
        if isinstance(node, ast.Call) and _call_leaf(node) in TOLERANT_COMPARISON_CALLS:
            continue
        stack.extend(ast.iter_child_nodes(node))


def _expression_is_tainted(
    expression: ast.AST,
    *,
    aliases: ImportAliases,
    risky_functions: frozenset[str],
    tainted_names: set[str],
) -> bool:
    for node in _unshielded_walk(expression):
        if isinstance(node, ast.Name) and node.id in tainted_names:
            return True
        if isinstance(node, ast.Call) and (
            _is_direct_libm_call(node, aliases) or _call_leaf(node) in risky_functions
        ):
            return True
    return False


def _scopes_and_assignments(
    tree: ast.Module,
    parents: dict[ast.AST, ast.AST],
) -> tuple[list[Scope], dict[Scope, list[tuple[set[str], ast.AST]]]]:
    scopes: list[Scope] = [
        tree,
        *[
            node
            for node in ast.walk(tree)
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        ],
    ]
    assignments: dict[Scope, list[tuple[set[str], ast.AST]]] = {
        scope: [] for scope in scopes
    }

    for node in ast.walk(tree):
        targets: set[str] = set()
        value: ast.AST | None = None
        if isinstance(node, ast.Assign):
            targets = set().union(*(_assigned_names(target) for target in node.targets))
            value = node.value
        elif isinstance(node, ast.AnnAssign):
            targets = _assigned_names(node.target)
            value = node.value
        elif isinstance(node, ast.NamedExpr):
            targets = _assigned_names(node.target)
            value = node.value
        if targets and value is not None:
            assignments[_scope_for(node, tree, parents)].append((targets, value))
    return scopes, assignments


def _scope_taint(
    tree: ast.Module,
    parents: dict[ast.AST, ast.AST],
    aliases: ImportAliases,
    risky_functions: frozenset[str],
) -> dict[Scope, set[str]]:
    scopes, assignments = _scopes_and_assignments(tree, parents)

    taint_by_scope: dict[Scope, set[str]] = {}
    module_taint: set[str] = set()
    for scope in scopes:
        tainted = set(module_taint) if scope is not tree else set()
        changed = True
        while changed:
            changed = False
            for targets, value in assignments[scope]:
                if targets <= tainted:
                    continue
                if _expression_is_tainted(
                    value,
                    aliases=aliases,
                    risky_functions=risky_functions,
                    tainted_names=tainted,
                ):
                    tainted.update(targets)
                    changed = True
        taint_by_scope[scope] = tainted
        if scope is tree:
            module_taint = tainted
    return taint_by_scope


def _contains_artifact_read(expression: ast.AST) -> bool:
    return any(
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr in ARTIFACT_READ_METHODS
        for node in _unshielded_walk(expression)
    )


def _argument_names(scope: Scope) -> set[str]:
    if isinstance(scope, ast.Module):
        return set()
    arguments = scope.args
    names = {
        argument.arg
        for argument in [
            *arguments.posonlyargs,
            *arguments.args,
            *arguments.kwonlyargs,
        ]
    }
    if arguments.vararg is not None:
        names.add(arguments.vararg.arg)
    if arguments.kwarg is not None:
        names.add(arguments.kwarg.arg)
    return names


def _expression_is_external(expression: ast.AST, external_names: set[str]) -> bool:
    return _contains_artifact_read(expression) or any(
        isinstance(node, ast.Name) and node.id in external_names
        for node in _unshielded_walk(expression)
    )


def _scope_external_taint(
    tree: ast.Module,
    parents: dict[ast.AST, ast.AST],
) -> dict[Scope, set[str]]:
    """Track values read from artifacts or supplied to a validation function."""

    scopes, assignments = _scopes_and_assignments(tree, parents)
    external_by_scope: dict[Scope, set[str]] = {}
    module_external: set[str] = set()
    for scope in scopes:
        external = set(module_external) | _argument_names(scope)
        changed = True
        while changed:
            changed = False
            for targets, value in assignments[scope]:
                if targets <= external:
                    continue
                if _expression_is_external(value, external):
                    external.update(targets)
                    changed = True
        external_by_scope[scope] = external
        if scope is tree:
            module_external = external
    return external_by_scope


def scan_source(source: str, *, path: str = "<memory>") -> list[Violation]:
    """Return exact-comparison violations in one Python source string."""

    try:
        tree = ast.parse(source, filename=path)
    except SyntaxError as exc:
        return [
            Violation(
                path=path,
                line=exc.lineno or 1,
                code="LIBM000",
                detail=f"source could not be parsed: {exc.msg}",
            )
        ]

    aliases = _import_aliases(tree)
    risky_functions = _local_function_risk(tree, aliases)
    parents = _parents(tree)
    taint_by_scope = _scope_taint(tree, parents, aliases, risky_functions)
    external_by_scope = _scope_external_taint(tree, parents)

    lines = source.splitlines()
    violations: list[Violation] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Compare):
            continue
        expressions = [node.left, *node.comparators]
        scope = _scope_for(node, tree, parents)
        tainted_names = taint_by_scope[scope]
        external_names = external_by_scope[scope]
        offending_pairs: list[tuple[ast.expr, ast.expr]] = []
        for index, operator in enumerate(node.ops):
            if not isinstance(operator, EXACT_OPERATORS):
                continue
            left, right = expressions[index : index + 2]
            left_libm = _expression_is_tainted(
                left,
                aliases=aliases,
                risky_functions=risky_functions,
                tainted_names=tainted_names,
            )
            right_libm = _expression_is_tainted(
                right,
                aliases=aliases,
                risky_functions=risky_functions,
                tainted_names=tainted_names,
            )
            left_external = _expression_is_external(left, external_names)
            right_external = _expression_is_external(right, external_names)
            if (left_libm and right_external) or (right_libm and left_external):
                offending_pairs.append((left, right))
        if not offending_pairs:
            continue

        source_line = lines[node.lineno - 1].strip() if node.lineno <= len(lines) else ""
        artifact_read = any(
            _contains_artifact_read(expression)
            for pair in offending_pairs
            for expression in pair
        )
        if artifact_read:
            code = "LIBM002"
            detail = (
                "bit-exact artifact comparison against a libm-derived value: "
                f"{source_line}"
            )
        else:
            code = "LIBM001"
            detail = (
                "bit-exact stored/external comparison against a libm-derived value: "
                f"{source_line}"
            )
        violations.append(
            Violation(
                path=path,
                line=node.lineno,
                code=code,
                detail=detail,
            )
        )
    return sorted(violations)


def active_python_paths(root: Path = ROOT) -> list[Path]:
    """Return every active Python implementation/guard path in deterministic order."""

    return sorted(
        path
        for directory in ACTIVE_SOURCE_DIRS
        for path in (root / directory).rglob("*.py")
        if "__pycache__" not in path.parts
    )


def scan_repository(root: Path = ROOT) -> list[Violation]:
    """Scan every active Python file below ``root``."""

    violations: list[Violation] = []
    for path in active_python_paths(root):
        relative = path.relative_to(root).as_posix()
        violations.extend(
            scan_source(path.read_text(encoding="utf-8"), path=relative)
        )
    return sorted(violations)


def main() -> int:
    paths = active_python_paths(ROOT)
    violations = scan_repository(ROOT)
    if violations:
        print("repository-wide libm artifact comparison guard: FAIL")
        for violation in violations:
            print(f"  {violation.render()}")
        return 1
    print(
        "repository-wide libm artifact comparison guard: "
        f"PASS ({len(paths)} active Python files)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
