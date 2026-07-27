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

thresholds_seas = os.environ.get("thresholds_seas", "DJF MAM JJA SON year month_clim").split()
print(f"thresholds_seas: {thresholds_seas}")
request = os.environ.get("var")
freq,request = request.split(':')

if not request:
    print("ERROR: environment variable 'var' not set")
    sys.exit(1)

try:
    # split requested variables in multivariate threshold
    if '|' in request:
        if '&' in request:
            print("ERROR: request is too complicated, cannot pass | and & together")
            sys.exit(1)
        else:
            combine='or'
            requests=request.split('|')
    elif '&' in request:
        combine='and'
        requests = request.split('&')
    else:
        combine='or'
        requests=[request]

    varlist = []
    ineqs = {}
    thresholds = {}
    # extract variables, thresholds and inequalities
    for phrase in requests:
        try:
            var,ineq,thres = phrase.split('_')
        except:
            print(f"ERROR: request {phrase} should have format variable_ineq_threshold")
        ineq=ineq.lower()
        assert ineq in ['gt','lt','ge','le','eq']
        varlist.append(var)
        ineqs[var]=ineq
        thresholds[var]=float(thres)


except:
    print("ERROR: could not parse environmental variable 'var'")
    sys.exit(1)

assert len(varlist)==len(np.unique(varlist))

# some keys are not relevant for observations data 
obsdata=os.environ.get('obsdata') in ['1','True','TRUE']
if obsdata:
    env_vars = ["data_path", "outdir", "data_name"]
    data_path, outdir,data_name  = [os.environ[v] for v in env_vars]
else:
    env_vars = ["data_path", "outdir", "domain", "gcm", "scenario", "realisation", "institution", "rcm2"]
    data_path, outdir, domain, gcm, scenario, realisation, institution, rcm2 = [os.environ[v] for v in env_vars]

input_dirs = {}
for var in varlist:
    input_dirs[var] = data_path.format(freq=freq,var=var)
#version_dirs = sorted(glob.glob(os.path.join(base_dir, "v*")))

#if not version_dirs:
#    raise FileNotFoundError(f"No version subdirectory found in {base_dir}")

#if len(version_dirs) > 1:
#    raise ValueError(f"Multiple version subdirectories found in {base_dir}: {version_dirs}")

#input_dir = version_dirs[0]
outname = request.replace('&','_and_').replace('|','_or_')
output_dir = os.path.join(outdir,'thresholds',outname)
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
ds = {}
for var in varlist:
    print(input_dirs[var])
    input_dir = glob.glob(input_dirs[var])
    assert len(input_dir)==1
    input_dir = input_dir[0]
    files = sorted([os.path.join(input_dir, f) for f in os.listdir(input_dir) 
                if f"{var}" in f and f.endswith(".nc")])
    #print(files)
    if not files:
        print(f"No files found for variable {var}")
        sys.exit(0)

    print(f"Processing variable: {var}")
    ds[var] = xr.open_mfdataset(files, combine="by_coords", data_vars="minimal",compat='override')

    # Drop lat_bnds / lon_bnds if they exist
    for bnd_var in ["lat_bnds", "lon_bnds","pressure","crs","time_bnds"]:
        if bnd_var in ds[var]:
            print(f"Dropping variable: {bnd_var}")
            ds[var] = ds[var].drop_vars(bnd_var)

    # Ensure time is datetime64
    #if not np.issubdtype(ds.time.dtype, np.datetime64):
    #    ds['time'] = pd.to_datetime(ds['time'].values)

    # Restrict dataset to start_date and end_date if defined
    if start_date or end_date:
        ds[var] = subset_time(ds[var], start_date=start_date, end_date=end_date)

# test that coords all match
if len(varlist)>1:
    var = varlist[0]
    for j in range(1,len(varlist)):
        for coord in ['lon','lat','time']:
            c1 = ds[var][coord]
            c2 = ds[varlist[j]][coord]
            try:
                xr.testing.assert_allclose(c1,c2)
            except AssertionError as error:
                if coord=='time' and len(ds[var][coord])==len(ds[varlist[j]][coord]):
                    print(f"Warning: setting time coordinate from {varlist[j]} from {var}")
                    ds[varlist[j]][coord] = ds[var][coord]
                else:
                    raise(error)

ds = xr.merge(ds.values(),compat='override')

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

# apply thresholds

ds_new = {}

for var in ds:
    ineq = ineqs[var]
    print(f'applying {ineq}{thresholds[var]} to {var}')
    if ineq == 'gt':
       ds_new[var] = ds[var]>thresholds[var]
    elif ineq == 'lt':
       ds_new[var] = ds[var]<thresholds[var]
    elif ineq == 'ge':
       ds_new[var] = ds[var]>=thresholds[var]
    elif ineq == 'le':
       ds_new[var] = ds[var]<=thresholds[var]
    elif ineq == 'eq':
       ds_new[var] = ds[var]==thresholds[var]


# combine with and/or
if combine == 'or':
    ds_new_combined = xr.concat(ds_new.values(), dim="new_dim").any(dim="new_dim")
elif combine == 'and':
    ds_new_combined = xr.concat(ds_new.values(), dim="new_dim").all(dim="new_dim")

output = {'frequency':ds_new_combined}

# save conditional means of each variable
for var in ds:
    if combine == 'or':
        output[var] = ds[var].where(ds_new[var])
    if combine == 'and':
        output[var] = ds[var].where(ds_new_combined)


output = xr.Dataset(output)
# -----------------------------
# Loop over seasons and calculate mean
# -----------------------------
weights = ds.time.dt.days_in_month


for season in thresholds_seas:
    print(f"  Calculating seasonal mean for {season}")

    # Check if we should weight (Only if operation is 'mean')
    do_weighting = (freq == 'mon')

    if season in ["DJF", "MAM", "JJA", "SON"]:
        if do_weighting:
            weighted_data = output * weights
            sum_weighted = weighted_data.resample(time='QS-DEC').sum(dim='time')
            sum_weights = weights.resample(time='QS-DEC').sum(dim='time')
            seasonal_all = sum_weighted / sum_weights
        else:
            seasonal_all = output.resample(time='QS-DEC').mean('time')

        target_month = {"DJF": 12, "MAM": 3, "JJA": 6, "SON": 9}[season]
        season_mean = seasonal_all.sel(time=seasonal_all['time.month'] == target_month)
        
        # Labeling shift
        label_years = season_mean['time.year'] + (1 if season == "DJF" else 0)
        season_mean = season_mean.assign_coords(time=label_years).rename({'time': 'year'})

    elif season == "year":
        if do_weighting:
            season_mean = (output * weights).groupby('time.year').sum(dim='time') / weights.groupby('time.year').sum(dim='time')
        else:
            season_mean = output.groupby('time.year').mean('time')
 
    elif season == "month_clim":
        # Climatology is usually kept unweighted to see the monthly average
        season_mean = output.groupby('time.month').mean('time')

    else:
        if season not in season_months:
            print(f"ERROR: Custom season '{season}' not defined in season_months.")
            continue # Skip to the next season instead of crashing

        months = season_months[season]
        # Custom month lists (Weighted)
        ds_sub = output.sel(time=ds['time.month'].isin(months))
        if do_weighting:
            w_sub = weights.sel(time=ds['time.month'].isin(months))
            season_mean = (ds_sub * w_sub).groupby('time.year').sum(dim='time') / w_sub.groupby('time.year').sum(dim='time')
        else:
            season_mean = ds_sub.groupby('time.year').mean('time')
    print("computation complete")
    season_mean.load()
    print("data loaded")
    # Save output
    if obsdata:
        out_file = os.path.join(output_dir, f"{outname}_{data_name}_v1-r1_{season}_{start_date}-{end_date}.nc")
    else:
        out_file = os.path.join(output_dir, f"{outname}_{domain}_{gcm}_{scenario}_{realisation}_{institution}_{rcm2}_v1-r1_{season}_{start_date}-{end_date}.nc")
    print(out_file)
    encoding = {}
    for var in ['frequency']+varlist:
        encoding[var] = {'zlib':True, 'complevel':1, 'shuffle':True, 'dtype': 'float32'}
    season_mean.to_netcdf(out_file, encoding=encoding)
    print(f"    Saved to {out_file}")
