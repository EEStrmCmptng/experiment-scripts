#!/bin/bash

currdate=`date +%m_%d_%Y_%H_%M_%S`
#set -x

export BEGIN_ITER=${BEGIN_ITER:="0"}
export NITERS=${NITERS:="0"}
#export MDVFS=${MDVFS:="0c00 0d00 0e00 0f00 1000 1100 1200 1300 1400 1500 1600 1700 1800 1900 1a00"}
export MDVFS=${MDVFS:="1"}
export ITRS=${ITRS:="1"}
export FLINK_RATE=${FLINK_RATE:="200000_600000"}
export BUFF=${BUFF:="-1"}
export NCORES=${NCORES:=16}
export TBENCH_SERVER1=${TBENCH_SERVER1:-"10.10.1.1"}
export TBENCH_SERVER2=${TBENCH_SERVER2:-"10.10.1.2"}
export MQUERY=${MQUERY:="query1"}
export MPOLICY=${MPOLICY:="ondemand conservative powersave performance schedutil"}

echo "[INFO] START: ${currdate}"
echo "[INFO] Input: MPOLICY ${MPOLICY}"
echo "[INFO] Input: MQUERY ${MQUERY}"
echo "[INFO] Input: DVFS ${MDVFS}"
echo "[INFO] Input: ITRS ${ITRS}"
echo "[INFO] Input: NITERS ${NITERS}"
echo "[INFO] Input: FLINK_RATE ${FLINK_RATE}"
echo "[INFO] Input: BUFF ${BUFF}"
echo "[INFO] Input: NCORES ${NCORES}"
echo "[INFO] Input: TBENCH_SERVER1 ${TBENCH_SERVER1}"
echo "[INFO] Input: TBENCH_SERVER2 ${TBENCH_SERVER2}"

function dvfspolicy {
    for i in `seq ${BEGIN_ITER} 1 $NITERS`; do
	for fr in $FLINK_RATE; do
	    echo "[INFO] Run Experiment"
	    echo "[INFO] python3 -u flink_dvfs_policy1.py --flinkrate ${fr} --bufftimeout -1 --nrepeat ${i} --cores 16 --query query1"

	    ssh ${TBENCH_SERVER2} sudo systemctl stop rapl_log
	    ssh ${TBENCH_SERVER2} sudo rm /data/rapl_log.log
	    ssh ${TBENCH_SERVER2} sudo systemctl restart rapl_log

	    python3 -u flink_dvfs_policy1.py --flinkrate ${fr} --bufftimeout -1 --nrepeat ${i} --cores 16 --query query1

	    ssh ${TBENCH_SERVER2} sudo systemctl stop rapl_log
 	    loc="./logs/${MQUERY}_cores${NCORES}_frate${fr}_fbuff-1_dvfspolicy1_repeat${i}"
 	    scp -r ${TBENCH_SERVER2}:/data/rapl_log.log ${loc}/server2_rapl.log
	    
 	    echo "[INFO] FINISHED"
	done
    done
}

function performance {
    for i in `seq ${BEGIN_ITER} 1 $NITERS`; do
	for fr in $FLINK_RATE; do
	    for itr in $ITRS; do
		for pol in $MPOLICY; do
		    echo "[INFO] Run Experiment"
		    echo "[INFO] python3 runexperiment_cloudlab.py --flinkrate ${fr} --bufftimeout -1 --itr ${itr} --dvfs 1 --nrepeat ${i}  --cores ${NCORES} --query ${MQUERY} --policy ${pol}"
		    ssh ${TBENCH_SERVER2} sudo systemctl stop rapl_log
		    ssh ${TBENCH_SERVER2} sudo rm /data/rapl_log.log
		    ssh ${TBENCH_SERVER2} sudo systemctl restart rapl_log
		    
		    #ssh 10.10.1.1 ethtool -C enp5s0f0 rx-usecs ${itr}
		    
		    python3 -u runexperiment_cloudlab.py --flinkrate ${fr} --bufftimeout -1 --itr ${itr} --dvfs 1 --nrepeat ${i}  --cores ${NCORES} --query ${MQUERY} --policy ${pol}

		    ssh ${TBENCH_SERVER2} sudo systemctl stop rapl_log
 		    loc="./logs/${MQUERY}_cores${NCORES}_frate${fr}_fbuff-1_itr${itr}_${pol}dvfs1_repeat${i}"
 		    scp -r ${TBENCH_SERVER2}:/data/rapl_log.log ${loc}/server2_rapl.log
		    
 		    echo "[INFO] FINISHED"
		done
	    done
	done
    done
}

function dynamic {
    for i in `seq ${BEGIN_ITER} 1 $NITERS`; do
	for fr in $FLINK_RATE; do
	    for pol in $MPOLICY; do
		echo "[INFO] Run Experiment"
		echo "[INFO] python3 runexperiment_cloudlab.py --flinkrate ${fr} --bufftimeout -1 --itr 1 --dvfs 1 --nrepeat ${i}  --cores ${NCORES} --query ${MQUERY} --policy ${pol}"

		ssh ${TBENCH_SERVER2} sudo systemctl stop rapl_log
		ssh ${TBENCH_SERVER2} sudo rm /data/rapl_log.log
		ssh ${TBENCH_SERVER2} sudo systemctl restart rapl_log
		
		python3 -u runexperiment_cloudlab.py --flinkrate ${fr} --bufftimeout -1 --itr 1 --dvfs 1 --nrepeat ${i}  --cores ${NCORES} --query ${MQUERY} --policy ${pol}

		ssh ${TBENCH_SERVER2} sudo systemctl stop rapl_log
 		loc="./logs/${MQUERY}_cores${NCORES}_frate${fr}_fbuff-1_itr1_${pol}dvfs1_repeat${i}"
 		scp -r ${TBENCH_SERVER2}:/data/rapl_log.log ${loc}/server2_rapl.log
		
 		echo "[INFO] FINISHED"
	    done
	done
    done
}

function static {
    for i in `seq ${BEGIN_ITER} 1 $NITERS`; do
	for fr in $FLINK_RATE; do
	    for itr in $ITRS; do
		for dvfs in ${MDVFS}; do			
       		    echo "[INFO] Run Experiment"
		    echo "[INFO] python3 runexperiment_cloudlab.py --flinkrate ${fr} --bufftimeout -1 --itr ${itr} --dvfs ${dvfs} --nrepeat ${i}  --cores ${NCORES} --query ${MQUERY}"

		    ssh ${TBENCH_SERVER2} sudo systemctl stop rapl_log
		    ssh ${TBENCH_SERVER2} sudo rm /data/rapl_log.log
		    ssh ${TBENCH_SERVER2} sudo systemctl restart rapl_log
		    
		    python3 -u runexperiment_cloudlab.py --flinkrate ${fr} --bufftimeout -1 --itr ${itr} --dvfs ${dvfs} --nrepeat ${i}  --cores ${NCORES} --query ${MQUERY} --policy userspace
		    sleep 1

		    ## stop power logging
		    ssh ${TBENCH_SERVER2} sudo systemctl stop rapl_log

		    loc="./logs/${MQUERY}_cores${NCORES}_frate${fr}_fbuff-1_itr${itr}_userspacedvfs${dvfs}_repeat${i}"
		    scp -r ${TBENCH_SERVER2}:/data/rapl_log.log ${loc}/server2_rapl.log
		    
		    echo "[INFO] FINISHED"
		done
	    done
	done
    done
}

echo "[INFO] END: ${currdate}"

"$@"
