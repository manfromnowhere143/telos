def main():
    try:
        from sympy.crypto.crypto import encode_morse, decode_morse

        # 1. Check that "1" encodes to ".----"
        enc_1 = encode_morse('1')
        if enc_1 != '.----':
            print(f"RESULT={('FAIL', f'encode_morse(1) returned {enc_1}')!r}")
            return

        # 2. Check that ".----" decodes to "1"
        dec_1 = decode_morse('.----')
        if dec_1 != '1':
            print(f"RESULT={('FAIL', f'decode_morse(.----) returned {dec_1}')!r}")
            return

        # 3. Verify that the old incorrect mapping is no longer present
        try:
            bad_dec = decode_morse('----')
            if bad_dec == '1':
                print(f"RESULT={('FAIL', 'decode_morse(----) still evaluates to 1')!r}")
                return
        except Exception:
            # It's okay if decoding an invalid/removed sequence raises an error
            pass

        # 4. Check an alphanumeric string consequence to ensure it integrates well
        msg = "A1"
        enc_msg = encode_morse(msg)
        dec_msg = decode_morse(enc_msg)
        if dec_msg != "A1":
            print(f"RESULT={('FAIL', f'Round-trip A1 resulted in {dec_msg}')!r}")
            return

        print(f"RESULT={('PASS',)!r}")
    except Exception as e:
        print(f"RESULT={('ERROR', type(e).__name__)!r}")

if __name__ == "__main__":
    main()
