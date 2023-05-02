#!/bin/bash

export victim=192.168.1.9
 
ssh  $victim 'mkdir data'

#ssh $victim 'sudo bpftrace -e 'BEGIN { printf("%u", *kaddr(\"tsc_khz\")); exit(); }' > ${datadir}/tsc.txt'
ssh $victim 'cat /sys/devices/system/cpu/cpu0/cpufreq/cpuinfo_max_freq > data/max_freq.txt'
ssh $victim 'cat /proc/cpuinfo > data/cpuinfo.txt'
ssh $victim 'ifconfig > data/ifconfig.txt'
ssh $victim 'cp /proc/cmdline data/cmdline.txt'
ssh $victim ' cp -r /sys/devices/system/cpu data/sys-devices-system-cpu 2> /dev/null'
#ssh $victim ' tar -czf $datadir/sys-devices-system-cpu.tgz $datadir/sys-devices-system-cpu'
ssh $victim 'rm -rf data/sys-devices-system-cpu'

scp -r $victim:data/ logs/clean/current_system/
