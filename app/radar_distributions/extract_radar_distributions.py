import xarray as xr
import sys
import os
sys.path.append(os.environ['suitedir']+'lib')
import lib_standards
from xhistogram.xarray import histogram
import numpy as np
from scipy.signal import convolve2d
""

def main():
    # read inputs
    station=int(os.environ['station'])
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
    obsdata = os.environ['obsdata'] in ['True',1,'true']
    print('read input variables')
    if obsdata:
        outname = os.environ['radar_outname']
        path=data_path
    else:
        path=path.format(var=var,freq=freq_in)
    # read in radar location information from mask file
    print('open mask')
    mask = xr.open_mfdataset(radar_path+f"masks/{station}.nc").rainrate
    mask = mask.rename(longitude='lon',latitude='lat')
    mask['lon'] = np.round(mask['lon'],4)
    mask['lat'] = np.round(mask['lat'],4)
    # to implement: regrid mask to desired grid
    if analysis_grid not in ["AUST04","AUST-04","AUS-04",'AUS-4']:
       print("Interpolation not implemented yet")
    # constrict mask by specified number of grid-cells in order to remove radar edge effects
    window = np.ones((2*boundary_pad+1,2*boundary_pad+1))
    window = window/window.sum()
    mask2=mask.copy(data=convolve2d(mask,
                                    window,
                                    mode='same',
                                    boundary='fill',
                                    fillvalue=1))
    # load in model data
    print("opening "+path+filename.format(var=var,
                                                  station=station,
                                                  freq=freq_in,
                                                  year1="*",
                                                  year2="*",
                                                  month1='*',
                                                  month2='*'))
    data = xr.open_mfdataset(path+filename.format(var=var,
                                                  station=station,
                                                  freq=freq_in,
                                                  year1="*",
                                                  year2="*",
                                                  month1='*',
                                                  month2='*'),chunks={})
    data = data.sel(time=slice(start_year,end_year))
    print('opened')
    try:
       data = data.rename(longitude='lon',latitude='lat')
    except ValueError:
       pass
    data = data.sel(lon=slice(mask2.lon.min(),mask2.lon.max()),
                    lat=slice(mask2.lat.min(),mask2.lat.max()))
    data['lon'] = np.round(data['lon'],4)
    data['lat'] = np.round(data['lat'],4)
    print(data)
    # if neccessary, regrid onto same grid as mask
    # may need optimising if regridding is required
    if not obsdata:
        if len(data.lon) != len(mask2.lon) or len(data.lat) != len(data.lat):
            print("regridding 1")
            data = lib_standards.regrid(data,mask2.to_dataset())
        elif (data.lon.values != mask.lon.values).any() or (data.lat.values != mask.lat.values).any():
             dx_data = np.abs(np.gradient(data.lon.values).mean())
             diff_x = np.abs(data.lon.values - mask2.lon.values).max()
             diff_y = np.abs(data.lat.values - mask2.lat.values).max()
             if max(diff_x,diff_y)/dx_data < 1e-3: # likely a rounding error
                 print("forcing dimension match-up")
                 data['lon'] = mask2['lon']
                 data['lat'] = mask2['lat']
             else:
                 print("regridding 2")
                 data = lib_standards.regrid(data,mask2.to_dataset())
        # assert regridding has worked
        assert (data.lon.values == mask2.lon.values).all()
        assert (data.lat.values == mask2.lat.values).all()
    # apply mask to data
    mask2.load()
    data = data[var].where(mask2==0)
    # resample first (if required), then apply scale factor
    if freq_out != freq_in:
        data = data.resample(time=freq_out).mean()*scale
    else:
        data = data*scale
    # rechunk
    nt,ny,nx = data.shape
    # generate bins
    maxvalue = data.max().load()
    bins = np.arange(0,maxvalue+bin_interval,bin_interval)
    print("bins as follows")
    print(bins)
    # calculate histograms
    hist = histogram(data,bins=bins,dim=['lon','lat']).resample(time='1M').sum()
    # save to output file
    print("histogram computed")
    print(hist)
    if obsdata:
        hist.to_netcdf(f"{outdir}/radar_distributions/{station}_{outname}",encoding = {"histogram_"+var:{'zlib':True}})
    else:
        filename_out = filename.format(var=f"Radar{station}",freq=freq_out,year1=start_year,year2=end_year,month1="01",month2="12")
        hist.to_netcdf(f"{outdir}/radar_distributions/{filename_out}",encoding = {"histogram_"+var:{'zlib':True}})
    print('saved')

main()
