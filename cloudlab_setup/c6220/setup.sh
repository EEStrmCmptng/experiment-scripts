#!/bin/bash

sudo apt-get update
sudo apt-get install -y cpufrequtils msr-tools maven openjdk-11-jdk-headless python3-pip

# disable HT
echo off | sudo tee /sys/devices/system/cpu/smt/control

# disable TurboBoost
echo "1" | sudo tee /sys/devices/system/cpu/intel_pstate/no_turbo

# enable MSR to set DVFS statically
sudo modprobe msr
# lets run without sudo
sudo setcap cap_sys_rawio=ep /usr/sbin/rdmsr 
sudo setcap cap_sys_rawio=ep /usr/sbin/wrmsr

# flink related
pip install numpy pandas flink-rest-client

# disable irq rebalance
sudo killall irqbalance

# set irq affinity - make sure receive/transmit queues are mapped to the same core
ieth=$(ifconfig | grep -B1 10.10.1 | grep -o "^\w*")
sudo ./intel_set_irq_affinity.sh -x all ${ieth}

# this is causing firmware issues, disable for now
sudo rmmod mlx4_ib
