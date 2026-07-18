import xarray as xr

def run_test():
    # Initialize using a standard Python list; xarray handles the internal array conversion.
    da = xr.DataArray(list(range(24)), dims=["time"])
    # Scalar multiplication operates on the underlying array
    da = da.assign_coords(day=365 * da)
    ds = da.to_dataset(name="T")

    # Perform the coarsening construct on the Dataset
    res_ds = ds.coarsen(time=12).construct(time=("year", "month"))
    
    if "day" not in res_ds.coords:
        return "FAIL", "Coordinate 'day' is missing from Dataset coords"
    
    if "day" in res_ds.data_vars:
        return "FAIL", "Coordinate 'day' was incorrectly demoted to data_vars"
        
    if res_ds.coords["day"].dims != ("year", "month"):
        return "FAIL", f"Expected coords['day'].dims to be ('year', 'month'), got {res_ds.coords['day'].dims}"
        
    # Also verify the behaviour on a DataArray directly
    res_da = da.coarsen(time=12).construct(time=("year", "month"))
    if "day" not in res_da.coords:
        return "FAIL", "Coordinate 'day' is missing from DataArray coords"
        
    return "PASS", None

try:
    status, detail = run_test()
    if status == "PASS":
        print(f"RESULT={('PASS',)!r}")
    else:
        print(f"RESULT={('FAIL', detail)!r}")
except Exception as e:
    print(f"RESULT={('ERROR', type(e).__name__)!r}")
