import xarray as xr
import pandas as pd
import numpy as np
import os
import sys
import glob
import xesmf as xe
import argparse
from dask.diagnostics import ProgressBar

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
    
def get_radial_profile(mean_psd_2d):
    """
    Collapses 2D PSD to 1D radial profile, following the 
    robust centering and division logic of _radial_average.
    """
    y, x = np.indices(mean_psd_2d.shape)
    
    # Use floating point center based on max/min indices
    # This matches (x.max() - x.min()) / 2.0 logic
    center_y = (y.max() - y.min()) / 2.0
    center_x = (x.max() - x.min()) / 2.0
    
    # Use np.hypot for better numerical stability and cast to int32
    r = np.hypot(x - center_x, y - center_y).astype(np.int32)
    
    # Sum values and count pixels in each radial bin
    tbin = np.bincount(r.ravel(), mean_psd_2d.ravel())
    nr = np.bincount(r.ravel())
    
    # Use np.maximum to avoid division by zero
    return tbin / np.maximum(nr, 1)

def compute_psd_chunked(da):
    """
    Computes 2D FFT on spatial dims and averages over time using Dask.
    """
    # 1. Apply 2D FFT spatially for each time slice
    # This remains lazy if using dask-backed xarray
    def fft_step(field2d):
        # field2d shape: (time, lat, lon)
        coeffs = np.fft.fft2(field2d, axes=(-2, -1))
        shifted = np.fft.fftshift(coeffs, axes=(-2, -1))
        return np.abs(shifted)**2

    print("  Initializing Dask-backed FFT calculation...")
    # Map the FFT over time chunks
    psd_2d_lazy = xr.apply_ufunc(
        fft_step, da,
        input_core_dims=[["lat", "lon"]],
        output_core_dims=[["lat", "lon"]],
        vectorize=True,
        dask="parallelized",
        output_dtypes=[np.float32]
    )

    # 2. Compute the mean over time (this triggers the computation)
    print("  Computing temporal mean (Running on Gadi nodes)...")
    with ProgressBar():
        mean_psd_2d = psd_2d_lazy.mean(dim="time").compute()
    
    return mean_psd_2d.values

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

psd_seas = os.environ.get("psd_seas", "DJF MAM JJA SON year").split()
var = os.environ.get("var")
if not var:
    print("ERROR: environment variable 'var' not set")
    sys.exit(1)

env_vars = ["data_path", "outdir", "domain", "gcm", "scenario", "realisation", "institution", "rcm2"]
data_path, outdir, domain, gcm, scenario, realisation, institution, rcm2 = [os.environ[v] for v in env_vars]
input_freq = os.environ.get("psd_freq", "1hr")
input_dir = data_path.format(freq=input_freq, var=var)
print(input_dir)

output_dir = os.path.join(outdir, "psd", var)
print(output_dir)
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

# Determine spatial resolution for wavelength calculation (approximate in km)
# 1 degree lat is ~111km
try:
    dx = np.abs(np.diff(ds.lon.values)).mean() * 111.0 
except:
    dx = 12.5 # Default fallback for CCAM AUS-20i

# -----------------------------
# PSD Main Loop
# -----------------------------
for season in psd_seas:
    months = season_months[season]
    print(f"--- Processing PSD for {season} ---")

    da_season = ds[var].sel(time=ds['time.month'].isin(months))
    
    # Fill NaNs with 0 for FFT stability
    da_season = da_season.fillna(0)

    # Compute the 2D Mean PSD (Memory safe)
    mean_psd_2d = compute_psd_chunked(da_season)
    
    # Extract 1D Profile
    radial_profile = get_radial_profile(mean_psd_2d)
    
    # Wavelength conversion logic
    ny, nx = mean_psd_2d.shape
    max_dim = max(ny, nx)
    domain_length_km = dx * max_dim
    bins = np.arange(len(radial_profile))
    wavelengths = np.zeros_like(radial_profile, dtype=float)
    wavelengths[1:] = domain_length_km / bins[1:]

    # Save to Dataset (Excluding DC component Bin 0)
    psd_ds = xr.Dataset(
        data_vars=dict(
            psd=(["wavelength"], radial_profile[1:]),
            log10_psd=(["wavelength"], np.log10(radial_profile[1:]))
        ),
        coords=dict(
            wavelength=wavelengths[1:],
            log10_wavelength=(["wavelength"], np.log10(wavelengths[1:]))
        )
    )

    # 4. Save output (using your specific naming convention)
    out_file = os.path.join(output_dir, f"{var}_{domain}_{gcm}_{scenario}_{realisation}_{institution}_{rcm2}_{season}_psd_{start_date}-{end_date}.nc")
    psd_ds.to_netcdf(out_file)
    print(f"    Saved PSD to {out_file}")
