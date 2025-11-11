import xarray as xr
import pandas as pd
import numpy as np
import os
import sys
import glob

# -----------------------------
# Read environment variables
# -----------------------------
means_seas = os.environ.get("means_seas", "DJF MAM JJA SON ANN").split()
var = os.environ.get("var")
if not var:
    print("ERROR: environment variable 'var' not set")
    sys.exit(1)

data_path = os.environ['data_path']
outdir = os.environ['outdir']
base_dir = os.path.join(data_path, "mon", var)
version_dirs = sorted(glob.glob(os.path.join(base_dir, "v*")))

if not version_dirs:
    raise FileNotFoundError(f"No version subdirectory found in {base_dir}")

if len(version_dirs) > 1:
    raise ValueError(f"Multiple version subdirectories found in {base_dir}: {version_dirs}")

input_dir = version_dirs[0]
output_dir = os.path.join(outdir,"means")
os.makedirs(output_dir, exist_ok=True)

start_year = os.environ.get("start_year")
end_year = os.environ.get("end_year")
if start_year:
    start_year = int(start_year)
if end_year:
    end_year = int(end_year)

# Map seasons to months
season_months = {
    "DJF": [12, 1, 2],
    "MAM": [3, 4, 5],
    "JJA": [6, 7, 8],
    "SON": [9, 10, 11],
    "ANN": list(range(1, 13))
}

# -----------------------------
# Load all NetCDF files for this variable
# -----------------------------
print(input_dir)
files = sorted([os.path.join(input_dir, f) for f in os.listdir(input_dir) 
                if f"{var}" in f and f.endswith(".nc")])
print(files)
if not files:
    print(f"No files found for variable {var}")
    sys.exit(0)

print(f"Processing variable: {var}")
ds = xr.open_mfdataset(files, combine="by_coords")

# Ensure time is datetime64
if not np.issubdtype(ds.time.dtype, np.datetime64):
    ds['time'] = pd.to_datetime(ds['time'].values)

# Restrict dataset to start_year and end_year if defined
if start_year or end_year:
    time_index = ds['time']
    if start_year:
        ds = ds.where(time_index.dt.year >= start_year, drop=True)
    if end_year:
        ds = ds.where(time_index.dt.year <= end_year, drop=True)

# -----------------------------
# Loop over seasons and calculate mean
# -----------------------------
for season in means_seas:
    months = season_months[season]
    print(f"  Calculating seasonal mean for {season}")

    if season == "DJF":
        # DJF crosses year boundary
        season_mean = ds[var].groupby('time.year').apply(
            lambda x: x.sel(time=x['time.month'].isin(months)).mean('time')
        )
    elif season == "ANN":
        season_mean = ds[var].groupby('time.year').mean('time')
    else:
        season_mean = ds[var].sel(time=ds['time.month'].isin(months)).groupby('time.year').mean('time')

    # Save output
    out_file = os.path.join(output_dir, f"{var}_{start_year}-{end_year}_{season}_mean.nc")
    season_mean.to_netcdf(out_file)
    print(f"    Saved to {out_file}")

