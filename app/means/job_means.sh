#!/bin/bash
module use ${python_module_path}
module load ${python_env}

which python
cd $suitedir/app/means

python means.py --regrid ${means_regrid}
