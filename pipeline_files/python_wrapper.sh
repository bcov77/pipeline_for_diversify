#!/bin/bash


$1 "${@:2}"

a=$?

#ctrl C or scheduler
if (( $a == 130 )); then
    exit
fi

if [ ! -f $2 ]; then
    echo "-" > $2
fi


