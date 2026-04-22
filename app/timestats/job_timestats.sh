#!/bin/bash
module use ${python_module_path}
module load ${python_env}

which python
cd $suitedir/app/timestats

python timestats.py --regrid ${timestats_regrid}
