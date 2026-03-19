#!/bin/bash


cd $suitedir/app/stations
all_var_list="${stations_vars}"
mkdir -p $logdir/stations
mkdir -p $outdir/stations
for vars in $all_var_list; do
	export var=$vars
#	echo $var
	jobname=stations.${var}
	echo "Submit $jobname"
	qsub -P ${compute_project} -q ${stations_queue} -l walltime=${stations_walltime} -l mem=${stations_mem} -l ncpus=${stations_ncpus} -l storage=${storage_project_list} -l jobfs=${stations_jobfs} -N $jobname  -o $logdir/stations/${jobname}.out -e $logdir/stations/${jobname}.err -V job_stations.sh
#	exit 0
done

