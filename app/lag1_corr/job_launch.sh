#!/bin/bash


cd $suitedir/app/lag1_corr
all_var_list="${lag1_corr_vars}"
mkdir -p $logdir/lag1_corr
for vars in $all_var_list; do
	export var=$vars
#	echo $var
	jobname=lag1_corr.${var}
	echo "Submit $jobname"
	qsub -P ${compute_project} -q ${lag1_corr_queue} -l walltime=${lag1_corr_walltime} -l mem=${lag1_corr_mem} -l ncpus=${lag1_corr_ncpus} ${storage_project_list} -l jobfs=${lag1_corr_jobfs} -N $jobname  -o $logdir/lag1_corr/${jobname}.out -e $logdir/lag1_corr/${jobname}.err -V job_lag1_corr.sh
#	exit 0
done

