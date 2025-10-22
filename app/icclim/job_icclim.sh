#!/bin/bash

# Script definition
icclim_path=$suitedir/app/icclim
###script="/g/data/xv83/dbi599/miniconda3/envs/icclim/bin/python  ${icclim_path}/run_icclim.py"
script="/g/data/xv83/users/bxn599/miniconda3/envs/icclim7.0.0/bin/python ${icclim_path}/run_icclim.py"
indir=$data_path/day
label="${domain}_${gcm}_${scenario}_${realisation}_${institution}_${rcm2}_v1-r1"
TIME_PERIOD="${start_year}-01-01 ${end_year}-12-31"

echo $index_list
for var_index in $index_list; do
	index=`echo $var_index | cut -d':' -f2`
	var_list=`echo $var_index | cut -d':' -f1`
	var_list=${var_list/&/ }
	echo $var_list
	outdir=$outdir/climdex/${index}
        mkdir -p ${outdir} || true

        cmd="${script}"
#	cmd="${script} --regrid ${icclim_template} --slice_mode ${icclim_slice_mode} --verbose"

#	if [ "${TIME_PERIOD}" != "" ]; then
#                start_date=`echo $TIME_PERIOD | cut -d' ' -f1`
#                end_date=`echo $TIME_PERIOD | cut -d' ' -f2`
#                cmd="${cmd} --start_date $start_date --end_date $end_date"
#        fi

	for var_name in ${var_list}; do
		echo "$var_name - $index"
		input_files="${indir}/${var_name}/v*/*.nc"
		first_file=`ls ${indir}/${var_name}/v*/*.nc | head -n 1`
		last_file=`ls ${indir}/${var_name}/v*/*.nc | tail -n 1`
		first_file=`basename ${first_file/.nc/}`
		last_file=`basename ${last_file/.nc/}`
	
		if [ "${TIME_PERIOD}" == "" ]; then
			tstart=`echo ${first_file##*_} | cut -d'-' -f1`
			tend=`echo ${last_file##*_} | cut -d'-' -f2`
			output_file=${outdir}/${index}_${label}_${icclim_slice_mode}_${tstart}-${tend}.nc
		else
			tmp=`echo ${TIME_PERIOD//-/}`
			output_file=${outdir}/${index}_${label}_${icclim_slice_mode}_${tmp/ /-}.nc
		fi

		cmd="${cmd} ${index} ${output_file} --regrid ${icclim_template} --slice_mode ${icclim_slice_mode} --verbose --input_files ${input_files} --variable ${var_name} --drop_time_bounds"
	done

        if [ "${TIME_PERIOD}" != "" ]; then
                start_date=`echo $TIME_PERIOD | cut -d' ' -f1`
                end_date=`echo $TIME_PERIOD | cut -d' ' -f2`
                cmd="${cmd} --start_date $start_date --end_date $end_date"
        fi

	rm ${output_file}

#	cmd="${index} ${output_file} ${cmd}"
	echo $cmd
	$cmd

	if [ $? -ne 0 ]; then
		echo "Fail $index with $var_name"
		touch fail.${label}.${index}
	else
		touch success.${label}.${index}
	fi
done
