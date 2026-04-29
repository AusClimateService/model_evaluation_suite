import numpy as np
import matplotlib.pyplot as plt
import glob
import argparse
import os
import progressbar
import xarray as xr
from dask.distributed import Client, as_completed
import dask
import tempfile
import gc
import pandas as pd

def calc_dp_extreme_pr_relation(data,bins,quantile=0.99):
    relation=[]
    count =[] 
    data.load()
    bin_index = []
    bin_width = (bins[1]-bins[0])
    for b in bins:
        if ((data['tdps']<b+bin_width/2)
           *(data['tdps']>b-bin_width/2)).sum()>0:
            bin_index.append(b)
            count.append(((data['tdps']<b+bin_width/2)
                         *(data['tdps']>b-bin_width/2)).sum())
            relation.append(data['pr'].where((data['tdps']<b+bin_width/2)
                                            *(data['tdps']>b-bin_width/2)).quantile(quantile))
    relation = xr.DataArray(relation,dims='bin')
    relation['bin']=bin_index
    relation['lat']=data.lat.mean()
    relation['lon']=data.lon.mean()
    count = xr.DataArray(count,dims='bin')
    count['bin']=bin_index
    count['lat']=data.lat.mean()
    count['lon']=data.lon.mean()
    return relation,count


def calc_across_map(client, data_path,filename, outdir, n, bins,  landmask=False,bounds=[-180,360,-90,90]):

    # create input (intermediate data) file name
    outname = filename.format(var='wethours',
                              freq='1hr', 
                              year1="*",
                              year2="*",
                              month1="*",
                              month2="*")
    files = glob.glob(os.path.join(outdir,'wethours',outname))
    # load input data
    data = [xr.open_mfdataset(f) for f in files]
    data = xr.concat(data,dim='index')
    data = data.sel(lon=slice(bounds[0],bounds[1]),
                    lat=slice(bounds[2],bounds[3]))

    nt,ny,nx = data.pr.shape
    print(f"data opened: shape = {(nt,ny,nx)}")

    # load data mask if neccessary
    if landmask:
        maskfile = glob.glob((data_path+"/*.nc").format(freq='fx',var='sftlf'))
        mask = xr.open_mfdataset(maskfile)['sftlf'].load()
        mask = mask.sel(lon=slice(bounds[0],bounds[1]),
                        lat=slice(bounds[2],bounds[3]))
        print("mask loaded")
        mask = mask.where(mask==100,drop=True)
    # number of gridpoints

    # create list of coarse-grid points with sufficient data to perform calculation
    coarse_gridpoints = []
    for i,x in enumerate(np.arange(0,nx,n)):
        for j,y in enumerate(np.arange(0,ny,n)):
            tmp=mask[y:y+n,x:x+n]
#            if landmask:
            if (~np.isnan(tmp)).mean()>0.3:
                coarse_gridpoints.append((x,y))
#            else:
#                coarse_gridpoints.append((x,y))
    coarse_gridpoints = np.array(coarse_gridpoints)
    print("set up coarse grid")
    # loop through coarse grid points and do dewpoint binning
    relation = []
    count = []
    for x,y in progressbar.progressbar(coarse_gridpoints):
        tmp = calc_dp_extreme_pr_relation(data.isel(lon=slice(x,x+n),lat=slice(y,y+n)),bins)
        relation.append(tmp[0])
        count.append(tmp[1])


    #  Cluster setup

    # Scatter shared data once 
#    data_future  = client.scatter(data,  broadcast=True)
#    bins_future  = client.scatter(bins,  broadcast=True)
    """
    def _worker(data_ref, bins_ref, x, y, n):
        subset = data_ref.isel(lon=slice(x, x + n), lat=slice(y, y + n))
        result = calc_dp_extreme_pr_relation(subset, bins_ref)
        return result

    print(f"started to scatter. {len(coarse_gridpoints)} points in total")
    futures = {
        client.submit(_worker, data_future, bins_future, x, y, n): (x, y)
        for x, y in coarse_gridpoints
    }

    # Collect results in completion order (maximises throughput) 
    relation = [None] * len(coarse_gridpoints)
    count    = [None] * len(coarse_gridpoints)

    gridpoint_index = {(x, y): i for i, (x, y) in enumerate(coarse_gridpoints)}

    for future in as_completed(futures):
        x, y   = futures[future]
        i      = gridpoint_index[(x, y)]
        result = future.result()
        relation[i] = result[0]
        count[i]    = result[1]
        print(f"Done {i+1}/{len(coarse_gridpoints)}: ({x}, {y})")
    """

    # recreate spatial (2D) arrays
    relation = xr.concat(relation,dim='n')
    print(relation)
    relation['n'] = pd.MultiIndex.from_arrays([relation.lat.values,relation.lon.values],names=['latitude','longitude'])
    relation = relation.unstack('n')
    relation = relation.drop_vars(['lat','lon']).rename(latitude='lat',
                                                        longitude='lon')
    
    count = xr.concat(count,dim='n')
    count['n'] = pd.MultiIndex.from_arrays([count.lat.values,count.lon.values],names=['latitude','longitude'])
    count = count.unstack('n')
    count = count.drop_vars(['lat','lon']).rename(latitude='lat',
                                                  longitude='lon')

    # save output
    ds = xr.Dataset({f'p99pr':relation,'count':count})
    outname = filename.format(var='extreme-pr-at-dewpoint-bins',
                              freq='1hr', 
                              year1="",
                              year2="",
                              month1="",
                              month2="")
    ds.to_netcdf(os.path.join(outdir,'wethours',outname).
                 replace("*","").
                 replace("_-",""))



if __name__=="__main__":
    bins = np.arange(10,30,1)
    data_path =  os.environ['data_path']
    filename =  os.environ['filename']
    try:
        lonmin = float(os.environ['wethours_lonmin'])
        lonmax = float(os.environ['wethours_lonmax'])
        latmin = float(os.environ['wethours_latmin'])
        latmax = float(os.environ['wethours_latmax'])
        bounds = [lonmin,lonmax,latmin,latmax]
    except KeyError:
        bounds = [-180,360,-90,90]
    calc_dp = (os.environ['wethours_calcdp'] in ['TRUE','true','True',1])
    apply_mask = True# (os.environ['wethours_landmask'] in ['TRUE','true','True',1])
    threshold = float(os.environ['wethours_threshold'])
    outdir=os.environ['outdir']
    client=1
    """    
    
    client = Client(
        n_workers=1,
        threads_per_worker=1,       # xarray/numpy releases the GIL inconsistently;
                                   # one thread per worker avoids contention
        memory_limit="50000 MB",
    )
    print(client.dashboard_link)    # monitor progress in browser
    """
    calc_across_map(client, data_path,filename, outdir, 25, bins, apply_mask, bounds)
    #client.close()
    

