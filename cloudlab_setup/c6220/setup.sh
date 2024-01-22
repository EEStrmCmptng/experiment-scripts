#!/bin/bash

set -x

APTCLONEDIR=~/cloudlab_c6220_JobManager_Ubuntu22_5.15.0-69-generic_10_18_2023.apt-clone.tar.apt-clone.tar.gz

sudo apt-get update
sudo apt-get install apt-clone

# reloading system libraries needed
sudo apt-clone restore $APTCLONEDIR

# disable HyperThreads
echo off | sudo tee /sys/devices/system/cpu/smt/control

# disable TurboBoost
echo "1" | sudo tee /sys/devices/system/cpu/intel_pstate/no_turbo

# enable MSR to set DVFS statically
sudo modprobe msr
# lets run without sudo
sudo setcap cap_sys_rawio=ep /usr/sbin/rdmsr 
sudo setcap cap_sys_rawio=ep /usr/sbin/wrmsr
sudo setcap cap_net_admin+ep /usr/sbin/ethtool

# flink related python libraries
pip install -r requirements.txt

# disable irq rebalance
sudo killall irqbalance

# set irq affinity - make sure receive/transmit queues are mapped to the same core
ieth=$(ifconfig | grep -B1 10.10.1 | grep -o "^\w*")
sudo ~/experiment-scripts/cloudlab_setup/c6220/intel_set_irq_affinity.sh -x all ${ieth}

# sets hostname depending on IP
case $ieth in

    "10.10.1.1")
	sudo hostname JobManager10-1
	;;

    "10.10.1.2")
	sudo hostname Source10-2
	;;

    "10.10.1.3")
	sudo hostname Mapper10-3
	;;

    "10.10.1.4")
	sudo hostname Sink10-4
	;;

    *)
	echo -n "Unknown IP: ${ieth}"
	;;
esac

# this is causing firmware issues on c6220 nodes, disable for now
sudo rmmod mlx4_ib
sudo rmmod mlx4_core

# create /data for raplog service to run
sudo mkdir /data
cd ~/experiment-scripts/cloudlab_setup/c6220/uarch-configure/rapl-read/ && make raplog && sudo setcap cap_sys_rawio=ep raplog
cd /etc/systemd/system && sudo ln -s ~/experiment-scripts/cloudlab_setup/c6220/rapl_service/rapl_log.service rapl_log.service

# creates msr group and lets user rdmsr, wrmsr without sudo
sudo groupadd msr
sudo chgrp msr /dev/cpu/*/msr
sudo ls -l /dev/cpu/*/msr
sudo chmod g+rw /dev/cpu/*/msr
sudo usermod -aG msr $(whoami)

echo "**** NOTE: Re-login to this node for msr group changes to take effect ****"
sudo newgrp msr



