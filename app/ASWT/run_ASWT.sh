#!/bin/bash
set -e 

${python_env}

which python

cd $suitedir/app/ASWT

/g/data/access/ngm/miniconda3/envs/analysis3-21.10/bin/python  assign.py

