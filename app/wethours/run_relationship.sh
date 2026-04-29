#!/bin/bash
set -e 
${python_env}

which python

cd $suitedir/app/wethours 

python calc_relationship_map.py

