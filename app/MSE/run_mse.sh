#!/bin/bash
set -x 
module use ${python_module_path}
module load ${python_env}

which python
cd $suitedir/app/MSE

python mse_flux.py 


