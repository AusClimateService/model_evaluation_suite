#!/bin/bash
${python_env1}
${python_env2}

which python
cd $suitedir/app/stations
mkdir -p $outdir/stations/$var

python extract_model_data.py
