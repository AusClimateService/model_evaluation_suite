
module use ${python_module_path}
module load ${python_env}



workdir="$syclops_scratchpath/workdir_${domain}_${gcm}_${scenario}_${realisation}_${institution}_${rcm2}/"
mkdir -p $workdir
cd $workdir

filepath="${data_path/\{freq\}/fx}"
filepath="${filepath/\{var\}/${var_name}}"

ln -s $filepath orog.nc
ln -s $suitedir/app/SyCLoPS/* .
# create output lists from all processors for DETECTNODES and VARIABLEPROCESSOR
ls $syclops_scratchpath/workdir_*_${domain}_${gcm}_${scenario}_${realisation}_${institution}_${rcm2}/out.dat > output_DN.txt

# create output list for SIZEBLOB
sed -e "s/out/blob/g" < output_DN.txt  > sizeblob_out.txt

# run SyCLoPS (remaining TE commands + classifier)
python SyCLoPS_main.py

mkdir -p $outdir/SyCLoPS
mv SyCLoPS_classified.csv $outdir/SyCLoPS/SyCLoPS_classified_${domain}_${gcm}_${scenario}_${realisation}_${institution}_${rcm2}_${start_year}01-${end_year}12.csv
mv SyCLoPS_classified.parquet $outdir/SyCLoPS/SyCLoPS_classified_${domain}_${gcm}_${scenario}_${realisation}_${institution}_${rcm2}_${start_year}01-${end_year}12.parquet
