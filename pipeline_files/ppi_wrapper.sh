#!/bin/bash

og_pwd=$(pwd)


base=$(basename $2)

mkdir ppi
mkdir ppi/$base
cp $2 ppi/$base
cd ppi/$base

$og_pwd/pipeline_files/mod_scripts/make_ala_comp.py $base

$og_pwd/rosetta -database $og_pwd/database -parser:protocol $og_pwd/pipeline_files/used_xmls/only_design_buns_ALA_NQST.xml -aa_composition_setup_file ala.comp -nstruct 1 -out:pdb_gz -out:prefix 4HQFmid1_ -s $base > ppi.log 2>&1


a=$?
echo $a > signal.log

#ctrl C or scheduler
if (( $a == 130 )); then
    exit
fi

# even a success ends up down here

# these are all failures
cd $og_pwd
echo "-" > $1


