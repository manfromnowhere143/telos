try:
    import sympy.crypto as crypto

    if hasattr(crypto, "decode_morse"):
        decoder = getattr(crypto, "decode_morse")
    else:
        import sympy.crypto.crypto as crypto_api
        if hasattr(crypto_api, "decode_morse"):
            decoder = getattr(crypto_api, "decode_morse")
        elif hasattr(crypto_api, "decipher_morse"):
            decoder = getattr(crypto_api, "decipher_morse")
        else:
            raise RuntimeError("No public Morse decoder available")

    result = decoder(".----")
except Exception as exc:
    result = ("ERROR", type(exc).__name__)

print(f"RESULT={result!r}")
