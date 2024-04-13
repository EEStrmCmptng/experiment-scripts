#!/bin/bash

POLL=0
C1=0
C1E=0
C3=0
C6=0

for (( c=0; c<$(nproc); c++ ))
do    
    POLL=$((POLL + $(cat /sys/devices/system/cpu/cpu${c}/cpuidle/state0/usage)))
    C1=$((C1 + $(cat /sys/devices/system/cpu/cpu${c}/cpuidle/state1/usage)))
    C1E=$((C1E + $(cat /sys/devices/system/cpu/cpu${c}/cpuidle/state2/usage)))
    C3=$((C3 + $(cat /sys/devices/system/cpu/cpu${c}/cpuidle/state3/usage)))
    C6=$((C6 + $(cat /sys/devices/system/cpu/cpu${c}/cpuidle/state4/usage)))
done

echo $POLL,$C1,$C1E,$C3,$C6
