import xarray as xr
import sys
import os
sys.path.append(os.environ['suitedir']+'lib')
import lib_standards
from xhistogram.xarray import histogram
import numpy as np
from scipy.signal import convolve2d
import iris
import glob

def main():
    # read inputs
    station=int(os.environ['station'])
    station=int(os.environ['station'])
    apply_mask = (os.environ['radar_apply_mask'] in ['TRUE','true','True',1])
    bin_interval = float(os.environ['radar_bin'])
    freq_in = os.environ['radar_freq_in']
    freq_out = os.environ['radar_freq_out']
    radar_path = os.environ['radar_path']
    scale = float(os.environ["radar_scale_factor"])
    analysis_grid=os.environ['radar_grid']
    boundary_pad=int(os.environ['radar_boundary_pad'])
    var=os.environ['radar_var']
    data_path = os.environ['data_path']
    outdir=os.environ['outdir']
    start_year=os.environ['start_year']
    end_year=os.environ['end_year']
    filename=os.environ['filename']
    obsdata = os.environ['obsdata'] in ['True',1,'true','TRUE']
    print('read input variables')
    if obsdata:
        outname = os.environ['radar_outname']
    path=data_path.format(var=var,freq=freq_in)
    # to implement: regrid mask to desired grid
    if analysis_grid not in ["AUST04","AUST-04","AUS-04",'AUS-4']:
       print("Interpolation not implemented yet")
    # read in radar location information from mask file
    if apply_mask:
        print('open mask')
        mask = xr.open_mfdataset(radar_path+f"masks/{station}.nc")
        if 'pr' in mask:
           mask=mask.pr
        else:
           mask=mask.rainrate
        try:
            mask = mask.rename(longitude='lon',latitude='lat')
        except ValueError:
            pass
        mask['lon'] = np.round(mask['lon'],4)
        mask['lat'] = np.round(mask['lat'],4)
       # constrict mask by specified number of grid-cells in order to remove radar edge effects
#        window = np.ones((2*boundary_pad+1,2*boundary_pad+1))
#        window = window/window.sum()
#        mask2=mask.copy(data=convolve2d(mask,
#                                    window,
#                                    mode='same',
#                                    boundary='fill',
#                                    fillvalue=1))
    # load in model data
    files = glob.glob(path+filename.format(var=var,
                                                  station=station,
                                                  freq=freq_in,
                                                  year1=f"*",
                                                  year2="*",
                                                  month1='*',
                                                  month2='*')) 
    files.sort()
    print("opening ",files)
    data = xr.open_mfdataset(files,chunks={})
    data = data.sel(time=slice(start_year,end_year))
    print('opened')
    try:
       data = data.rename(longitude='lon',latitude='lat')
    except ValueError:
       pass
    if apply_mask:
        data = data.sel(lon=slice(mask.lon.min(),mask.lon.max()),
                    lat=slice(mask.lat.min(),mask.lat.max()))
    data['lon'] = np.round(data['lon'],4)
    data['lat'] = np.round(data['lat'],4)
    print(data)
    # if neccessary, regrid onto same grid as mask
    # may need optimising if regridding is required
    if not obsdata:
        if len(data.lon) != len(mask.lon) or len(data.lat) != len(data.lat):
            print("regridding 1")
            data = lib_standards.regrid(data,mask.to_dataset())
        elif (data.lon.values != mask.lon.values).any() or (data.lat.values != mask.lat.values).any():
             dx_data = np.abs(np.gradient(data.lon.values).mean())
             diff_x = np.abs(data.lon.values - mask.lon.values).max()
             diff_y = np.abs(data.lat.values - mask.lat.values).max()
             if max(diff_x,diff_y)/dx_data < 1e-3: # likely a rounding error
                 print("forcing dimension match-up")
                 data['lon'] = mask['lon']
                 data['lat'] = mask['lat']
             else:
                 print("regridding 2")
                 data = lib_standards.regrid(data,mask.to_dataset())
        # assert regridding has worked
        assert (data.lon.values == mask.lon.values).all()
        assert (data.lat.values == mask.lat.values).all()
    # apply mask to data
    if apply_mask:
        mask.load()
        data = data[var].where(mask==1)
    # resample first (if required), then apply scale factor
    if freq_out != freq_in:
        data = data.resample(time=freq_out).mean()*scale
    else:
        data = data*scale
    # rechunk
    nt,ny,nx = data.shape
    # generate bins
    maxvalue = data.max().load()
    if np.isnan(maxvalue):
       print("Max value is NaN")
       maxvalue = 500
    bins = np.arange(0,maxvalue+bin_interval,bin_interval)
    print("bins as follows")
    print(bins)
    # calculate histograms
    hist = histogram(data,bins=bins,dim=['lon','lat']).resample(time='1M').sum()
    # save to output file
    print("histogram computed")
    print(hist)
    if obsdata:
        hist.to_netcdf(f"{outdir}/radar_distributions/Radar{station}_{outname}",encoding = {"histogram_"+var:{'zlib':True}})
    else:
        filename_out = filename.format(var=f"Radar{station}",freq=freq_out,year1=start_year,year2=end_year,month1="01",month2="12")
        hist.to_netcdf(f"{outdir}/radar_distributions/{filename_out}",encoding = {"histogram_"+var:{'zlib':True}})
    print('saved')

main()
