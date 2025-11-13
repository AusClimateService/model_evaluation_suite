#!/bin/bash

export ESMFMKFILE=/g/data/xv83/users/bxn599/miniconda3/envs/icclim7.0.0/lib/esmf.mk
cd $suitedir/app/xclim
all_index_list="${xclim_indices_tasmax} ${xclim_indices_tasmin} ${xclim_indices_prcp}"
mkdir -p $logdir/xclim
for index in $all_index_list; do
	export index_list=$index
	echo $index_list
	jobname=index.${index_list//[: ]/_}
	echo "Submit $jobname"
	qsub -P ${compute_project} -q ${xclim_queue} -l walltime=${xclim_walltime} -l mem=${xclim_mem} -l ncpus=${xclim_ncpus} -l storage=${storage_project_list} -N $jobname  -o $logdir/xclim/xclim_${jobname}.out -e $logdir/xclim/xclim_${jobname}.err -V job_xclim.sh
#	exit 0
done

