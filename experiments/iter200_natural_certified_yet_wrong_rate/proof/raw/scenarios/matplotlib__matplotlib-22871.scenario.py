import matplotlib

matplotlib.use("Agg")

import matplotlib.dates as mdates
from datetime import datetime, timezone

locator = mdates.AutoDateLocator()
formatter = mdates.ConciseDateFormatter(
    locator,
    tz=timezone.utc,
    formats=["Y%Y", "M%m", "D%d", "H%H", "N%M", "S%S", "U%f"],
    zero_formats=["ZY%Y", "ZMONTH_YEAR_%Y", "ZD%d", "ZH%H", "ZN%M", "ZS%S", "ZU%f"],
    offset_formats=["OY%Y", "OFFSET_YEAR_%Y", "OD%Y", "OH%Y", "ON%Y", "OS%Y", "OU%Y"],
)

values = mdates.date2num([
    datetime(2020, 12, 1, tzinfo=timezone.utc),
    datetime(2021, 1, 1, tzinfo=timezone.utc),
])

labels = formatter.format_ticks(values)
print("RESULT=" + repr((labels, formatter.get_offset())))
