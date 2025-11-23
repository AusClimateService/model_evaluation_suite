#!/bin/bash

mkdir -p ${outdir}/radar_distributions/
mkdir -p ${logdir}/radar



for station in $radar_station_list; do
         export station=$station
         echo $station
         qsub -P ${compute_project} -q ${radar_queue} -l walltime=${radar_walltime} -l mem=${radar_mem} -l jobfs=${radar_jobfs} -l ncpus=${radar_ncpus} -l storage=${storage_project_list} -N radar_${station} -o $logdir/radar/radar_${station}.out -e $logdir/radar/radar_${station}.err -V $suitedir/app/radar_distributions/run_radar_distributions.sh
done
