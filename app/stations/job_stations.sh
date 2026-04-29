#!/bin/bash
${python_env}

which python
cd $suitedir/app/stations
mkdir -p $outdir/stations/$var

python extract_model_data.py
