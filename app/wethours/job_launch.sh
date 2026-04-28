
start=$start_year
end=$end_year

cd $suitedir/app/wethours 
mkdir -p $logdir/wethours
mkdir -p $outdir/wethours
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
        for ((MON=1; MON<=12; MON++)); # iterate through months and submit jobs
            do
            printf -v MONTH "%02d" $MON
            export MONTH=$MONTH
            echo $YEAR $MONTH
            JID=`qsub -P ${compute_project} -q ${wethours_queue} -l walltime=${wethours_walltime} -l mem=${wethours_mem} -l ncpus=${wethours_ncpus} -N wethours_${YEAR}${MONTH} -V  -o $logdir/wethours/wethours_${YEAR}${MONTH}.out -e $logdir/wethours/wethours_${YEAR}${MONTH}.err  run_wethours.sh`
            echo $JID
            JIDLIST=$JIDLIST:$JID
        done
    done

