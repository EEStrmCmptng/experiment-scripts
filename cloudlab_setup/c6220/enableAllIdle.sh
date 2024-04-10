#!/bin/bash

for((c=0;c<$(nproc);c++))
do    
    for((state=0;state<5;state++))
    do
	echo "0" | sudo tee /sys/devices/system/cpu/cpu$c/cpuidle/state$state/disable > /dev/null
    done
done
