#!/bin/bash

cd $2

rif_dock="/home/bcov/rifdock/scheme/build/apps/rosetta/rif_dock_test"

if [ ! -f "$rif_dock" ]; then
    rif_dock="/suppscr/baker/bcov/rifdock/scheme/build/apps/rosetta/rif_dock_test"
fi

$rif_dock @rifdock.flag @morph.flag > phase2.log

a=$?
echo $a > signal.log

if (( $a == 0 )); then
    echo $(readlink -f .) > $1
    exit
fi

#ctrl C or scheduler
if (( $a == 130 )); then
    exit
fi

# these are all failures
echo "-" > $1
