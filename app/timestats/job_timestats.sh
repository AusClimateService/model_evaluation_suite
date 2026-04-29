#!/bin/bash
${python_env1}
${python_env2}
which python
cd $suitedir/app/timestats

python timestats.py --regrid ${timestats_regrid}
