#!/bin/bash


cd $suitedir/app/means
all_var_list="${means_vars}"
mkdir -p $logdir/means
for vars in $all_var_list; do
	export var=$vars
#	echo $var
	jobname=${means_oper}.${var}
	echo "Submit $jobname"
	qsub -P ${compute_project} -q ${means_queue} -l walltime=${means_walltime} -l mem=${means_mem} -l ncpus=${means_ncpus} ${storage_project_list} -l jobfs=${means_jobfs} -N $jobname  -o $logdir/means/${jobname}.out -e $logdir/means/${jobname}.err -V job_means.sh
#	exit 0
done

