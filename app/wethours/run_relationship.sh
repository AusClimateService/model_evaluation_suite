#!/bin/bash
set -e 
${python_env1}
${python_env2}

cd $suitedir/app/wethours 

python calc_relationship_map.py

