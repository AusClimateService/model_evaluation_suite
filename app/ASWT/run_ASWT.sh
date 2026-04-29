#!/bin/bash
set -e 

${python_env1}
${python_env2}

which python

cd $suitedir/app/ASWT

/g/data/access/ngm/miniconda3/envs/analysis3-21.10/bin/python  assign.py

