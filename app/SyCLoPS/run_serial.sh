
module use ${python_module_path}
module load ${python_env}

set -e

workdir="$syclops_scratchpath/workdir_${domain}_${gcm}_${scenario}_${realisation}_${institution}_${rcm2}/"
mkdir -p $workdir
rm -rf $workdir/*
cd $workdir
#rm -r $workdir/*

filepath="${data_path/\{freq\}/fx}"
filepath="${filepath/\{var\}/orog}"

ln -s $filepath/*.nc orog.nc
ln -s $suitedir/app/SyCLoPS/* .
# create output lists from all processors for DETECTNODES and VARIABLEPROCESSOR
ls $syclops_scratchpath/workdir_*_${domain}_${gcm}_${scenario}_${realisation}_${institution}_${rcm2}/out.dat > output_DN.txt

# create output list for SIZEBLOB
sed -e "s/out/blob/g" < output_DN.txt  > sizeblob_out.txt

# run SyCLoPS (remaining TE commands + classifier)
python SyCLoPS_main.py

mkdir -p $outdir/$SyCLoPS_outdir_name
mv SyCLoPS_classified.csv $outdir/$SyCLoPS_outdir_name/SyCLoPS_classified_${domain}_${gcm}_${scenario}_${realisation}_${institution}_${rcm2}_${start_year}01-${end_year}12.csv
mv SyCLoPS_classified.parquet $outdir/$SyCLoPS_outdir_name/SyCLoPS_classified_${domain}_${gcm}_${scenario}_${realisation}_${institution}_${rcm2}_${start_year}01-${end_year}12.parquet


rm -r $syclops_scratchpath/workdir*_${domain}_${gcm}_${scenario}_${realisation}_${institution}_${rcm2}
