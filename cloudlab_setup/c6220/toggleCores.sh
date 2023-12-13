#!/bin/bash
#export BEGIN_CORE=${BEGIN_CORE:="0"}
#export NITERS=${NITERS:="0"}

function enablecores
{
    for (( c=8; c<16; c++ ))
    do
	#echo "/sys/devices/system/cpu/cpu${c}/online"
	echo "Enable core ${c}" 
	echo 1 > /sys/devices/system/cpu/cpu${c}/online
	cat /sys/devices/system/cpu/cpu${c}/online
	sleep 1
    done
}

function disablecores
{
    for (( c=8; c<16; c++ ))
    do
	#echo "/sys/devices/system/cpu/cpu${c}/online"
	echo "Disable core ${c}"
	echo 0 > /sys/devices/system/cpu/cpu${c}/online
	cat /sys/devices/system/cpu/cpu${c}/online
	sleep 1
    done
}

"$@"
