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

set -e

ls /g/data

${python_env}
module load cdo

# link input files 
workdir="$syclops_scratchpath/workdir_${YEAR}${MONTH}_${domain}_${gcm}_${scenario}_${realisation}_${institution}_${rcm2}/"
rm -rf $workdir/*
mkdir -p $workdir
cd $workdir

echo $data_path

for var_name in $syclops_6hourly_vars;
  do
    filepath="${data_path/\{freq\}/6hr}"
    filepath="${filepath/\{var\}/${var_name}}"
    echo ln -s ${filepath}/*_${YEAR}${MONTH}* $var_name.nc
    ln -s ${filepath}/*_${YEAR}${MONTH}* $var_name.nc
  done



for var_name in $syclops_3hourly_vars;
  do
    filepath="${data_path/\{freq\}/3hr}"
    filepath="${filepath/\{var\}/${var_name}}"
    echo ln -s ${filepath}/*_${YEAR}${MONTH}* $var_name.nc
    ln -s ${filepath}/*_${YEAR}${MONTH}* $var_name.nc
  done


for var_name in $syclops_hourly_vars;
  do
    filepath="${data_path/\{freq\}/1hr}"
    filepath="${filepath/\{var\}/${var_name}}"
    echo ln -s ${filepath}/*_${YEAR}${MONTH}* $var_name.nc
    ln -s ${filepath}/*_${YEAR}${MONTH}* $var_name.nc
  done


if [[ $syclops_6hourly_vars == *"hus100"* ]]; then
   echo "6 hourly 100 hPa humidity is present"
elif [[ $syclops_3hourly_vars == *"hus100"* ]]; then
   echo "3 hourly 100 hPa humidity is present"
else
  echo "extracting hus100 and ta100 from the driving GCM"
  echo cdo -L chname,hus,hus100 -selyear,$YEAR -intntime,4 -remapbil,hus850.nc -sellevel,10000 -seldate,$((YEAR-1))-12-30T00:00:00,$((YEAR+1))-01-02T00:00:00 -cat "/g/data/r87/DRSv3/CMIP6/*/*/${gcm}/${scenario}/${realisation}/day/hus/*/*/*.nc" hus100.nc
  cdo -L chname,hus,hus100 -intntime,4 -remapbil,hus850.nc -sellevel,10000 -selyear,$YEAR -cat "/g/data/r87/DRSv3/CMIP6/*/*/${gcm}/${scenario}/${realisation}/day/hus/*/*/*.nc" hus100.nc
  echo cdo -L chname,ta,ta100  -selyear,$YEAR -intntime,4 -remapbil,hus850.nc -sellevel,10000  -seldate,$((YEAR-1))-12-30T00:00:00,$((YEAR+1))-01-02T00:00:00 -cat "/g/data/r87/DRSv3/CMIP6/*/*/${gcm}/${scenario}/${realisation}/day/ta/*/*/*.nc" ta100.nc
  cdo -L chname,ta,ta100   -intntime,4 -remapbil,hus850.nc -sellevel,10000 -selyear,$YEAR -cat "/g/data/r87/DRSv3/CMIP6/*/*/${gcm}/${scenario}/${realisation}/day/ta/*/*/*.nc" ta100.nc
fi





# create input and output file lists for DetectNodes
find "$PWD/" -name "*.nc" > input.txt
tr -s '\r\n' ';' < input.txt | sed -e 's/,$/\n/' | sed ' s/.$//' > input_DN.txt
infiles=`tr -s '\r\n' ';' < input.txt | sed -e 's/,$/\n/'`
rm input.txt
echo "{$workdir}/TE_nodes_${YEAR}_${DM}_${SCENARIO}_${RCM}.txt" > output_DN.txt

mkdir TE_log

opt=""
if [ -z "$syclops_minlat" ]; then
  echo "using full domain"
else
  echo "using domain subset"
  opt="$opt --minlat $syclops_minlat"
  opt="$opt --minlon $syclops_minlon"
  opt="$opt --maxlat $syclops_maxlat"
  opt="$opt --maxlon $syclops_maxlon"
fi

echo $opt

# run DetectNodes
echo $syclops_TE_path/bin/DetectNodes $opt --in_data_list input_DN.txt --searchbymin psl --closedcontourcmd "psl,10,5.5,0" --mergedist 6.000001 --outputcmd "psl,min,0;psl,posclosedcontour,2.0,0;psl,posclosedcontour,5.5,0;sfcWind,max,2.0;_DIFF(_VECMAG(ua200,va200),_VECMAG(ua850,va850)),avg,10.0;_DIFF(zg300,zg500),negclosedcontour,6.5,1.0;_DIFF(zg500,zg700),negclosedcontour,3.5,1.0;_DIFF(zg700,zg925),negclosedcontour,3.5,1.0;zg500,posclosedcontour,3.5,1.0;_CURL{16,2.5}(ua500,va500),max,0;hus100,max,0.0;hus850,max,0.0;ta100,max,0.0;ta850,max,0.0;zg850,min,0;ua850,posminusnegwtarea,5.5;_VECMAG(ua200,va200),maxpoleward,1.0" --timefilter "6hr" --latname "lat" --lonname "lon" --regional --mergeequal --logdir "./TE_log"
$syclops_TE_path/bin/DetectNodes $opt --in_data_list input_DN.txt --searchbymin psl --closedcontourcmd "psl,10,5.5,0" --mergedist 6.000001 --outputcmd "psl,min,0;psl,posclosedcontour,2.0,0;psl,posclosedcontour,5.5,0;sfcWind,max,2.0;_DIFF(_VECMAG(ua200,va200),_VECMAG(ua850,va850)),avg,10.0;_DIFF(zg300,zg500),negclosedcontour,6.5,1.0;_DIFF(zg500,zg700),negclosedcontour,3.5,1.0;_DIFF(zg700,zg925),negclosedcontour,3.5,1.0;zg500,posclosedcontour,3.5,1.0;_CURL{16,2.5}(ua500,va500),max,0;hus100,max,0.0;hus850,max,0.0;ta100,max,0.0;ta850,max,0.0;zg850,min,0;ua850,posminusnegwtarea,5.5;_VECMAG(ua200,va200),maxpoleward,1.0" --timefilter "6hr" --latname "lat" --lonname "lon" --regional --mergeequal --logdir "./TE_log"


if  [ -z "$syclops_minlat" ]; then
# create input and output file lists for VariableProcessor
   find "$PWD/" -name "*.nc" > input.txt
   tr -s '\r\n' ';' < input.txt | sed -e 's/,$/\n/' | sed ' s/.$//' > input_VP.txt
   infiles=`tr -s '\r\n' ';' < input.txt | sed -e 's/,$/\n/'`
   rm input.txt
 else
   for var_name in ua850 va850 ua925 va925;
      do
      echo cdo sellonlatbox,$syclops_minlon,$syclops_maxlon,$syclops_minlat,$syclops_maxlat ${var_name}.nc ${var_name}_subset.nc
      cdo sellonlatbox,$syclops_minlon,$syclops_maxlon,$syclops_minlat,$syclops_maxlat ${var_name}.nc ${var_name}_subset.nc
      done
   find "$PWD/" -name "*_subset.nc" > input.txt
   tr -s '\r\n' ';' < input.txt | sed -e 's/,$/\n/' | sed ' s/.$//' > input_VP.txt
   infiles=`tr -s '\r\n' ';' < input.txt | sed -e 's/,$/\n/'`
   rm input.txt
fi
   

echo "${workdir}/vort_${YEAR}_${gcm}_${scenario}_${rcm2}.nc" > output_VP.txt


# run VariableProcessor
$syclops_TE_path/bin/VariableProcessor --in_data_list input_VP.txt --out_data_list output_VP.txt --var "_COND(_LAT(),_CURL{8,3}(ua850,va850),_PROD(_CURL{8,3}(ua850,va850),-1)),ua925,va925" --varout "Cyclonic_Vorticity,U925,V925" --latname "lat" --lonname "lon" --logdir "./TE_log" --timefilter "6hr" --regional

# create output file list for DetectBlobs
echo "${workdir}/blob.dat" > sizeblob_out.txt

# run DetectBlobs
$syclops_TE_path/bin/DetectBlobs $opt --in_data_list output_VP.txt --out_list sizeblob_out.txt --thresholdcmd "((Cyclonic_Vorticity,>=,2e-5,0) & (_VECMAG(U925,V925),>=,12.0,0)) | (Cyclonic_Vorticity,>=,4e-5,0)" --geofiltercmd "area,>=,1e4km2" --tagvar "blobid" --latname "lat" --lonname "lon" --timefilter "6hr" --regional --logdir ./TE_log

# remove vorticity once blobs have been detected
rm $workdir/vort_${YEAR}_${gcm}_${scenario}_${rcm2}.nc
rm -f $workdir/*_subset.nc
