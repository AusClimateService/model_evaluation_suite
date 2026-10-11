#!/bin/bash
${python_env1}
${python_env2}

which python
cd $suitedir/app/psd

python psd.py --regrid ${psd_regrid}
