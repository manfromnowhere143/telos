try:
    from astropy.io import fits

    # Build HDUs with VLA columns in memory (no filesystem)
    def make_hdu():
        col = fits.Column('a', format='QD', array=[[0], [0, 0]])
        return fits.BinTableHDU.from_columns([col])

    hdu1 = make_hdu()
    hdu2 = make_hdu()

    hdl1 = fits.HDUList([fits.PrimaryHDU(), hdu1])
    hdl2 = fits.HDUList([fits.PrimaryHDU(), hdu2])

    diff = fits.FITSDiff(hdl1, hdl2)
    if not diff.identical:
        print(f"RESULT={('FAIL', 'identical VLA HDULists reported as different')!r}")
    else:
        # also test comparing to itself
        diff_self = fits.FITSDiff(hdl1, hdl1)
        if not diff_self.identical:
            print(f"RESULT={('FAIL', 'self-comparison reported different')!r}")
        else:
            # Verify genuine differences are still detected
            col_diff = fits.Column('a', format='QD', array=[[1], [0, 0]])
            hdu3 = fits.BinTableHDU.from_columns([col_diff])
            hdl3 = fits.HDUList([fits.PrimaryHDU(), hdu3])
            diff_real = fits.FITSDiff(hdl1, hdl3)
            if diff_real.identical:
                print(f"RESULT={('FAIL', 'real VLA difference not detected')!r}")
            else:
                print(f"RESULT={('PASS',)!r}")
except Exception as exc:
    print(f"RESULT={('ERROR', type(exc).__name__)!r}")
