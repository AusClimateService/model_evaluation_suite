#!/bin/bash


cd $suitedir/app/thresholds
all_var_list="${thresholds_vars}"
mkdir -p $logdir/thresholds
for vars in $all_var_list; do
	export var=$vars
#	echo $var
#	jobname=${thresholds_oper}.${var}
        jobname=`echo $var | sed 's/:/./g'`
        jobname=`echo $jobname | sed 's/&/./g'`
        jobname=`echo $jobname | sed 's/|/./g'`
        
	echo "Submit $jobname"
	qsub -P ${compute_project} -q ${thresholds_queue} -l walltime=${thresholds_walltime} -l mem=${thresholds_mem} -l ncpus=${thresholds_ncpus} ${storage_project_list} -l jobfs=${thresholds_jobfs} -N $jobname  -o $logdir/thresholds/${jobname}.out -e $logdir/thresholds/${jobname}.err -V job_thresholds.sh
#	exit 0
done

