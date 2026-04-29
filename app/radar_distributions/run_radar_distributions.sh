#!/bin/bash

${python_env}

which python
cd $suitedir/app/radar_distributions

python extract_radar_distributions.py > ${logdir}/radar/stdout_${station}.txt


~                                                                               
~                                                        
