#!/bin/bash
#PBS -l walltime=04:00:00
#PBS -l ncpus=1
#PBS -l mem=7GB
#PBS -l wd
#PBS -m n
#PBS -P tp28
#PBS -q normalbw
#PBS -l storage=scratch/tp28+gdata/ia39+gdata/tp28+gdata/hh5+gdata/rq0+gdata/access+gdata/xp65+gdata/py18
#PBS -v YEAR,MONTH

module use ${python_module_path}
module load ${python_env}


# link input files 
workdir="$syclops_scratchpath/workdir_${YEAR}${MONTH}_${domain}_${gcm}_${scenario}_${realisation}_${institution}_${rcm2}/"
mkdir -p $workdir
cd $workdir

for var in $syclops_6hourly_vars;
  do
    filepath="${data_path/\{freq\}/6hr}"
    filepath="${path/\{var\}/${var_name}}"
    ln -s ${filepath}/*_${YEAR}${MONTH}* $var.nc
  done

varlist="sfcWind wsgsmax pr psl"


for var in $syclops_3hourly_vars;
  do
    filepath="${data_path/\{freq\}/3hr}"
    filepath="${filepath/\{var\}/${var_name}}"
    ln -s ${filepath}/*_${YEAR}${MONTH}* $var.nc
  done


for var in $syclops_hourly_vars;
  do
    filepath="${data_path/\{freq\}/1hr}"
    filepath="${filepath/\{var\}/${var_name}}"
    ln -s ${filepath}/*_${YEAR}${MONTH}* $var.nc
  done

# create input and output file lists for DetectNodes
find "$PWD/" -name "*.nc" > input.txt
tr -s '\r\n' ';' < input.txt | sed -e 's/,$/\n/' | sed ' s/.$//' > input_DN.txt
infiles=`tr -s '\r\n' ';' < input.txt | sed -e 's/,$/\n/'`
rm input.txt
echo "{$workdir}/TE_nodes_${YEAR}_${DM}_${SCENARIO}_${RCM}.txt" > output_DN.txt

mkdir TE_log

# run DetectNodes
$syclops_TE_path/bin/DetectNodes --in_data_list input_DN.txt --searchbymin psl --closedcontourcmd "psl,10,5.5,0" --mergedist 6.000001 --outputcmd "psl,min,0;psl,posclosedcontour,2.0,0;psl,posclosedcontour,5.5,0;sfcWind,max,2.0;_DIFF(_VECMAG(ua200,va200),_VECMAG(ua850,va850)),avg,10.0;_DIFF(zg300,zg500),negclosedcontour,6.5,1.0;_DIFF(zg500,zg700),negclosedcontour,3.5,1.0;_DIFF(zg700,zg925),negclosedcontour,3.5,1.0;zg500,posclosedcontour,3.5,1.0;_CURL{16,2.5}(ua500,va500),max,0;hus100,max,0.0;hus850,max,0.0;ta100,max,0.0;ta850,max,0.0;zg850,min,0;ua850,posminusnegwtarea,5.5;_VECMAG(ua200,va200),maxpoleward,1.0" --timefilter "6hr" --latname "lat" --lonname "lon" --regional --mergeequal --logdir "./TE_log"


# create input and output file lists for VariableProcessor
find "$PWD/" -name "*.nc" > input.txt
tr -s '\r\n' ';' < input.txt | sed -e 's/,$/\n/' | sed ' s/.$//' > input_VP.txt
infiles=`tr -s '\r\n' ';' < input.txt | sed -e 's/,$/\n/'`

rm input.txt
echo "${workdir}/vort_${YEAR}_${DM}_${SCENARIO}_${RCM}.nc" > output_VP.txt

# run VariableProcessor
$syclops_TE_path/bin/VariableProcessor --in_data_list input_VP.txt --out_data_list output_VP.txt --var "_COND(_LAT(),_CURL{8,3}(ua850,va850),_PROD(_CURL{8,3}(ua850,va850),-1)),ua925,va925" --varout "Cyclonic_Vorticity,U925,V925" --latname "lat" --lonname "lon" --logdir "./TE_log" --timefilter "6hr" --regional

# create output file list for DetectBlobs
echo "${workdir}/blob.dat" > sizeblob_out.txt

# run DetectBlobs
$syclops_TE_path/bin/DetectBlobs --in_data_list output_VP.txt --out_list sizeblob_out.txt --thresholdcmd "((Cyclonic_Vorticity,>=,2e-5,0) & (_VECMAG(U925,V925),>=,12.0,0)) | (Cyclonic_Vorticity,>=,4e-5,0)" --geofiltercmd "area,>=,1e4km2" --tagvar "blobid" --latname "lat" --lonname "lon" --timefilter "6hr" --regional --logdir ./TE_log

# remove vorticity once blobs have been detected
rm $workdir/vort_${YEAR}_${DM}_${SCENARIO}_${RCM}.nc
