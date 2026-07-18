import xarray as xr

try:
    ds = xr.Dataset(
        data_vars={
            "T": (
                ("time", "station"),
                [[0, 1], [2, 3], [4, 5], [6, 7]],
            )
        },
        coords={
            "day": ("time", [100, 101, 102, 103]),
            "quality": (
                ("time", "station"),
                [[10, 11], [12, 13], [14, 15], [16, 17]],
            ),
            "station": ("station", ["north", "south"]),
            "run": "fixture",
        },
    )

    before_coords = set(ds.coords)
    result = ds.coarsen(time=2).construct(time=("year", "month"))

    assert before_coords.issubset(set(result.coords)), "coordinate was demoted"
    assert not before_coords.intersection(set(result.data_vars)), "coordinate became data variable"
    assert result["day"].dims == ("year", "month"), "1D auxiliary coordinate dims"
    assert result["quality"].dims == ("year", "month", "station"), "2D auxiliary coordinate dims"
    assert result["day"].values.tolist() == [[100, 101], [102, 103]], "day values"
    assert result["quality"].values.tolist() == [
        [[10, 11], [12, 13]],
        [[14, 15], [16, 17]],
    ], "quality values"
    assert result["run"].item() == "fixture", "scalar coordinate"

    print(f"RESULT={('PASS',)!r}")
except AssertionError as exc:
    print(f"RESULT={('FAIL', str(exc) or 'assertion')!r}")
except Exception as exc:
    print(f"RESULT={('ERROR', type(exc).__name__)!r}")
