

start=$start_year
end=$end_year

cd $suitedir/app/SyCLoPS 
mkdir -p $logdir/syclops/
if [[ "${file_frequency}" == "monthly" ]]; 
then
    for ((YEAR=start; YEAR<=end; YEAR++)); 
        do
        for MONTH in {1..2};
            do
            printf -v MONTH "%02d" $MONTH
            export YEAR=$YEAR
            export MONTH=$MONTH
            JID=`qsub -P ${compute_project} -q ${syclops_queue} -l walltime=${syclops_walltime} -l mem=${syclops_mem} -l ncpus=${syclops_ncpus} -l storage=${storage_project_list} -N syclops_${YEAR}${MON} -V  -o $logdir/syclops/syclops_${year}${mon}.out -e $logdir/syclops/syclops_${year}${mon}.err  run_parallel.sh`
            echo $JID
            JIDLIST=$JIDLIST:$JID
        done
    done
else
    for ((YEAR=start; YEAR<=end; YEAR++)); 
        do
        export YEAR=$YEAR
        export MONTH=
        JID=`qsub -P ${compute_project} -q ${syclops_queue} -l walltime=${syclops_walltime} -l mem=${syclops_mem} -l ncpus=${syclops_ncpus} -l storage=${storage_project_list} -N syclops_${YEAR}${MON} -V  -o $logdir/syclops/syclops_${year}${mon}.out -e $logdir/syclops/syclops_${year}${mon}.err  run_parallel.sh`
        echo $JID
        JIDLIST=$JIDLIST:$JID
    done
fi


echo qsub -W depend=afterok$JIDLIST -P ${compute_project} -q ${syclops_queue} -l walltime=${syclops_walltime} -l mem=${syclops_mem} -l ncpus=${syclops_ncpus} -l storage=${storage_project_list} -N syclops_serial -V  -o $logdir/syclops/syclops_${year}${mon}.out -e $logdir/syclops/syclops_${year}${mon}.err  run_serial.sh
qsub -W depend=afterok$JIDLIST -P ${compute_project} -q ${syclops_queue} -l walltime=${syclops_walltime} -l mem=${syclops_mem} -l ncpus=${syclops_ncpus} -l storage=${storage_project_list} -N syclops_serial -V  -o $logdir/syclops/syclops_${year}${mon}.out -e $logdir/syclops/syclops_${year}${mon}.err  run_serial.sh

