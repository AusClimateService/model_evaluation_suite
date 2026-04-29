#!/bin/bash
${python_env}

which python
cd $suitedir/app/timestats

python timestats.py --regrid ${timestats_regrid}
