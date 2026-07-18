import xarray as xr

try:
    times = list(range(24))
    stations = ["north", "south"]
    values = [[2 * t, 2 * t + 1] for t in times]
    aux = [[1000 + 10 * t + s for s in range(2)] for t in times]

    ds = xr.Dataset(
        {"T": (("time", "station"), values)},
        coords={
            "time": times,
            "station": stations,
            "day": ("time", [365 * t for t in times]),
            "aux": (("time", "station"), aux),
            "run": "fixture",
        },
    )

    result = ds.coarsen(time=12).construct(time=("year", "month"))

    assert {"time", "station", "day", "aux", "run"} - set(result.coords) == set()
    assert result["day"].dims == ("year", "month")
    assert result["aux"].dims == ("year", "month", "station")
    assert result["run"].dims == ()
    assert result["day"].values.tolist() == [
        [365 * t for t in range(12)],
        [365 * t for t in range(12, 24)],
    ]
    assert result["aux"].values.tolist()[1][11][1] == 1231
    print(f"RESULT={('PASS',)!r}")
except AssertionError:
    print(f"RESULT={('FAIL', 'coordinates were not preserved or reshaped')!r}")
except Exception as exc:
    print(f"RESULT={('ERROR', type(exc).__name__)!r}")
