#!/bin/bash
${python_env1}
${python_env2}

which python
cd $suitedir/app/lag1_corr

python lag1_corr.py --regrid ${lag1_corr_regrid}
