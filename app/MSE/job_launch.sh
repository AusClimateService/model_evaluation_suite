#!/bin/bash

mkdir -p ${outdir}/mse/
mkdir -p ${logdir}/mse
start=$start_year
end=$end_year

#for ((year=start; year<=end; year++)); do
#         export year=$year
#         export mon=1
#         echo $year $mon
qsub -P ${compute_project} -q ${mse_queue} -l walltime=${mse_walltime} -l mem=${mse_mem} -l jobfs=${mse_jobfs} -l ncpus=${mse_ncpus} -l storage=${storage_project_list} -N mse_${GCM} -o $logdir/mse/mse_${year}${mon}.out -e $logdir/mse/mse_${GCM}.err -V $suitedir/app/MSE/run_mse.sh
#done
