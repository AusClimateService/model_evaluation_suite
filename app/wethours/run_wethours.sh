#!/bin/bash
set -e 
${python_env1}
${python_env2}

which python

cd $suitedir/app/wethours 

python extract_wet_hours.py

