#!/bin/bash

mkdir -p ${outdir}/mse/
mkdir -p ${logdir}/mse
start=$start_year
end=$end_year

for ((year=start; year<=end; year++)); do
    for mon in {3..12}; do
         export year=$year
         export mon=$mon
         echo $year $mon
         qsub -P ${compute_project} -q ${mse_queue} -l walltime=${mse_walltime} -l mem=${mse_mem} -l jobfs=${mse_jobfs} -l ncpus=${mse_ncpus} -l storage=${storage_project_list} -N mse_${year}${mon} -o $logdir/mse/mse_${year}${mon}.out -e $logdir/mse/mse_${year}${mon}.err -V $suitedir/app/MSE/run_mse.sh
    done
done
