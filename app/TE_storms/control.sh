

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
            sh run_parallel.sh > $logdir/log_${YEAR}_$MONTH 2> $logdir/TE_storms/err_${YEAR}_$MONTH  &
        done
    done
else
    for ((YEAR=start; YEAR<=end; YEAR++)); 
        do
        export YEAR=$YEAR
        export MONTH=
        sh run_parallel.sh  > $logdir/log_${YEAR}_$MONTH 2> $logdir/TE_storms/err_${YEAR}_$MONTH  &
    done
fi

echo "waiting for all tasks to finish"
wait
sh run_serial.sh > $logdir/TE_storms/log_serial 2> $logdir/TE_storms/err_serial
echo "complete"

