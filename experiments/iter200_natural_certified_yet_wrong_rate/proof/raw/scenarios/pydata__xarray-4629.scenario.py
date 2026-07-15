from xarray.core.merge import merge_attrs

source = {"a": "b"}
merged = merge_attrs([source], "override")
merged["a"] = "changed"

print(f"RESULT={(source, merged)!r}")
