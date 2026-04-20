import xarray as xr
import pandas as pd
import numpy as np
import os
import sys
import glob
import xesmf as xe
import argparse

def subset_time(ds, start_date=None, end_date=None):
    """Subset the time axis.

    Parameters
    ----------
    ds : Union[xarray.DataArray, xarray.Dataset]
        Input data.
    start_date : Optional[str]
        Start date of the subset.
        Date string format -- can be year ("%Y"), year-month ("%Y-%m") or year-month-day("%Y-%m-%d").
        Defaults to first day of input data-array.
    end_date : Optional[str]
        End date of the subset.
        Date string format -- can be year ("%Y"), year-month ("%Y-%m") or year-month-day("%Y-%m-%d").
        Defaults to last day of input data-array.

    Returns
    -------
    Union[xarray.DataArray, xarray.Dataset]
        Subsetted xarray.DataArray or xarray.Dataset
    """

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
    if os.path.isfile(args.regrid):
        print(f'Data will be regridded to {args.regrid}')
    elif args.regrid.lower() in ["none", "false"]:
        args.regrid=None
        print(f'Data will not be regridded')
    else:
        assert 0,f'Regridder reference {args.regrid} '

means_seas = os.environ.get("means_seas", "DJF MAM JJA SON year month_clim").split()
var = os.environ.get("var")

if 'means_oper' in os.environ:
    oper_name = os.environ['means_oper']
    oper = getattr(np,oper_name)
else:
    oper = np.mean
    oper_name ="mean"


if 'means_freq' in os.environ:
    freq = os.environ['means_freq']
else:
    freq ="mon"

if not var:
    print("ERROR: environment variable 'var' not set")
    sys.exit(1)

# some keys are not relevant for observations data 
obsdata=os.environ.get('obsdata') in ['1','True','TRUE']
if obsdata:
    env_vars = ["data_path", "outdir", "data_name"]
    data_path, outdir,data_name  = [os.environ[v] for v in env_vars]
else:
    env_vars = ["data_path", "outdir", "domain", "gcm", "scenario", "realisation", "institution", "rcm2"]
    data_path, outdir, domain, gcm, scenario, realisation, institution, rcm2 = [os.environ[v] for v in env_vars]

input_dir = data_path.format(freq=freq,var=var)
#version_dirs = sorted(glob.glob(os.path.join(base_dir, "v*")))

#if not version_dirs:
#    raise FileNotFoundError(f"No version subdirectory found in {base_dir}")

#if len(version_dirs) > 1:
#    raise ValueError(f"Multiple version subdirectories found in {base_dir}: {version_dirs}")

#input_dir = version_dirs[0]
output_dir = os.path.join(outdir,oper_name,var)
os.makedirs(output_dir, exist_ok=True)

start_date = os.environ.get("start_year")
end_date = os.environ.get("end_year")

# Map seasons to months
season_months = {
    "JJAS": [6, 7, 8, 9],
    "OND": [10, 11, 12],
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
ds = xr.open_mfdataset(files, combine="by_coords", data_vars="minimal")

# Drop lat_bnds / lon_bnds if they exist
for bnd_var in ["lat_bnds", "lon_bnds"]:
    if bnd_var in ds:
        print(f"Dropping variable: {bnd_var}")
        ds = ds.drop_vars(bnd_var)

# Ensure time is datetime64
#if not np.issubdtype(ds.time.dtype, np.datetime64):
#    ds['time'] = pd.to_datetime(ds['time'].values)

# Restrict dataset to start_date and end_date if defined
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
# Loop over seasons and calculate mean
# -----------------------------
weights = ds.time.dt.days_in_month
for season in means_seas:
    print(f"  Calculating seasonal {oper_name} for {season}")

    # Check if we should weight (Only if operation is 'mean')
    do_weighting = (oper_name == "mean")

    if season in ["DJF", "MAM", "JJA", "SON"]:
        if do_weighting:
            weighted_data = ds[var] * weights
            sum_weighted = weighted_data.resample(time='QS-DEC').sum(dim='time')
            sum_weights = weights.resample(time='QS-DEC').sum(dim='time')
            seasonal_all = sum_weighted / sum_weights
        else:
            seasonal_all = ds[var].resample(time='QS-DEC').reduce(oper, 'time')

        target_month = {"DJF": 12, "MAM": 3, "JJA": 6, "SON": 9}[season]
        season_mean = seasonal_all.sel(time=seasonal_all['time.month'] == target_month)
        
        # Labeling shift
        label_years = season_mean['time.year'] + (1 if season == "DJF" else 0)
        season_mean = season_mean.assign_coords(time=label_years).rename({'time': 'year'})

    elif season == "year":
        if do_weighting:
            season_mean = (ds[var] * weights).groupby('time.year').sum(dim='time') / weights.groupby('time.year').sum(dim='time')
        else:
            season_mean = ds[var].groupby('time.year').reduce(oper, 'time')

    elif season == "month_clim":
        # Climatology is usually kept unweighted to see the monthly average
        season_mean = ds[var].groupby('time.month').reduce(oper, 'time')

    else:
        if season not in season_months:
            print(f"ERROR: Custom season '{season}' not defined in season_months.")
            continue # Skip to the next season instead of crashing

        months = season_months[season]
        # Custom month lists (Weighted)
        ds_sub = ds[var].sel(time=ds['time.month'].isin(months))
        if do_weighting:
            w_sub = weights.sel(time=ds['time.month'].isin(months))
            season_mean = (ds_sub * w_sub).groupby('time.year').sum(dim='time') / w_sub.groupby('time.year').sum(dim='time')
        else:
            season_mean = ds_sub.groupby('time.year').reduce(oper, 'time')

    season_mean.name = var
    # Save output
    if obsdata:
        out_file = os.path.join(output_dir, f"{var}_{data_name}_v1-r1_{season}_{oper_name}_{start_date}-{end_date}.nc")
    else:
        out_file = os.path.join(output_dir, f"{var}_{domain}_{gcm}_{scenario}_{realisation}_{institution}_{rcm2}_v1-r1_{season}_{oper_name}_{start_date}-{end_date}.nc")
    print(out_file)
    season_mean.to_netcdf(out_file, encoding={var:{'zlib':True, 'complevel':1, 'shuffle':True, 'dtype': 'float32'}})
    print(f"    Saved to {out_file}")
