#!/bin/bash

# This script really shouldn't be used without some
# further tweaking in run_imgproc.sh and runexperiments_cloudlab.py
# to set directory names based upon cstates being enabled/disabled.

# This script also assumes the getStatsSimplified.sh script is in the same directory

export PERFSTATMETRICS=${PERFSTATMETRICS:="power/energy-cores/,power/energy-pkg/,power/energy-ram/"}
export RESHEADERS=${RESHEADERS:="STATE,RATE,POLICY,CORE_ENERGY,PKG_ENERGY,RAM_ENERGY,POLL_RES,C1_RES,C1E_RES,C3_RES,C6_RES"}
export POLICIES=${POLICIES:="powersave conservative ondemand schedutil performance"}
export IPMAPPER=${IPMAPPER:="10.10.1.3"}

function switchStates {
    for ((i = 0; i < 5; i++)); do # Iterate over each cstate in the system
	for ((j = 0; j < 32; j++)); do # Set the state for all cpus
	    ssh $IPMAPPER "echo $1 | sudo tee /sys/devices/system/cpu/cpu${j}/cpuidle/state${i}/disable"
        done
    done
}

echo $RESHEADERS > results.csv
for ((state = 0; state < 2; state++)); do # 2 iterations: 0 = cstates enabled, 1 = cstates disabled
    echo Running with State $state.
    echo -n $state, >> results.csv
    switchStates $state
    for ((rate=100; rate <= 2000; rate+=100)); do #set flink rate to 100, 200, ..., 2000
        echo -n $rate >> results.csv
        for policy in $POLICIES; do
	    echo -n $policy >> results.csv
            perf stat -a -x, -o buffer.csv -e $PERFSTATMETRICS "MQUERY=imgproc MCFG="1;16;16" NSOURCES=1 NSINKS=16 NMAPPERS=16 FLINK_RATE=$rate_300000 /users/gustinj/experiment-scripts/run_imgproc.sh"
            awk -F, '{print $1}' buffer.csv | tail -n +3 | awk '{printf "%s,", $0}' >> results.csv # Append power info
            echo $(./getStatsSimplified.sh) >> results.csv # Needs to be fixed. Appends residency info of current system, not mapper.
	done
    done
done
echo "ALL RUNS COMPLETE"
rm buffer.csv

