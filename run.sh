#!/bin/bash

set -x

#NITERS="1" FLINK_RATE="300000_600000" MPOLICY="conservative ondemand powersave performance schedutil" ./run_query1.sh dynamic >> query1.out
#sleep 60
NITERS="3" FLINK_RATE="100000_600000 200000_600000 300000_600000 400000_600000" ITRS="2 50 100 200 400 600 800" MDVFS="0c00 0d00 0e00 0f00 1000 1100 1200 1300 1400 1500 1600 1700 1800 1900 1a00" ./run_query1.sh static >> query1.out
