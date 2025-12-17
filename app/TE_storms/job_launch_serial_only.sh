# launch serial syclops task manually. For occasional manual use when -W dependencies fail for whatever reason

source ../../suite.conf

qsub -P ${compute_project} -q ${syclops_queue} -l walltime=${syclops_walltime} -l mem=${syclops_mem} -l ncpus=${syclops_ncpus} -l storage=${storage_project_list} -N syclops_${YEAR}${MON} -V  -o $logdir/syclops/syclops_serial.out -e $logdir/syclops/syclops_serial.err  run_serial.sh
