import xarray as xr
import os
import numpy as np
import matplotlib.pyplot as plt
import glob

def integrate(data,surface, surf_coord, coord='pressure',ascending=True):
    """
    Vertically integrate a data-array dealing correctly with masked values beneath the surface.
    Parameters
    ==========
    data: xarray DataArray
        n-dim input data containing coord 'coord'
    surface: xarray DataArray
        (n-1)-dim input data representing surface conditions at coord=surf. 
    surf_coord: xarray DataArray
        (n-1)-dim Value of coord at surface
    coord: string
        Name of coordinate to integrate over
    ascending:
        Whether the surface is at the start (true) or end (False) of the coord. 
        Integral will switch sign if ascend is negative
    Returns
    =======
    xarray DataArray
        (n-1) dim output data containing integrated data
    """
    data = data.sortby(coord,ascending=ascending)
    na_count = np.isnan(data).sum(coord)
    out = data.integrate(coord).fillna(0)
    for i in range(1,na_count.max().values+1):
        out += (na_count==i)*(data.isel({coord:slice(i,None)}).integrate(coord) + (surface + data.isel({coord:i})) * ( data[coord][i] - surf_coord ) /2  ).fillna(0)
    return out


def mse(year, mon, exppath,file_freq,outdir,freq):
    """
    Compute moist static energy budget terms for BARPA
    Input
    =====
    year: int
    month: int
    exppath: string, location of inputs
    file_freq: string, frequency of data files (either monthly or yearly)
    outdir: string, where to save outputs
    """
    data= {}
    # load 3D data
    for var in ['ta','zg','ua','va','wa','hus']:
#    for var in ['ta','zg','hus','ua','va','wa']:
        varlist = glob.glob(exppath.format(freq=freq,var=f'{var}*'))
        varlist = [x.strip('/') for x in varlist]
        varlist = [x.split('/')[-2] for x in varlist]
        varlist = [x for x in varlist if x[-1] in ['0','5']]
        varlist.sort()
        if var == 'hus':
            varlist = ['hus500','hus600','hus700','hus850','hus925','hus1000']
        print(varlist)
        data[var] = []
        for var2 in varlist:
            print(var2)
            if (len(var2) - len(var) )==2:
                continue
            if not (var2[len(var):]).isdigit():
                continue
#            if file_freq=='monthly':
#                data[var].append(xr.open_mfdataset(os.path.join(exppath.format(freq=freq,var=var2),f"*_{year}{mon:02d}*"),chunks={})[var2])
#            else:
            data[var].append(xr.open_mfdataset(os.path.join(exppath.format(freq=freq,var=var2),f"*_{year}*"),chunks={})[var2])
            try:
                data[var][-1] = data[var][-1].drop_vars('crs')
            except:
                pass
            data[var][-1]['pressure'] = int(var2[len(var):])
        data[var] = xr.concat(data[var],'pressure').sortby('pressure').rename(var).transpose('time','pressure','lat','lon')
        data[var]['pressure'] = data[var]['pressure']*100
        data[var] = data[var]
        data[var] = data[var].chunk({'time':1,'pressure':20,'lat':510,'lon':650})
    # load 2D data
    varlist = ['hfls','hfss','rlut','rsut','rsus','rlus','rlds','rsds','clivi','tas','huss','ps','uas','vas','rsdt']
    for var in varlist:
            print(var)
            filepath = os.path.join(exppath.format(var=var,freq=freq),f"*_{year}*")
            data[var]=xr.open_mfdataset(filepath,chunks={})[var]
            data[var] = data[var].chunk({'time':1,'lat':510,'lon':650})
    data['orog'] = xr.open_mfdataset(os.path.join(exppath.format(var='orog',freq='fx'),"*.nc"))['orog']
    # normalise coords
    for var in data:
        data[var]['lon'] = np.round(data[var]['lon'],4)
        data[var]['lat'] = np.round(data[var]['lat'],4)
    # Constants
    cp = 1004.64 # J/kg/K
    cv = 718 # J/kg/K
    Lv = 2501000 # J/kg
    Lf =  334000 
    g=-9.8 # m/s2
    r=6371000
    # kg m2/s3 /m2 = kg/s3 
    # mse
    data['hus'] = xr.broadcast(data['ta'],data['hus'])[1].fillna(0)
    h = cp*data['ta']+Lv*data['hus']-g*data['zg']
    h = h.chunk({'time':1,'pressure':20,'lat':510,'lon':650})
    hs = cp*data['tas']+Lv*data['huss']-g*data['orog']
    hs = hs.chunk({'time':1,'lat':510,'lon':650})
    eps = cv*data['ta']+Lv*data['hus']-g*data['zg']
    eps_s = cv*data['tas']+Lv*data['huss']-g*data['orog']
    # map factors
    yfac = 2*np.pi*r/360
    xfac = 2*np.pi*r/360*np.cos(h.lat*np.pi/180)
    # budget terms
    budget = {}
    budget['Moist Static Energy'] = integrate(eps,eps_s,data['ps'],ascending=False)/g
    budget['Forcing'] = data['hfls']+data['hfss']+data['rlus']+data['rsus']-data['rlds']-data['rsds']+data['rsdt']-data['rlut']-data['rsut']
#    budget['ddt'] = integrate(eps,eps_s,data['ps'],ascending=False).chunk({'time':16}).differentiate('time',datetime_unit='s')/g


    budget['div'] = integrate(data['va']*(h.differentiate('lat')/yfac),data['vas']*(hs.differentiate('lat')/yfac),data['ps'],ascending=False)/g \
                   +integrate(data['ua']*(h.differentiate('lon')/xfac),data['uas']*(hs.differentiate('lon')/xfac),data['ps'],ascending=False)/g
    budget['vert'] = integrate(data['wa']*(data['zg'].differentiate('pressure')) *h.differentiate('pressure'),
                           0*data['ps'],data['ps'],ascending=False)/g
    budget = xr.Dataset(budget)

    budget.to_netcdf(f"{outdir}/mse/mse_{year}.nc", encoding = {var:{'zlib':True} for var in budget})    
                                                                                                                                    
    
if __name__ == "__main__":
    start_year = int(os.environ['start_year'])
    end_year = int(os.environ['end_year'])
    data_path =  os.environ['data_path']
    freq = os.environ['mse_freq']
    file_freq=os.environ['file_frequency']
    outdir=os.environ['outdir']
    mon=1
    for year in np.arange(start_year,end_year+1):
        mse(year,mon,data_path,file_freq,outdir,freq)
