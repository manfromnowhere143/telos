from astropy.io import fits

try:
    # The issue states that FITSDiff reports differences when comparing identical files
    # if they contain Variable Length Array (VLA) columns (e.g., format 'QD').
    # We construct two identical tables with a VLA column and compare them in memory.
    
    col1 = fits.Column('a', format='QD', array=[[0], [0, 0]])
    hdu1 = fits.BinTableHDU.from_columns([col1])
    hdul1 = fits.HDUList([fits.PrimaryHDU(), hdu1])
    
    col2 = fits.Column('a', format='QD', array=[[0], [0, 0]])
    hdu2 = fits.BinTableHDU.from_columns([col2])
    hdul2 = fits.HDUList([fits.PrimaryHDU(), hdu2])
    
    # Compare the two identical HDU lists
    diff = fits.FITSDiff(hdul1, hdul2)
    
    if diff.identical:
        print(f"RESULT={('PASS',)!r}")
    else:
        print(f"RESULT={('FAIL', 'FITSDiff reported differences for identical VLA columns')!r}")
        
except Exception as e:
    print(f"RESULT={('ERROR', type(e).__name__)!r}")
