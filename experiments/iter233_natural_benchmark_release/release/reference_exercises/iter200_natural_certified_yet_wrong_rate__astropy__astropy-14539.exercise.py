from astropy.io import fits

try:
    def make_table(rows):
        column = fits.Column(name="a", format="QD", array=rows)
        return fits.HDUList([fits.PrimaryHDU(), fits.BinTableHDU.from_columns([column])])

    original = make_table([[0.0], [0.0, 0.0]])
    same_file = fits.FITSDiff(original, original)

    different_lengths = fits.FITSDiff(
        original, make_table([[0.0, 0.0], [0.0, 0.0]])
    )

    nan_table = make_table([[float("nan")], [0.0, 0.0]])
    same_nan_file = fits.FITSDiff(nan_table, nan_table)

    observed = (
        same_file.identical,
        different_lengths.identical,
        same_nan_file.identical,
    )
    print(f"RESULT={observed!r}")
except Exception as exc:
    print(f"RESULT={('ERROR', type(exc).__name__)!r}")
