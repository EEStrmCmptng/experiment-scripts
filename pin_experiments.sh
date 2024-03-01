#!/bin/bash

export CS=${CS:="C1 C2 C3 C4 C5"}
export FLINKC=${FLINKC:="query1_cores16_frate100000_6000000_fbuff-1_itr1_ondemanddvfs1_source16_mapper4_sink16_repeat0"}
EDIR="pin_experiments/$FLINKC"

set -x

function base {
    echo "🟢🟢 Gather base numbers 🟢🟢"
    ./pin.sh reset $EDIR/jstack.processed
    sleep 180
    
    rm -rf $EDIR/$FUNCNAME
    mkdir -p $EDIR/$FUNCNAME
    
    ./cloudlab_setup/c6220/getStats.sh > $EDIR/$FUNCNAME/statsSTART.csv
    cat /proc/stat > $EDIR/$FUNCNAME/procstatsSTART.csv
    
    sudo rm /tmp/rapl.log
    sudo systemctl restart rapl_log
    sleep 120
    sudo systemctl stop rapl_log
    
    ./cloudlab_setup/c6220/getStats.sh > $EDIR/$FUNCNAME/statsEND.csv
    cat /proc/stat > $EDIR/$FUNCNAME/procstatsEND.csv
    cp /tmp/rapl.log $EDIR/$FUNCNAME/
    ssh 10.10.1.1 "tail -n 1 /users/hand32/experiment-scripts/logs/${FLINKC}/Flinklogs/'Operator_Source: Bids Source_0'" > $EDIR/$FUNCNAME/Source.0
}

function doJstack
{
    echo "🟢🟢 Run jstack to get thread info  🟢🟢"
    sleep 180
    jstack $(pgrep -f java) > $EDIR/jstack.raw
    ./process_jstack.sh $EDIR/jstack.raw > $EDIR/jstack.processed
    sleep 5
}

function doC
{
    echo "🟢🟢 Run Config " $1 " 🟢🟢"
    ./pin.sh reset $EDIR/jstack.processed
    sleep 180
    
    ./pin.sh $1 $EDIR/jstack.processed
    sleep 180

    rm -rf $EDIR/$1
    mkdir -p $EDIR/$1
    
    ./cloudlab_setup/c6220/getStats.sh > $EDIR/$1/statsSTART.csv
    cat /proc/stat > $EDIR/$1/procstatsSTART.csv
    
    sudo rm /tmp/rapl.log
    sudo systemctl restart rapl_log
    sleep 120
    sudo systemctl stop rapl_log
    
    ./cloudlab_setup/c6220/getStats.sh > $EDIR/$1/statsEND.csv
    cat /proc/stat > $EDIR/$1/procstatsEND.csv
    cp /tmp/rapl.log $EDIR/$1/
    ssh 10.10.1.1 "tail -n 1 /users/hand32/experiment-scripts/logs/${FLINKC}/Flinklogs/'Operator_Source: Bids Source_0'" > $EDIR/$1/Source.0
}

function test1
{
    ssh 10.10.1.1 "tail -n 1 /users/hand32/experiment-scripts/logs/${FLINKC}/Flinklogs/'Operator_Source: Bids Source_0'"
}

function run
{
    echo "🟢🟢 START run 🟢🟢"
    mkdir -p $EDIR
    doJstack
    base
    
    for c in $CS; do
	doC $c
    done
}

"$@"

