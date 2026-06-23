import xarray as xr
import pandas as pd
import numpy as np
import os
import sys
import argparse
import xesmf as xe
from dask.diagnostics import ProgressBar

# -------------------------------------------------------------------------
# Modified from lag1_corr in https://github.com/WCRP-CORDEX/ml-benchmark
# -------------------------------------------------------------------------

def round_coordinates(ds):
    """Rounds lat and lon to eliminate tiny floating-point variations."""
    if 'lon' in ds.coords:
        ds.coords['lon'] = ds.coords['lon'].round(4)
    if 'lat' in ds.coords:
        ds.coords['lat'] = ds.coords['lat'].round(4)

# Round boundary variables if they exist in the dataset
    if 'lon_bnds' in ds.variables:
        ds['lon_bnds'] = ds['lon_bnds'].round(4)
    if 'lat_bnds' in ds.variables:
        ds['lat_bnds'] = ds['lat_bnds'].round(4)

    return ds

def subset_time(ds, start_date=None, end_date=None):
    """Subset the time axis."""
    return ds.sel({'time': slice(start_date, end_date)})

# -----------------------------
# Read environment variables
# -----------------------------
arg_parser = argparse.ArgumentParser(
    description=__doc__,
    argument_default=argparse.SUPPRESS,
    formatter_class=argparse.RawDescriptionHelpFormatter
)
arg_parser.add_argument(
    "--regrid",
    type=str,
    default='None',
    help="Instructions to regrid dataset before computing index. Supply a float in degrees (e.g. 1.5) or a path to a template file",
)
args = arg_parser.parse_args()
try:
    args.regrid = float(args.regrid)
    print(f'Data will be regridded to a {args.regrid:0.2f} degree grid')
except ValueError:
    if os.path.isfile(str(args.regrid)):
        print(f'Data will be regridded to {args.regrid}')
    elif str(args.regrid).lower() in ["none", "false"]:
        args.regrid = None
        print(f'Data will not be regridded')
    else:
        assert 0, f'Regridder reference {args.regrid} not found'

# Using a generic "seas" environment variable, defaulting to standard seasons
lag1_seas = os.environ.get("lag1_corr_seas", "DJF MAM JJA SON year").split()
var = os.environ.get("var")
if not var:
    print("ERROR: environment variable 'var' not set")
    sys.exit(1)

env_vars = ["data_path", "outdir", "domain", "gcm", "scenario", "realisation", "institution", "rcm2"]
data_path, outdir, domain, gcm, scenario, realisation, institution, rcm2 = [os.environ[v] for v in env_vars]

# Adjust input frequency as needed
input_freq = os.environ.get("lag1_corr_freq", "1hr")
input_dir = data_path.format(freq=input_freq, var=var)
print(f"Input directory: {input_dir}")

output_dir = os.path.join(outdir, "lag1_corr", var)
print(f"Output directory: {output_dir}")
os.makedirs(output_dir, exist_ok=True)

start_date = os.environ.get("start_year")
end_date = os.environ.get("end_year")

season_months = {
    "DJF": [12, 1, 2], "MAM": [3, 4, 5], "JJA": [6, 7, 8], "SON": [9, 10, 11], "year": list(range(1, 13))
}

# -----------------------------
# Load Data with Dask
# -----------------------------
files = sorted([os.path.join(input_dir, f) for f in os.listdir(input_dir) if f"{var}" in f and f.endswith(".nc")])
# IMPORTANT: Use chunks to prevent memory overflow
ds = xr.open_mfdataset(files, combine="by_coords", chunks={'time': 100, 'lat': -1, 'lon': -1}, preprocess=round_coordinates, coords='minimal', compat="override")

for bnd_var in ["lat_bnds", "lon_bnds"]:
    if bnd_var in ds: ds = ds.drop_vars(bnd_var)

if not np.issubdtype(ds.time.dtype, np.datetime64):
    ds['time'] = pd.to_datetime(ds['time'].values)

if start_date or end_date:
    ds = subset_time(ds, start_date=start_date, end_date=end_date)

    # Regrid if true
    if args.regrid and str(args.regrid).lower() != "false":
        if type(args.regrid) is float:
            delta = args.regrid
            lon = np.arange(round(ds.lon.min().values/delta)*delta,ds.lon.max().values,delta)
            lat = np.arange(round(ds.lat.min().values/delta)*delta+delta/2,ds.lat.max().values,delta)
            ds_ref = xr.DataArray(
                name='reference',
                data = np.ones((len(lat),len(lon))),
                dims=["lat", "lon"],
                coords=dict(
                    lat=("lat", lat),
                    lon=("lon", lon),
                )).to_dataset()
        else:
            ds_ref = xr.open_dataset(args.regrid)
            ds_ref = ds_ref.sel(
                lat=slice(ds.lat.min().values,ds.lat.max().values),
                lon=slice(ds.lon.min().values,ds.lon.max().values)
                    )
        ref_res = np.mean([np.abs(np.gradient(ds_ref.lon.values)).mean(),np.abs(np.gradient(ds_ref.lat.values)).mean()])
        df_res = np.mean([np.abs(np.gradient(ds.lon.values)).mean(),np.abs(np.gradient(ds.lat.values)).mean()])
        if ref_res < df_res:
            regrid_method = 'bilinear'
            print('Warning: downscaling data to finer resoulution using bilinear regridding')
        else:
            regrid_method = 'conservative'
        ds = ds.unify_chunks()
        ds = ds.chunk(chunks={'time':ds.chunks['time'],'lat':ds.lat.shape,'lon':ds.lon.shape})      
        regridder = xe.Regridder(ds, ds_ref, regrid_method)
        ds = regridder(ds)

# -----------------------------
# Lag-1 Autocorrelation Main Loop
# -----------------------------
for season in lag1_seas:
    months = season_months[season]
    print(f"--- Processing Lag-1 Correlation for {season} ---")

    # Filter to specific season
    da_season = ds[var].sel(time=ds['time.month'].isin(months))
    
    # Create the shifted array along the time dimension
    da_shifted = da_season.shift(time=1)

    print("  Computing correlation over time (Running lazily via Dask)...")
    # xr.corr handles dask arrays nicely, so we wrap the computation in ProgressBar
    with ProgressBar():
        lag1_corr_da = xr.corr(da_season, da_shifted, dim="time").compute()
    
    # Save to Dataset
    out_ds = xr.Dataset(
        data_vars=dict(
            lag1_corr=(["lat", "lon"], lag1_corr_da.values)
        ),
        coords=dict(
            lat=lag1_corr_da.lat,
            lon=lag1_corr_da.lon
        )
    )

    # Save output using the established naming convention
    out_file = os.path.join(output_dir, f"{var}_{domain}_{gcm}_{scenario}_{realisation}_{institution}_{rcm2}_{season}_lag1corr_{start_date}-{end_date}.nc")
    out_ds.to_netcdf(out_file)
    print(f"    Saved Lag-1 Correlation to {out_file}")
