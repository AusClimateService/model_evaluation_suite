#!/bin/bash

mkdir -p ${outdir}/aswt/
mkdir -p ${logdir}/aswt
start=$start_year
end=$end_year

#for ((year=start; year<=end; year++)); do
#         export year=$year
#         export mon=1
#         echo $year $mon
qsub -P ${compute_project} -q ${aswt_queue} -l walltime=${aswt_walltime} -l mem=${aswt_mem} -l jobfs=${aswt_jobfs} -l ncpus=${aswt_ncpus} -l storage=${storage_project_list} -N aswt_${GCM} -o $logdir/aswt/aswt_${year}${mon}.out -e $logdir/aswt/aswt_${GCM}.err -V $suitedir/app/ASWT/run_ASWT.sh
#done
