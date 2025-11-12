import geopandas as gp
import spatial_selection
import xarray as xr
import numpy as np
# Domain extents for analysis
DOMAINS = {"CORDEX-AA": (-52.36, 12.21, 89.25, 206.57),  # as per CORDEX definition
           "Australia": (-44.5, -10, 112, 156.25)}  # as per AGCD

# Methods for regridding
REGRID_UPSCALE_METHOD = "conservative"
REGRID_DOWNSCALE_METHOD = "bilinear"
REGRID_UPSCALE_METHOD_WITH_MASK = "conservative_normed"

# AGCD data quality mask
#AGCD_MASK = "/g/data/tp28/dev/evaluation_datasets/awap_mask.nc"
AGCD_MASK = "/g/data/xv83/users/bxn599/ACS/evaluation/AGCDv1_precip_weights_1985-2014_average.nc"


def region_aggregation(ds, aggregator, region=None):
    """
    Inputs:
        ds: xarray.DataArray
            Input data, 2d or 3d
        aggregator: str
            Name of x-array reduction method to apply. Valid entries:
                ['weightmean','all','any','count','cumprod','cumsum','max',
                'mean','median','min','prod','std','sum','ar']
        region: str 
            Choose from, Australia, Northern Australia, Rangelands, Eastern Australia, 
            Southern Australia, Central Slopes, East Coast, Murray Basin, 
            Monsoonal North, Rangelands, Southern Slopes, 
            Southern and South-Western Flatlands, Wet Tropics
    """

    assert(aggregator in ['weightmean', 'all', 'any', 'count', 'cumprod', 'cumsum', 'max', 'mean', 'median', 'min', 'prod', 'std', 'sum', 'ar'])

    dims = ['lat', 'lon']

    if region is not None:
        if aggregator in ['weightmean']:
            mask = get_region_mask(ds, region, method='weight')
        else:
            mask = get_region_mask(ds, region, method='centre')
            mask.values[mask.values == 0] = 1

        if aggregator == 'weightmean':
            result = (mask*ds).where(mask > 0).sum(dims) / mask.sum(dims)
        else:
            result = getattr(ds.where(mask > 0), aggregator)(dims)

    else:
        result = eval('ds.%s()' % aggregator)

    return result

#
# APPLY DOMAIN INFORMATION
#

def get_subnrm_names():
    """
    Returns the labelling names of the various NRM sub regions.
    
    Returns:
        list of str
    """
    #return ['Wet Tropics', 'Rangelands (North)', 'Monsoonal North (East)',\
    #   'Monsoonal North (West)', 'East Coast (South)', 'Central Slopes',\
    #   'Murray Basin', 'Southern and South Western Flatlands (West)',\
    #   'Southern and South Western Flatlands (East)',\
    #   'Southern Slopes (Vic/NSW East)', 'Southern Slopes (Vic West)',\
    #   'Southern Slopes (Tas East)', 'Southern Slopes (Tas West)',\
    #   'East Coast (North)', 'Rangelands (South)']
    return ['Southern Slopes (Vic/NSW East)', 'Southern Slopes (Vic West)',\
       'Southern Slopes (Tas East)', 'Southern Slopes (Tas West)',\
       'Murray Basin', 'Southern and South Western Flatlands (West)',\
       'Southern and South Western Flatlands (East)',\
       'Central Slopes', 'East Coast (South)', 'East Coast (North)', \
       'Rangelands (South)', 'Rangelands (North)', \
       'Monsoonal North (East)', 'Monsoonal North (West)', \
       'Wet Tropics']

def get_nrm_names():
    """
    Returns the labelling names of the various NRM cluster egions.
    
    Returns:
        list of str
    """
    #return ['Central Slopes', 'East Coast', 'Monsoonal North', 'Murray Basin',\
    #   'Rangelands', 'Southern Slopes', 'Southern and South Western Flatlands', 'Wet Tropics']
    return ['Southern Slopes', 'Murray Basin', \
            'Southern and South Western Flatlands', 'Central Slopes', \
            'East Coast', 'Rangelands', 'Monsoonal North', 'Wet Tropics']

def get_supernrm_names():
    """
    Returns the labelling names of the various Super NRM regions.
    
    Returns:
        list of str
    """
    #return ['Eastern Australia', 'Northern Australia', 'Rangelands','Southern Australia']
    return ['Southern Australia', 'Eastern Australia', 'Rangelands', 'Northern Australia']

def get_coastline_names():
    """
    Returns the labelling names of the various coastline regions.
    
    Returns:
        list of str
    """
    return ['Coastline Australia 100km']

def get_topography_names():
    """
    Returns the labelling names of the various topography regions.
    
    Returns:
        list of str
    """
    return ['Topography Australia 500']

def get_state_names():
    """
    Returns the labelling names of states and territories.
    
    Returns:
        list of str
    """
    return ['Queensland', 'New South Wales', \
            'Australian Capital Territory', 'Victoria', 'Tasmania',\
            'South Australia', 'Western Australia', 'Northern Territory', 'Other Territories']
    
def get_subnrm_shape(name):
    """
    Returns the GeoDataFrame of the selected NRM sub region.
    
    Returns:
        GeoDataFrame
    """
    SHP_NRM = "/g/data/ia39/aus-ref-clim-data-nci/shapefiles/data/nrm_regions/nrm_regions.shp"
    SUBNRM_SHAPE = gp.read_file(SHP_NRM)
    
    nrm_names = list(SUBNRM_SHAPE.SubClusNm.values) +['All']
    assert name in nrm_names, "Unknown NRM, only from {:}".format(nrm_names)
    
    index = nrm_names.index(name)
    
    if name == 'All':
        return SUBNRM_SHAPE
    return SUBNRM_SHAPE.iloc[[index]]

def get_nrm_shape(name):
    """
    Returns the GeoDataFrame of the selected NRM region.
    
    Returns:
        GeoDataFrame
    """
    SHP_NRM = "/g/data/ia39/aus-ref-clim-data-nci/shapefiles/data/nrm_regions/nrm_regions.shp"
    # NRM sub clusters
    SUBNRM_SHAPE = gp.read_file(SHP_NRM)
    # NRM clusters
    NRM_SHAPE = SUBNRM_SHAPE.dissolve(by='ClusterNm', as_index=False)
    NRM_SHAPE = NRM_SHAPE.drop(columns=['SubClusNm', 'SubClusAb'])
    NRM_SHAPE = NRM_SHAPE[['ClusterNm', 'ClusterAb', 'SupClusNm', 'SupClusAb', 'geometry']]
    
    nrm_names = list(NRM_SHAPE.ClusterNm.values) + ['All']
    assert name in nrm_names, "Unknown NRM, only from {:}".format(nrm_names)
    
    index = nrm_names.index(name)
    
    if name == 'All':
        return NRM_SHAPE
    return NRM_SHAPE.iloc[[index]]
    
def get_supernrm_shape(name):
    """
    Returns the GeoDataFrame of the selected Super NRM region.
    
    Returns:
        GeoDataFrame
    """
    # Regions
    SHP_NRM = "/g/data/ia39/aus-ref-clim-data-nci/shapefiles/data/nrm_regions/nrm_regions.shp"
    
    # NRM sub clusters
    SUBNRM_SHAPE = gp.read_file(SHP_NRM)
    # NRM clusters
    NRM_SHAPE = SUBNRM_SHAPE.dissolve(by='ClusterNm', as_index=False)
    NRM_SHAPE = NRM_SHAPE.drop(columns=['SubClusNm', 'SubClusAb'])
    NRM_SHAPE = NRM_SHAPE[['ClusterNm', 'ClusterAb', 'SupClusNm', 'SupClusAb', 'geometry']]
    # NRM superclusters
    SUPNRM_SHAPE = NRM_SHAPE.dissolve(by='SupClusNm', as_index=False)
    SUPNRM_SHAPE = SUPNRM_SHAPE.drop(columns=['ClusterNm', 'ClusterAb'])
    SUPNRM_SHAPE = SUPNRM_SHAPE[['SupClusNm', 'SupClusAb', 'geometry']]

    if name == 'All':
        return SUPNRM_SHAPE
        
    nrm_names = list(SUPNRM_SHAPE.SupClusNm.values)
    assert name in nrm_names, "Unknown NRM, only from {:}".format(nrm_names)
    
    index = nrm_names.index(name)
    
    return SUPNRM_SHAPE.iloc[[index]]

def get_coastline_shape(name):
    """
    Returns the GeoDataFrame of the selected coastline.
    
    Returns:
        GeoDataFrame
    """
    coast_names = get_coastline_names()
    assert name in coast_names, "Unknown NRM, only from {:}".format(coast_names)
    
    index = coast_names.index(name)
    # Regions
    if name == "Coastline Australia 100km":
        SHP_COAST = "/g/data/ia39/aus-ref-clim-data-nci/shapefiles/data/aus_coastline/australia_coastline_100km.shp"
    else:
        assert False, f"{name} not found in coastline regions!"
    COAST_SHAPE = gp.read_file(SHP_COAST)
    return COAST_SHAPE

def get_topography_shape(name):
    """
    Returns the GeoDataFrame of the selected topography.
    
    Returns:
        GeoDataFrame
    """
    topography_names = get_topography_names()
    assert name in topography_names, "Unknown NRM, only from {:}".format(topography_names)
    
    index = topography_names.index(name)
    # Regions
    if name == "Topography Australia 500":
        SHP_COAST = "/g/data/ia39/aus-ref-clim-data-nci/shapefiles/data/aus_topo/australia_topography_higher500.shp"
    else:
        assert False, f"{name} not found in topography regions!"
    COAST_SHAPE = gp.read_file(SHP_COAST)
    return COAST_SHAPE

def get_state_shape(name):
    SHP_STATE = "/g/data/ia39/aus-ref-clim-data-nci/shapefiles/data/aus_states_territories/aus_states_territories.shp"
    # States and Territories
    STATE_SHAPE = gp.read_file(SHP_STATE)
    STATE_SHAPE = STATE_SHAPE.dissolve(by='STE_NAME21', as_index=False)

    state_names = list(STATE_SHAPE.STE_NAME21.values) + ['All']
    assert name in state_names, "Unknown NRM, only from {:}".format(state_names)
    
    index = state_names.index(name)
    if name == 'All':
        return STATE_SHAPE
    return STATE_SHAPE.iloc[[index]]
    
def get_region_shape(region):
    available_regions = ['Australia'] + get_supernrm_names() + get_subnrm_names() + get_nrm_names() + get_coastline_names() + get_topography_names() + get_state_names()
    assert region in available_regions, "Unknown region {:}: {:}".format(region, available_regions)
    
    if region == 'Australia':
        SHP_AUS = "/g/data/ia39/aus-ref-clim-data-nci/shapefiles/data/australia/australia.shp"
        AUS_SHAPE = gp.read_file(SHP_AUS)
        return AUS_SHAPE
    elif region in get_subnrm_names():
        return get_subnrm_shape(region)
    elif region in get_nrm_names():
        return get_nrm_shape(region)
    elif region in get_supernrm_names():
        return get_supernrm_shape(region)
    elif region in get_coastline_names():
        return get_coastline_shape(region)
    elif region in get_topography_names():
        return get_topography_shape(region)
    elif region in get_state_names():
        return get_state_shape(region)
     
def apply_region_mask(ds, region, overlap_fraction=None):
    """
    Masks the xarray.DataArray to return data over specific regions.
    
    Inputs:
        ds: xarray.DataArray
            Input data to be masked
        regions: str
            Region to be masked. 
            Choose from, Australia, 
            
            or sub-NRM clusters: {Wet Tropics, Rangelands (North), Monsoonal North (East), Monsoonal North (West), East Coast (South), Central Slopes, Murray Basin, Southern and South Western Flatlands (West), Southern and South Western Flatlands (East), Southern Slopes (Vic/NSW East), Southern Slopes (Vic West), Southern Slopes (Tas East), Southern Slopes (Tas West), East Coast (North), Rangelands (South)}
            
            or NRM clusters: {Central Slopes, East Coast, Monsoonal North, Murray Basin, Rangelands, Southern Slopes, Southern and South Western Flatlands, Wet Tropics}
            
            or super NRM clusters: {Eastern Australia, Northern Australia, Rangelands, Southern Australia}
            
        overlap_fraction: float
            Fraction that a grid cell must overlap with a shape to be included.
            If no fraction is provided, grid cells are selected if their centre
            point falls within the shape.

    Returns:
        xarray.DataArray
    """    
    ds_out = ds
    region_shape = get_region_shape(region)
    ds_out = spatial_selection.select_shapefile_regions(ds, region_shape, overlap_fraction=overlap_fraction)
    
    return ds_out

def add_region_land_mask(ds, region):
    """
    Add a dataarray named mask to the input xarray.DataArray.
    
    Inputs:
        ds: xarray.DataArray
            Input data to be masked
        region: str
            Choose from, Australia, 
            
            or sub-NRM clusters: {Wet Tropics, Rangelands (North), Monsoonal North (East), Monsoonal North (West), East Coast (South), Central Slopes, Murray Basin, Southern and South Western Flatlands (West), Southern and South Western Flatlands (East), Southern Slopes (Vic/NSW East), Southern Slopes (Vic West), Southern Slopes (Tas East), Southern Slopes (Tas West), East Coast (North), Rangelands (South)}
            
            or NRM clusters: {Central Slopes, East Coast, Monsoonal North, Murray Basin, Rangelands, Southern Slopes, Southern and South Western Flatlands, Wet Tropics}
            
            or super NRM clusters: {Eastern Australia, Northern Australia, Rangelands, Southern Australia}
    Returns:
        xarray.DataArray
    """

    ds_out = ds
    mask = get_region_mask(ds, region)
    mask_binary = np.where(np.isnan(mask), 0, 1)
    ds_out['mask'] = (["lat", "lon"], mask_binary)
        
    return ds_out

def get_region_mask(ds, region, method='centre', overlap_fraction=0.5):
    """
    Returns a land mask for a given region.

    Inputs:
        ds: xarray.DataArray
            Input data to be masked
        region: str
            Choose from, Australia, 
            
            or sub-NRM clusters: {Wet Tropics, Rangelands (North), Monsoonal North (East), Monsoonal North (West), East Coast (South), Central Slopes, Murray Basin, Southern and South Western Flatlands (West), Southern and South Western Flatlands (East), Southern Slopes (Vic/NSW East), Southern Slopes (Vic West), Southern Slopes (Tas East), Southern Slopes (Tas West), East Coast (North), Rangelands (South)}
            
            or NRM clusters: {Central Slopes, East Coast, Monsoonal North, Murray Basin, Rangelands, Southern Slopes, Southern and South Western Flatlands, Wet Tropics}
            
            or super NRM clusters: {Eastern Australia, Northern Australia, Rangelands, Southern Australia}
        overlap_fraction: float
            Fraction that a grid cell must overlap with a shape to be included.
            If no fraction is provided, grid cells are selected if their centre
            point falls within the shape.
    Returns:
        xarray.DataArray
    """

    region_shape = get_region_shape(region)
    
    lat = ds['lat'].values
    lon = ds['lon'].values

    if method == 'centre':
        mask_values = spatial_selection.centre_mask(region_shape, lon, lat, output="2D")
    elif method == 'overlap':
        mask_values = spatial_selection.fraction_overlap_mask(region_shape, lon, lat, overlap_fraction)
    elif method == 'weight':
        mask_values = spatial_selection.fraction_weight_mask(region_shape, lon, lat)
    
    ds_mask = xr.DataArray(
        data = mask_values,
        dims = ["lat", "lon"],
        coords = dict(
            lat = (["lat"], lat),
            lon = (["lon"], lon)
        ),
        name = 'mask'
    )
    
    return ds_mask

def apply_agcd_data_mask(ds):
    """
    Apply masking based on AGCD data quality mask
    Inputs:
        ds: xarray.dataset
    Output:
        xarray.dataset
            The same dataarray but with the mask applied.
    """
    amask = xr.open_dataset(AGCD_MASK)
    amask_regrid = amask['data_mask'].interp_like(ds, method='nearest')
    return ds.where(amask_regrid == 1)
