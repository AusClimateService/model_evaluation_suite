"""
Extract model data for given station locations.                                   
The station information is defined in a CSV file, e.g., 
/g/data/tp28/SRA_CCRS_project/scripts/sgp_stations.csv
"""                                                                                                  
import os,sys
import xarray as xr
import pandas as pd
import tempfile
import glob
import contextlib
import numpy as np
import datetime as dt
from pathlib import Path

def read_station_info(f):
    # Read in as a DataFrame
    if f[-3:]=='csv':
        st_df = pd.read_csv(f)
        st_df.index.name = 'station'
        # Convert to an xarray DataArray
        st_da = st_df.to_xarray()
        return st_da
    elif f[-2:]=='nc':
        st_da = xr.open_mfdataset(f)
        return st_da
    else:
        print("unknown station filetype")
        exit()

def main(years,data_path,filename,freq,var,stationlist,outdir):
    stations = read_station_info(stationlist)
    extracted = []
    for year in years:
        files = glob.glob((data_path+filename).format(freq=freq,
                                                var=var,
                                                month1="*",
                                                year1=year,
                                                month2="*",
                                                year2=year))
        print((data_path+filename).format(freq=freq,
                                                var=var,
                                                month1="*",
                                                year1=year,
                                                month2="*",
                                                year2=year))
        print(f"loading {files} for {var}")
        data = xr.open_mfdataset(files)
        data = data[var].sel(lon=stations.lon, lat=stations.lat, method='Nearest').load()
        extracted.append(data)
    extracted = xr.concat(extracted,dim='time')
    outfile = filename.format(freq=freq,
                              var=var+"-at-stations",
                              month1="01",
                              year1=years[0],
                              month2="12",
                              year2=years[-1])
    extracted.to_netcdf(os.path.join(outdir,'stations',var,outfile),
                        encoding = {var:{'zlib':True}})


if __name__ == "__main__":
    start_year = int(os.environ['start_year'])
    end_year = int(os.environ['end_year'])
    data_path =  os.environ['data_path']
    filename =  os.environ['filename']
    outdir=os.environ['outdir']
    freq = os.environ['stations_freq']
    stationlist = os.environ['stations_list']
    var = os.environ['var']
    years =np.arange(start_year,end_year+1)
    main(years,data_path,filename,freq,var,stationlist,outdir)
