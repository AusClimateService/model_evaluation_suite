

start=$start_year
end=$end_year

cd $suitedir/app/TE_storms
mkdir -p $logdir/TE_storms/
if [[ "${file_frequency}" == "monthly" ]]; 
then
    for ((YEAR=start; YEAR<=end; YEAR++)); 
        do
        for MONTH in {1..12};
            do
            printf -v MONTH "%02d" $MONTH
            export YEAR=$YEAR
            export MONTH=$MONTH
            echo qsub -P ${compute_project} -q ${TE_storms_queue} -l walltime=${TE_storms_walltime} -l mem=${TE_storms_mem} -l ncpus=${TE_storms_ncpus}  ${storage_project_list} -N TE_storms_${YEAR}${MON} -V  -o $logdir/TE_storms/TE_storms_${YEAR}.out -e $logdir/TE_storms/TE_storms_${YEAR}.err run_parallel.sh
            JID=`qsub -P ${compute_project} -q ${TE_storms_queue} -l walltime=${TE_storms_walltime} -l mem=${TE_storms_mem} -l ncpus=${TE_storms_ncpus}  ${storage_project_list} -N TE_storms_${YEAR}${MON} -V  -o $logdir/TE_storms/TE_storms_${YEAR}.out -e $logdir/TE_storms/TE_storms_${YEAR}.err run_parallel.sh`
            echo $JID
            JIDLIST=$JIDLIST:$JID
        done
    done
else
    for ((YEAR=start; YEAR<=end; YEAR++)); 
        do
        export YEAR=$YEAR
        export MONTH=
        JID=`qsub -P ${compute_project} -q ${TE_storms_queue} -l walltime=${TE_storms_walltime} -l mem=${TE_storms_mem} -l ncpus=${TE_storms_ncpus}  ${storage_project_list} -N TE_storms_${YEAR}${MON} -V  -o $logdir/TE_storms/TE_storms_${YEAR}.out -e $logdir/TE_storms/TE_storms_${YEAR}.err  run_parallel.sh`
        echo $JID
        JIDLIST=$JIDLIST:$JID
    done
fi


echo qsub -W depend=afterok$JIDLIST -P ${compute_project} -q ${TE_storms_queue} -l walltime=${TE_storms_walltime} -l mem=${TE_storms_mem} -l ncpus=${TE_storms_ncpus}  ${storage_project_list} -N TE_storms_serial -V  -o $logdir/TE_storms/TE_storms_serial.out -e $logdir/TE_storms/TE_storms_serial.err  run_serial.sh
qsub -W depend=afterok$JIDLIST -P ${compute_project} -q ${TE_storms_queue} -l walltime=${TE_storms_walltime} -l mem=${TE_storms_mem} -l ncpus=${TE_storms_ncpus}  ${storage_project_list} -N TE_storms_serial -V  -o $logdir/TE_storms/TE_storms_serial.out -e $logdir/TE_storms/TE_storms_serial.err  run_serial.sh

