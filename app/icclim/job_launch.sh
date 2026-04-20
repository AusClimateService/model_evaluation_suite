#!/bin/bash

export ESMFMKFILE=/g/data/xv83/users/bxn599/miniconda3/envs/icclim7.0.0/lib/esmf.mk
cd $suitedir/app/icclim
all_index_list="${icclim_indices_tasmax} ${icclim_indices_tasmin} ${icclim_indices_prcp}"
mkdir -p $logdir/icclim
for index in $all_index_list; do
	export index_list=$index
	jobname=index.${index_list/:/_}
	echo "Submit $jobname"
	qsub -P ${compute_project} -q ${icclim_queue} -l walltime=${icclim_walltime} -l mem=${icclim_mem} -l ncpus=${icclim_ncpus}  ${storage_project_list} -N $jobname  -o $logdir/icclim/icclim_${jobname}.out -e $logdir/icclim/icclim_${jobname}.err -V job_icclim.sh
#	exit 0
done

