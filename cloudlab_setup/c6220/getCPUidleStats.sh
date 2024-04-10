#!/bin/bash

FILES="above below power time usage rejected"

for((c=0;c<$(nproc);c++))
do
    for((state=0;state<5;state++))
    do
	for file in $FILES; do
	    a=$(cat "/sys/devices/system/cpu/cpu${c}/cpuidle/state${state}/${file}")
	    echo -n "$a,"
	done
    done
done
echo ""
