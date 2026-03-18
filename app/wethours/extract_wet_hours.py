import xarray as xr
import numpy as np
import matplotlib.pyplot as plt
import glob
import argparse
import os
from metpy.calc import dewpoint_from_relative_humidity


def extract_wet_hours(data_path, month, year, outdir, calc_dp=False, threshold=0.2,bounds=[-180,360,-90,90]):
    """
    Extracts pr and dewpoint from hours with rainfall exceeding a threshold.
    Applies 1-hour lag to dewpoint
    Args:
        data_path: filepath with wilds for frequency, year, month and variable 
        month: month to process
        year: year to process
        outdir: path to save outputs
        calc_dp: whether to calculate dewpoint from tas and rh or to load it directly
        threshold: threshold to retain rainfall values above
        bounds: spatial extent for optional subsetting 
    Returns
        Saves data to global variable savepath/filename
    """
    x0,x1,y0,y1=bounds
    # locate input files
    files = {}
    if calc_dp:
        varlist = ['pr','hurs','tas']
    else:
        varlist = ['pr','tdps']
    for var in varlist:
        files[var] = glob.glob(data_path.format(freq='1hr', 
                                                month1=f"{month:02d}", 
                                                year1=year, 
                                                var=var, 
                                                month2=f"{month:02d}", 
                                                year2=year))
        if var != 'pr':
        # include dewpoint from final hour of previous month (if available)
            if month == 1:
                 datapath_lastmonth = data_path.format(freq='1hr', 
                                                       month1=12, 
                                                       year1=year-1, 
                                                       var=var, 
                                                       month2=12,
                                                       year2=year-1)
            else:
                 datapath_lastmonth = data_path.format(freq='1hr', 
                                                       month1=f"{month-1:02d}", 
                                                       year1=year, 
                                                       var=var,
                                                       month2=f"{month-1:02d}",
                                                       year2=year)
            files_lastmonth =  glob.glob(datapath_lastmonth)
            files_lastmonth.sort()
            if len(files_lastmonth)>0:
                files[var].append(files_lastmonth[-1])
            else:
                print(f"No previous month found for {var} {year} {month} - is this the start of the dataset?")
        files[var].sort()
    print(f"opening {len(files['pr'])} files for pr")
    print(f"{files['pr']}")
    pr = xr.open_mfdataset(files['pr']).pr.sel(lon=slice(x0,x1),lat=slice(y0,y1))
    print("Loaded precip")
    print(pr)
    if calc_dp:
        print(f"opening {len(files['tas'])} files for tas")
        print(f"{files['tas']}")
        tas = xr.open_mfdataset(files['tas']).tas.sel(lon=slice(x0,x1),lat=slice(y0,y1))
        print(f"opening {len(files['tas'])} files for rh")
        print(f"{files['hurs']}")
        rh = xr.open_mfdataset(files['hurs']).hurs.sel(lon=slice(x0,x1),lat=slice(y0,y1))
        print("Loaded tas and rh")
        tdps = dewpoint_from_relative_humidity(tas,rh/100)
        print("Computed dewpoint")
    else:
        print(f"opening {len(files['tdps'])} files for dewpoint")
        print(f"{files['tdps']}")
        tdps = xr.open_mfdataset(files['tdps']).tdps.sel(lon=slice(x0,x1),lat=slice(y0,y1))
        print("Loaded tdps")

    # shift dewpoint forward one hour
    tdps_shift = tdps.shift(time=1)[-1*len(pr.time):]
    # at each grid-point, sort by precip values. Scale precip into mm/hr
    array_index= pr.values.argsort(axis=0)
    pr_sorted = np.take_along_axis(pr.values, array_index, axis=0)*3600
    tdps_sorted = np.take_along_axis(tdps_shift.values, array_index, axis=0)
    # compute number of datapoints with values above precip threshold 
    n = (pr_sorted.max(axis=(1, 2))>=threshold).sum()
    # truncate most values below threshold
    pr_trunc = pr_sorted[-n:]
    tdps_trunc = tdps_sorted[-n:]
    # convert to xarray format. Remove time coordinate as times have been scrambled
    pr_trunc_xr = pr[-n:].copy(data=pr_trunc).drop_vars('time').rename({'time':'index'})
    tdps_trunc_xr = tdps[-n:].copy(data=tdps_trunc).drop_vars('time').rename({'time':'index'})
    ds = xr.Dataset({'pr':pr_trunc_xr, 'tdps':tdps_trunc_xr})
    # mask remaining values below precip threshold
    ds = ds.where(ds.pr>0.2)
    ds.to_netcdf(os.path.join(outdir,'wethours',f'wethours_{year}{month:02d}.nc'),
                 encoding = {'pr':{'zlib':True},
                             'tdps':{'zlib':True}})

if __name__=="__main__":
    year = int(os.environ['YEAR'])
    month = int(os.environ['MONTH'])
    data_path =  os.environ['data_path']
    filename =  os.environ['filename']
    lonmin = float(os.environ['wethours_lonmin'])
    lonmax = float(os.environ['wethours_lonmax'])
    latmin = float(os.environ['wethours_latmin'])
    latmax = float(os.environ['wethours_latmax'])
    calc_dp = (os.environ['wethours_calcdp'] in ['TRUE','true','True',1])
    threshold = float(os.environ['wethours_threshold'])
    outdir=os.environ['outdir']
    extract_wet_hours(data_path+filename, month, year, outdir, calc_dp, threshold, [lonmin,lonmax,latmin,latmax]) 
