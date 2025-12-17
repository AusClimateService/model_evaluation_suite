

start=$start_year
end=$end_year

cd $suitedir/app/TE_storms
for MONTH in {1..12};
    do
    printf -v MONTH "%02d" $MONTH
    export MONTH=$MONTH
    echo "sh run_parallel.sh > $logdir/log_${YEAR}_$MONTH 2> $logdir/TE_storms/err_${YEAR}_$MONTH"  
    sh run_parallel.sh > $logdir/log_${YEAR}_$MONTH 2> $logdir/TE_storms/err_${YEAR}_$MONTH  &
done

wait

