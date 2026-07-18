from astropy.io import fits

try:
    column = fits.Column(
        name="vla",
        format="QD",
        array=[[0.0], [0.0, 0.0], [1.5, 2.5, 3.5]],
    )
    table = fits.BinTableHDU.from_columns([column])
    hdul = fits.HDUList([fits.PrimaryHDU(), table])

    diff = fits.FITSDiff(hdul, hdul)
    assert diff.identical, "self comparison of VLA table differed"

    print(f"RESULT={('PASS',)!r}")
except AssertionError as exc:
    detail = str(exc) or "assertion failed"
    print(f"RESULT={('FAIL', detail)!r}")
except Exception as exc:
    print(f"RESULT={('ERROR', type(exc).__name__)!r}")
