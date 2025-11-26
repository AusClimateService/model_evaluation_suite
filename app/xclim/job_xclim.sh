#!/bin/bash

# Script definition
xclim_path=$suitedir/app/xclim
script="/g/data/xv83/users/bxn599/miniconda3/envs/icclim7.0.0/bin/python ${xclim_path}/run_xclim.py"
indir="${data_path/\{freq\}/day}"
indir="${indir/\{var\}/${var_name}}"
label="${domain}_${gcm}_${scenario}_${realisation}_${institution}_${rcm2}_v1-r1"
TIME_PERIOD="${start_year}-01-01 ${end_year}-12-31"

echo $index_list
for var_index in $index_list; do
	index=`echo $var_index | cut -d':' -f2`
	var_list=`echo $var_index | cut -d':' -f1`
	threshold=$(echo "$var_index" | cut -d':' -f3-)
	echo $threshold
	var_list=${var_list/&/ }
	echo $var_list
	outdir=$outdir/xclim/${index}
        mkdir -p ${outdir} || true

        cmd="${script}"

	for var_name in ${var_list}; do
		echo "$var_name - $index - $threshold"
		input_files="${indir}/*.nc"
		first_file=`ls ${indir}/${var_name}/v*/*.nc | head -n 1`
		last_file=`ls ${indir}/${var_name}/v*/*.nc | tail -n 1`
		first_file=`basename ${first_file/.nc/}`
		last_file=`basename ${last_file/.nc/}`
	
		if [ "${TIME_PERIOD}" == "" ]; then
			tstart=`echo ${first_file##*_} | cut -d'-' -f1`
			tend=`echo ${last_file##*_} | cut -d'-' -f2`
			output_file=${outdir}/${index}_${label}_${xclim_freq}_${tstart}-${tend}.nc
		else
			tmp=`echo ${TIME_PERIOD//-/}`
			output_file=${outdir}/${index}_${label}_${xclim_freq}_${tmp/ /-}.nc
		fi

	        if [ "$xclim_freq" == "year" ]; then
	                freq=YS
		fi
	        if [ "$xclim_freq" == "month" ]; then
	                freq=MS
	        fi
	        if [ "$xclim_freq" == "DJF" ]; then
	                freq=QS-DEC
	        fi
	        if [ "$xclim_freq" == "MAM" ]; then
	                freq=QS-DEC
	        fi
	        if [ "$xclim_freq" == "JJA" ]; then
	                freq=QS-DEC
	        fi
	        if [ "$xclim_freq" == "SON" ]; then
	        	freq=QS-DEC
	        fi

#		cmd="${cmd} ${index} ${output_file} --regrid ${xclim_template} --freq ${xclim_freq} --verbose --input_files ${input_files} --variable ${var_name}"
		if [ -n "$threshold" ]; then
		    cmd="${cmd} ${index} ${output_file} --regrid ${xclim_template} --freq ${freq} --verbose --input_files ${input_files} --variable ${var_name} --thresh $threshold"
		else
		    cmd="${cmd} ${index} ${output_file} --regrid ${xclim_template} --freq ${freq} --verbose --input_files ${input_files} --variable ${var_name}"
		fi

	done

        if [ "${TIME_PERIOD}" != "" ]; then
                start_date=`echo $TIME_PERIOD | cut -d' ' -f1`
                end_date=`echo $TIME_PERIOD | cut -d' ' -f2`
                cmd="${cmd} --start_date $start_date --end_date $end_date"
        fi

	rm ${output_file}

	echo $cmd
	$cmd

	if [ $? -ne 0 ]; then
		echo "Fail $index with $var_name"
		touch fail.${label}.${index}
	else
		touch success.${label}.${index}
	fi
done
