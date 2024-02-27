#!/bin/bash

set -x
TIME=60
mkdir results

# enable HyperThreads
echo on | sudo tee /sys/devices/system/cpu/smt/control

# enable TurboBoost
echo "0" | sudo tee /sys/devices/system/cpu/intel_pstate/no_turbo

sleep 60

for ((iter=0; iter<3; iter+=1 )); do
    for (( i=1; i<=$(nproc); i+=1 )); do
	sudo rm /tmp/rapl.log
	sudo systemctl restart rapl_log
	
	stress-ng --vm $i --vm-bytes 1500M --mmap $i --mmap-bytes 1500M --page-in -t ${TIME}s
	
	sudo systemctl stop rapl_log
	cp /tmp/rapl.log "results/stress-ng.iter${iter}.numcpus${i}.TurboOn.HyperThreadOn.vm.60"
    done
done

sleep 60
# disable HyperThreads
echo off | sudo tee /sys/devices/system/cpu/smt/control

# disable TurboBoost
echo "1" | sudo tee /sys/devices/system/cpu/intel_pstate/no_turbo
sleep 60

for ((iter=0; iter<3; iter+=1 )); do
    for (( i=1; i<=$(nproc); i+=1 )); do
	sudo rm /tmp/rapl.log
	sudo systemctl restart rapl_log
	
	stress-ng --vm $i --vm-bytes 1500M --mmap $i --mmap-bytes 1500M --page-in -t ${TIME}s
	
	sudo systemctl stop rapl_log
	cp /tmp/rapl.log "results/stress-ng.iter${iter}.numcpus${i}.TurboOff.HyperThreadOff.vm.60"
    done
done
