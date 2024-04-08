#!/bin/bash

export POLICIES=${POLICIES:="performance powersave conservative ondemand schedutil"}
export IPMAPPER=${IPMAPPER:="10.10.1.3"}

function switchStates {
    numCPUs=$(ssh $IPMAPPER nproc --all)
    echo "Num CPUs in Mapper: ${numCPUs}"
    for ((i = 0; i < 5; i++)); do # Iterate over each cstate in the system
	for ((j = 0; j < $numCPUs; j++)); do # Set the state for all cpus
	    ssh $IPMAPPER "echo $1 | sudo tee /sys/devices/system/cpu/cpu${j}/cpuidle/state${i}/disable"
        done
    done
}

echo $RESHEADERS > results.csv
for ((state = 0; state < 2; state++)); do # 2 iterations: 0 = cstates enabled, 1 = cstates disabled
    echo Running with State $state.
    switchStates $state
    for ((rate=100; rate <= 2000; rate+=100)); do #set flink rate to 100, 200, ..., 2000
        for policy in $POLICIES; do
            SLEEPDISABLE=$state MPOLICY=$policy MQUERY=imgproc MCFG="1;16;16" NSOURCES=1 NSINKS=16 NMAPPERS=16 FLINK_RATE="${rate}_300000" /users/gustinj/experiment-scripts/run_imgproc.sh
	done
    done
done

python parse_simplified.py --name imgproc --log ~/experiment-scripts/logs
cp ~/experiment-scripts/combined.csv ./results.csv

echo "ALL RUNS COMPLETE"

