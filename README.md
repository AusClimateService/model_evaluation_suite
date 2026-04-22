# model_evaluation_suite
Combined repository for automated, aggregated evaluation of ACS regional climate models. Intended for benchmarking CPM and ML developments

# App List


| Name | Description | Status | Observations | Notes | Reference |
| --- | --- | --- | --- | --- | --- |
| ASWT | Australian Synoptic Weather Types | Complete | ERA5 (precomputed by authors) | Only relevant for Australian domain | [Paper](https://doi.org/10.1029/2025JD043873), [Github](https://github.com/21centuryweather/Australian-synoptic-weather-types) 
| MSE | Moist static energy | 90% | ERA5 (gadi dependent) | Fairly inconclusive | |
| SyCLoPS | Tempest Extremes low pressure classifier | Complete | ERA5 (precomputed by authors), IBTrACS | Needs up-to-date (2026) installation of [Tempest Extremes](https://github.com/ClimateGlobalChange/tempestextremes) | [paper](https://agupubs.onlinelibrary.wiley.com/doi/10.1029/2024JD041287) [doc](https://climate.ucdavis.edu/syclops.php) |
| TE_storms | Tempest Extremes updraft helicity tracker | 90% | BARRA, ACCESS-CE |  slow on a large domain. Needs [Tempest Extremes](https://github.com/ClimateGlobalChange/tempestextremes) | N/A |
| icclim | Rainfall and temperature climate indices | Complete |  Gridded rainfall and temperature products | Needs icclim python library installed in conda environment | [icclim](https://icclim.readthedocs.io/en/stable/) | 
| icclim_1hr | Attempt to apply icclim indices to hourly data | Some bugs | BARRA-C2. Ideally BRAIN | units are mm/day rather than mm/hr | [icclim](https://icclim.readthedocs.io/en/stable/) |
| timestats | Compute seasonal, annual and climatological monthly means, maxes, mins, quantiles and threshold exceedance | Complete | BARRA, AGCD. ERA5 not implemented yet | Used for sensitivity analysis as well as obs comparison | N/A |
| radar distributions | Subset to radar domain and compute histogram | Complete | Rainrates derived from radars | Radars regridded to model grid offline. NCI specific without some work | N/A |
| stations | extract data at station locations | 90% | Station data | Needs input csv/netcdf with coords lat, lon and (if CSV) station | N/A |
| wethours | extract dewpoint and rainfall at hours with rainfall above threshold | Complete | Station data |Intended for dewpoint/extreme rainfall comparison | N/A |
| xclim | Compute bespoke temperature indices not found in icclim | Complete | Needs python library: check with Benjamin Ng or see ref | Gridded temperature data (e.g. AGCD) | [xclim](https://xclim.readthedocs.io/en/stable/) |
# To do 
* Add app to calculate seasonal means, quantiles, threshold exceedances
* Finish adding AGCDv1 indices
* Change filepath handling: add string replacement so we can remove hardcoded addition of {freq}/{var}/vXXXXXXXX/
* Add additional evaluation tools (as per planner)
* Add Jupyter notebooks (consider papermill)
* Extend to reference datasets
* Add CCAM optional configurations
* Add BARPA-R optional configurations
* Add documentation


# Recent updates
* Added rainfall distributions
& Handles obs: AGCDv2 rainfall indices, Radar distributions
