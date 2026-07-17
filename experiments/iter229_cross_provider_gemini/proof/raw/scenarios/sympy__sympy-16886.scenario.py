from sympy.crypto.crypto import (
    encipher_kid_rsa,
    decipher_kid_rsa,
    kid_rsa_private_key,
    kid_rsa_public_key,
)

parameters = (2, 1000000007, 1, 1)
public_key = kid_rsa_public_key(*parameters)
private_key = kid_rsa_private_key(*parameters)

ciphertext = encipher_kid_rsa("1", public_key)
result = decipher_kid_rsa(ciphertext, private_key)

print("RESULT=" + repr(result))
