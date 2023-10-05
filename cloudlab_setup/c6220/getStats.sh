#!/bin/bash

POLL=0
C1=0
C1E=0
C3=0
C6=0
RXP=0
RXB=0
TXP=0
TXB=0
ERXP=0
ERXB=0
ETXP=0
ETXB=0

for (( c=0; c<$(nproc); c++ ))
do    
    POLL=$((POLL + $(cat /sys/devices/system/cpu/cpu${c}/cpuidle/state0/usage)))
    C1=$((C1 + $(cat /sys/devices/system/cpu/cpu${c}/cpuidle/state1/usage)))
    C1E=$((C1E + $(cat /sys/devices/system/cpu/cpu${c}/cpuidle/state2/usage)))
    C3=$((C3 + $(cat /sys/devices/system/cpu/cpu${c}/cpuidle/state3/usage)))
    C6=$((C6 + $(cat /sys/devices/system/cpu/cpu${c}/cpuidle/state4/usage)))
done

tmp=$(ifconfig | grep -A5 10.10.1 | grep 'RX packets' | grep '\w*')
RXP=$(echo $tmp | cut -f3 -d' ')
RXB=$(echo $tmp | cut -f5 -d' ')

tmp=$(ifconfig | grep -A5 10.10.1 | grep 'TX packets' | grep '\w*')
TXP=$(echo $tmp | cut -f3 -d' ')
TXB=$(echo $tmp | cut -f5 -d' ')

tmp=$(ifconfig | grep -A5 128.110.96 | grep 'RX packets' | grep '\w*')
ERXP=$(echo $tmp | cut -f3 -d' ')
ERXB=$(echo $tmp | cut -f5 -d' ')

tmp=$(ifconfig | grep -A5 128.110.96 | grep 'TX packets' | grep '\w*')
ETXP=$(echo $tmp | cut -f3 -d' ')
ETXB=$(echo $tmp | cut -f5 -d' ')

echo $POLL, $C1, $C1E, $C3, $C6, $RXP, $RXB, $TXP, $TXB, $ERXP, $ERXB, $ETXP, $ETXB
