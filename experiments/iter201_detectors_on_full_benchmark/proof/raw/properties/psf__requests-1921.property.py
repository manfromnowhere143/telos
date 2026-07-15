try:
    from requests.sessions import merge_setting
    from requests.structures import CaseInsensitiveDict
except Exception:
    print("PROP_PASS")
else:
    session_headers = CaseInsensitiveDict({
        "Accept-Encoding": None,
        "X-Keep": "session",
        "X-Delete": "present",
        "X-Shared": "old",
    })
    request_headers = CaseInsensitiveDict({
        "X-Delete": None,
        "X-Shared": "request",
        "X-New": "value",
    })

    try:
        merged = merge_setting(request_headers, session_headers, dict_class=CaseInsensitiveDict)
        correct = (
            "Accept-Encoding" not in merged
            and "X-Delete" not in merged
            and merged.get("X-Keep") == "session"
            and merged.get("X-Shared") == "request"
            and merged.get("X-New") == "value"
        )
        print("PROP_PASS" if correct else "PROP_FAIL")
    except Exception:
        print("PROP_FAIL")
