#!/bin/bash

export ESMFMKFILE=/g/data/xv83/users/bxn599/miniconda3/envs/icclim7.0.0/lib/esmf.mk
cd $suitedir/app/icclim_1hr
all_index_list="${icclim_1hr_indices_prcp}"
mkdir -p $logdir/icclim_1hr
for index in $all_index_list; do
	export index_list=$index
	jobname=index.${index_list/:/_}
	echo "Submit $jobname"
	qsub -P ${compute_project} -q ${icclim_1hr_queue} -l walltime=${icclim_1hr_walltime} -l mem=${icclim_1hr_mem} -l ncpus=${icclim_1hr_ncpus} -l storage=${storage_project_list} -N $jobname  -o $logdir/icclim_1hr/icclim_1hr_${jobname}.out -e $logdir/icclim_1hr/icclim_1hr_${jobname}.err -V job_icclim.sh
#	exit 0
done

