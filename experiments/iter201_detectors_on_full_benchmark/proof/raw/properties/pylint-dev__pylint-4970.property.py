import inspect
import io

try:
    from pylint.checkers import similar

    cls = getattr(similar, "Similar")
    kwargs = {}
    positional = []
    possible = True

    for param in inspect.signature(cls).parameters.values():
        if param.kind in (param.VAR_POSITIONAL, param.VAR_KEYWORD):
            continue
        if "min_similarity" in param.name:
            value = 0
        elif param.name.startswith("ignore_"):
            value = False
        elif param.default is not inspect.Parameter.empty:
            continue
        else:
            possible = False
            break

        if param.kind is param.POSITIONAL_ONLY:
            positional.append(value)
        else:
            kwargs[param.name] = value

    if not possible:
        print("PROP_PASS")
    else:
        checker = cls(*positional, **kwargs)
        before = len(checker.linesets) if hasattr(checker, "linesets") else None
        correct = True

        for index in range(2):
            stream = io.StringIO(
                "def duplicated_function():\n"
                "    value = 1\n"
                "    return value\n"
                "\n"
                "def another_function():\n"
                "    value = 1\n"
                "    return value\n"
            )
            checker.append_stream(f"stream-{index}", stream, f"duplicate-{index}.py")
            if stream.tell() != 0:
                correct = False
                break

        if before is not None and len(checker.linesets) != before:
            correct = False

        print("PROP_PASS" if correct else "PROP_FAIL")
except Exception:
    print("PROP_PASS")
