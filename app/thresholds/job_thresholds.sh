#!/bin/bash
module use ${python_module_path}
module load ${python_env}

which python
cd $suitedir/app/thresholds
python -i thresholds.py --regrid ${thresholds_regrid}
