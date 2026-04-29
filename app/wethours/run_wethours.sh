#!/bin/bash
set -e 
#echo module use ${python_module_path}
#module use ${python_module_path}
#echo module load ${python_env}
#module load ${python_env}

#which python

# activating python environment
source ~/.myconda
conda activate research

cd $suitedir/app/wethours 

python extract_wet_hours.py

