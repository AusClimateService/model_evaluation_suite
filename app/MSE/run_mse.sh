#!/bin/bash
set -x 
module use ${python_module_path}
module load ${python_env}

which python
cd $suitedir/app/MSE

/g/data/access/ngm/miniconda3/envs/analysis3-21.10/bin/python mse_flux.py 


