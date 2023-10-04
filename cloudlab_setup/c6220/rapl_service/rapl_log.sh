#! /bin/bash

for i in `seq 0 1 $1`; do
    ssh $TBENCH_SERVER "sudo ~/bayop/uarch-configure/rapl-read/raplog -m"
    #echo ''
done

