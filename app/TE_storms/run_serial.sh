infmt="lon,lat,"

for var in $TE_storms_hourly_vars;
  do
    infmt="$infmt${var}max,"
  done

infmt="${infmt}prmean"
echo $infmt

ls $TE_storms_scratchpath/workdir_*_${domain}_${gcm}_${scenario}_${realisation}_${institution}_${rcm2}/out.dat > output_DN.txt
mkdir -p $outdir

outfile=TempestExtremes_UHMaxima_${domain}_${gcm}_${scenario}_${realisation}_${institution}_${rcm2}_${start_year}01-${end_year}12.csv


mkdir -p $outdir/TE_storms
$TE_storms_TE_path/bin/StitchNodes --in_list output_DN.txt --out $outdir/TE_storms/$outfile --in_fmt $infmt --range 0.4 --mintime "1h" --maxgap "1h" --out_file_format "csv"


