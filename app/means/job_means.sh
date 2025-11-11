#!/bin/bash
module use /g/data/xp65/public/modules
module load conda/analysis3-25.10

which python
cd $suitedir/app/means

/g/data/xp65/public/apps/med_conda_scripts/analysis3-25.10.d/bin/python means.py
