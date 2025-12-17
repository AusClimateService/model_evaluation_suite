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
workdir="$TE_storms_scratchpath/workdir_${YEAR}${MONTH}_${domain}_${gcm}_${scenario}_${realisation}_${institution}_${rcm2}/"
mkdir -p $workdir
cd $workdir

echo $workdir


outputcmd=""

for var in $TE_storms_hourly_vars;
  do
    filepath="${data_path/\{freq\}/1hr}"
    filepath="${filepath/\{var\}/${var}}"
    ln -s ${filepath}/*_${YEAR}${MONTH}* . 
    outputcmd="$outputcmd$var,max,0.1;"
  done

outputcmd="${outputcmd}pr,avg,0.1"


echo $outputcmd

# create input and output file lists for DetectNodes
find "$PWD/" -name "*.nc" > input.txt
tr -s '\r\n' ';' < input.txt | sed -e 's/,$/\n/' | sed ' s/.$//' > input_DN.txt
infiles=`tr -s '\r\n' ';' < input.txt | sed -e 's/,$/\n/'`
rm input.txt
echo "{$workdir}/TE_nodes_${YEAR}_${DM}_${SCENARIO}_${RCM}.txt" > output_DN.txt

mkdir TE_log

# run DetectNodes
$TE_storms_TE_path/bin/DetectNodes --in_data_list input_DN.txt --searchbymax helicitymax --thresholdcmd "helicitymax,>=,75,0.1" --mergedist 0.400 --latname "lat" --lonname "lon" --regional --mergeequal  --outputcmd $outputcmd --logdir "./TE_log"

# create output file list for DetectBlobs
#echo "${workdir}/blob.dat" > sizeblob_out.txt

# run DetectBlobs
#$TE_storms_TE_path/bin/DetectBlobs --in_data_list input_DN.txt --out_list sizeblob_out.txt --thresholdcmd "helicitymax,>=,75,0.1" --tagvar "blobid" --latname "lat" --lonname "lon" --minlat -31 --maxlat -21 --minlon 145 --maxlon 157 --regional --logdir ./TE_log
