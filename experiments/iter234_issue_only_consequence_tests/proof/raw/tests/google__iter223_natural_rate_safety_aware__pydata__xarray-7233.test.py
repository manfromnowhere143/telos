import xarray as xr

def main():
    try:
        # Create a DataArray with a non-dimensional coordinate
        da = xr.DataArray(list(range(24)), dims=["time"])
        da = da.assign_coords(day=("time", [365 * i for i in range(24)]))
        
        # Convert to Dataset as per the issue's MCVE
        ds = da.to_dataset(name="T")

        # Perform coarsen.construct on Dataset
        ds_c = ds.coarsen(time=12).construct(time=("year", "month"))
        
        # Check if the non-dimensional coordinate was demoted to a data variable
        if "day" not in ds_c.coords:
            print(f"RESULT={('FAIL', 'Dataset: coordinate missing from coords')!r}")
            return
            
        if "day" in ds_c.data_vars:
            print(f"RESULT={('FAIL', 'Dataset: coordinate demoted to data_vars')!r}")
            return
            
        # Perform coarsen.construct on DataArray (for thoroughness)
        da_c = da.coarsen(time=12).construct(time=("year", "month"))
        
        if "day" not in da_c.coords:
            print(f"RESULT={('FAIL', 'DataArray: coordinate missing from coords')!r}")
            return
            
        print(f"RESULT={('PASS',)!r}")

    except Exception as e:
        print(f"RESULT={('ERROR', type(e).__name__)!r}")

if __name__ == '__main__':
    main()
