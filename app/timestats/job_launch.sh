#!/bin/bash


cd $suitedir/app/timestats
all_var_list="${timestats_vars}"
mkdir -p $logdir/timestats
for vars in $all_var_list; do
	export var=$vars
#	echo $var
#	jobname=${timestats_oper}.${var}
        jobname=`echo $var | sed 's/:/./g'`
        
	echo "Submit $jobname"
	qsub -P ${compute_project} -q ${timestats_queue} -l walltime=${timestats_walltime} -l mem=${timestats_mem} -l ncpus=${timestats_ncpus} ${storage_project_list} -l jobfs=${timestats_jobfs} -N $jobname  -o $logdir/timestats/${jobname}.out -e $logdir/timestats/${jobname}.err -V job_timestats.sh
#	exit 0
done

