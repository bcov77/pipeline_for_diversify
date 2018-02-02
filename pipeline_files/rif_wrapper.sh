#!/bin/bash

og_pwd=$(pwd)
cd $2

rif_dock=$(readlink -f rif_dock_test)

$rif_dock @rifdock.flag @morph.flag > phase2.log 2>&1

a=$?
echo $a > signal.log

if (( $a == 0 )); then
    to_write=$(readlink -f .)
    cd $og_pwd
    echo $to_write > $1
    exit
fi

#ctrl C or scheduler
if (( $a == 130 )); then
    exit
fi

# these are all failures
cd $og_pwd
echo $pwd
echo "-" > $1
