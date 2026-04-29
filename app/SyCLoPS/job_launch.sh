

start=$start_year
end=$end_year

cd $suitedir/app/SyCLoPS 
mkdir -p $logdir/syclops/
if [[ "${file_frequency}" == "monthly" ]]; # if monthly files, submit 1 job per month 
then
    for ((YEAR=start; YEAR<=end; YEAR++)); # first work out start and end months, accounting for mid-year starts
        do
        export YEAR=$YEAR
        if [[ "$start" -eq $end ]];
           then
           m0=$start_month
           m1=$end_month
        elif [[ "$YEAR" -eq $start ]];
           then
           m0=$start_month
           m1=12
        elif [[ "$YEAR" -eq $end ]]; 
           then
           m0=1
           m1=$end_month
        else
           m0=1
           m1=12
        fi       
        for ((MON=$m0; MON<=$m1; MON++)); # iterate through months and submit jobs
            do
            printf -v MONTH "%02d" $MON
            export MONTH=$MONTH
            echo $YEAR $MONTH
            JID=`qsub -P ${compute_project} -q ${syclops_queue} -l walltime=${syclops_walltime} -l mem=${syclops_mem} -l ncpus=${syclops_ncpus}  ${storage_project_list} -N syclops_${YEAR}${MONTH} -V  -o $logdir/syclops/syclops_${YEAR}${MONTH}.out -e $logdir/syclops/syclops_${YEAR}${MONTH}.err  run_parallel.sh`
            echo $JID
            JIDLIST=$JIDLIST:$JID
        done
    done
else
    for ((YEAR=start; YEAR<=end; YEAR++)); # for annual jobs
        do
        export YEAR=$YEAR
        export MONTH=
        JID=`qsub -P ${compute_project} -q ${syclops_queue} -l walltime=${syclops_walltime} -l mem=${syclops_mem} -l ncpus=${syclops_ncpus}  ${storage_project_list} -N syclops_${YEAR}${MONTH} -V  -o $logdir/syclops/syclops_${YEAR}${MONTH}.out -e $logdir/syclops/syclops_${YEAR}${MONTH}.err  run_parallel.sh`
        echo $JID
        JIDLIST=$JIDLIST:$JID
    done
fi

# when all months/years are run, gather together
echo qsub -W depend=afterok$JIDLIST -P ${compute_project} -q ${syclops_queue} -l walltime=${syclops_walltime} -l mem=${syclops_mem} -l ncpus=${syclops_ncpus}  ${storage_project_list} -N syclops_serial -V  -o $logdir/syclops/syclops_serial.out -e $logdir/syclops/syclops_serial.err  run_serial.sh
qsub -W depend=afterok$JIDLIST -P ${compute_project} -q ${syclops_queue} -l walltime=${syclops_walltime} -l mem=${syclops_mem} -l ncpus=${syclops_ncpus}  ${storage_project_list} -N syclops_serial -V  -o $logdir/syclops/syclops_serial.out -e $logdir/syclops/syclops_serial.err  run_serial.sh

