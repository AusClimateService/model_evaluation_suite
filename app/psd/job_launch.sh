#!/bin/bash


cd $suitedir/app/psd
all_var_list="${psd_vars}"
mkdir -p $logdir/psd
for vars in $all_var_list; do
	export var=$vars
#	echo $var
	jobname=psd.${var}
	echo "Submit $jobname"
	qsub -P ${compute_project} -q ${psd_queue} -l walltime=${psd_walltime} -l mem=${psd_mem} -l ncpus=${psd_ncpus} ${storage_project_list} -l jobfs=${psd_jobfs} -N $jobname  -o $logdir/psd/${jobname}.out -e $logdir/psd/${jobname}.err -V job_psd.sh
#	exit 0
done

