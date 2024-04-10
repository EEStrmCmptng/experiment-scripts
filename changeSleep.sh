export IPMAPPER=${IPMAPPER:="10.10.1.3"}

numCPUs=$(ssh $IPMAPPER nproc --all)
echo "Num CPUs in Mapper: ${numCPUs}"
for ((i = 0; i < 5; i++)); do # Iterate over each cstate in the system
    for ((j = 0; j < $numCPUs; j++)); do # Set the state for all cpus
        ssh $IPMAPPER "echo $1 | sudo tee /sys/devices/system/cpu/cpu${j}/cpuidle/state${i}/disable"
    done
done
