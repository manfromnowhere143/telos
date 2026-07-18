try:
    import sympy.crypto.crypto as crypto

    if not (hasattr(crypto, "encipher_kid_rsa") and
            hasattr(crypto, "decipher_kid_rsa")):
        raise AttributeError("KID RSA API unavailable")

    if (hasattr(crypto, "kid_rsa_public_key") and
            hasattr(crypto, "kid_rsa_private_key")):
        public_key = crypto.kid_rsa_public_key(3, 5, 7, 11)
        private_key = crypto.kid_rsa_private_key(3, 5, 7, 11)
    else:
        public_key = (1147, 101)
        private_key = (1147, 159)

    encrypted = crypto.encipher_kid_rsa("1", public_key)
    result = crypto.decipher_kid_rsa(encrypted, private_key)
    print(f"RESULT={result!r}")
except BaseException as exc:
    print(f"RESULT={('ERROR', type(exc).__name__)!r}")
