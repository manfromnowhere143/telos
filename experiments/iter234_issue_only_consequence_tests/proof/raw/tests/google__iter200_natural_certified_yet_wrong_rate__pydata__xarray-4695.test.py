import xarray as xr

def main():
    try:
        # Create a DataArray with dimensions named after all the keyword 
        # arguments of DataArray.sel() to ensure .loc avoids collisions.
        da = xr.DataArray(
            [[[[1, 2], [3, 4]], [[5, 6], [7, 8]]]],
            dims=["indexers", "method", "tolerance", "drop"],
            coords={
                "indexers": ["x"],
                "method": ["a", "b"],
                "tolerance": [0.1, 0.2],
                "drop": ["yes", "no"]
            }
        )
        
        # Access using .loc with a dictionary containing keys that overlap
        # with arguments of DataArray.sel()
        res = da.loc[dict(indexers="x", method="b", tolerance=0.1, drop="no")]
        
        # Verify the outcome is correct
        if res.item() != 6:
            print(f"RESULT={('FAIL', f'Expected 6, got {res.item()}')!r}")
            return
            
        print(f"RESULT={('PASS',)!r}")
    except Exception as e:
        print(f"RESULT={('ERROR', type(e).__name__)!r}")

if __name__ == "__main__":
    main()
