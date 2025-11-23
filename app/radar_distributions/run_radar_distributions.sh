#!/bin/bash
module use ${python_module_path}
module load ${python_env}

which python
cd $suitedir/app/radar_distributions

python extract_radar_distributions.py > ${logdir}/radar/stdout_${station}.txt


~                                                                               
~                                                        
