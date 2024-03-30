#!/bin/bash

export PERFSTATMETRICS=${PERFSTATMETRICS:="power/energy-cores/,power/energy-pkg/,power/energy-ram/"}
export RESHEADERS=${RESHEADERS:="STATE,CORE_ENERGY,PKG_ENERGY,RAM_ENERGY,POLL_RES,C1_RES,C1E_RES,C3_RES,C6_RES"}

echo $RESHEADERS > results.csv
for ((state = 0; state < 32; state++)); do # Iterate through all combinations of sleep states
    echo Running State \#$state.
    echo -n $state, >> results.csv
    for ((i = 0; i < 5; i++)); do # Iterate over each bit in binary values 0-31. One bit for each state
        bit=$(( ($state >> $i) & 1 )) # Get the bit for the current state
	for ((j = 0; j < 32; j++)); do # Set the state for all cpus
	    echo $bit | sudo tee /sys/devices/system/cpu/cpu$j/cpuidle/state$i/disable > /dev/null
        done
    done
    perf stat -a -x, -o buffer.csv -e $PERFSTATMETRICS sleep 30
    awk -F, '{print $1}' buffer.csv | tail -n +3 | awk '{printf "%s,", $0}' >> results.csv # Append power info
    echo $(./getStatsSimplified.sh) >> results.csv # Append residency info
done
echo "ALL RUNS COMPLETE"
rm buffer.csv
