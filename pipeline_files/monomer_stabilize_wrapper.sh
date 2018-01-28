#!/bin/bash

og_pwd=$(pwd)
cd $2




./command.sh > monomer.log 2>&1

a=$?
echo $a > signal.log

if (( $a == 0 )); then
    pdb=$(echo "*__0001.pdb")
    spr=$(grep 'score_per_res' $pdb | awk '{print $2}')
    echo $spr
    if ([ $(echo "$spr < -3.2" | bc) -ne 0 ]); then
        to_write=$(readlink -f $pdb)
        cd $og_pwd
        echo $to_write > $1
        exit
    else
        cd $og_pwd
        echo "-" > $1
        exit
    fi
fi

#ctrl C or scheduler
if (( $a == 130 )); then
    exit
fi

# these are all failures
cd $og_pwd
echo "-" > $1


