#!/bin/bash

POLL_USAGE=0
C1_USAGE=0
C1E_USAGE=0
C3_USAGE=0
C6_USAGE=0

POLL_TIME=0
C1_TIME=0
C1E_TIME=0
C3_TIME=0
C6_TIME=0

for (( c=0; c<$(nproc); c++ ))
do    
    POLL_USAGE=$((POLL_USAGE + $(cat /sys/devices/system/cpu/cpu${c}/cpuidle/state0/usage)))
    C1_USAGE=$((C1_USAGE + $(cat /sys/devices/system/cpu/cpu${c}/cpuidle/state1/usage)))
    C1E_USAGE=$((C1E_USAGE + $(cat /sys/devices/system/cpu/cpu${c}/cpuidle/state2/usage)))
    C3_USAGE=$((C3_USAGE + $(cat /sys/devices/system/cpu/cpu${c}/cpuidle/state3/usage)))
    C6_USAGE=$((C6_USAGE + $(cat /sys/devices/system/cpu/cpu${c}/cpuidle/state4/usage)))

    POLL_TIME=$((POLL_TIME + $(cat /sys/devices/system/cpu/cpu${c}/cpuidle/state0/time)))
    C1_TIME=$((C1_TIME + $(cat /sys/devices/system/cpu/cpu${c}/cpuidle/state1/time)))
    C1E_TIME=$((C1E_TIME + $(cat /sys/devices/system/cpu/cpu${c}/cpuidle/state2/time)))
    C3_TIME=$((C3_TIME + $(cat /sys/devices/system/cpu/cpu${c}/cpuidle/state3/time)))
    C6_TIME=$((C6_TIME + $(cat /sys/devices/system/cpu/cpu${c}/cpuidle/state4/time)))
done

echo $POLL_USAGE,$C1_USAGE,$C1E_USAGE,$C3_USAGE,$C6_USAGE,$POLL_TIME,$C1_TIME,$C1E_TIME,$C3_TIME,$C6_TIME
