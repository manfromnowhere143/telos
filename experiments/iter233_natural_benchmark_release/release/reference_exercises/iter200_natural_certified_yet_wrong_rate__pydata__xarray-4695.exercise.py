import xarray as xr

try:
    results = []
    for dim in ("dim2", "method", "tolerance", "drop"):
        array = xr.DataArray(
            [[0, 1], [2, 3]],
            dims=("dim1", dim),
            coords={"dim1": ["x", "y"], dim: ["a", "b"]},
        )
        selected = array.loc[{"dim1": "x", dim: "a"}]
        results.append((dim, selected.item(), selected.dims))
    print("RESULT=" + repr(tuple(results)))
except Exception as exc:
    print("RESULT=" + repr(("ERROR", type(exc).__name__)))
