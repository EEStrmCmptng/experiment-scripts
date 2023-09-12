#!/bin/bash

currdate=`date +%m_%d_%Y_%H_%M_%S`
#set -x

export BEGIN_ITER=${BEGIN_ITER:="0"}
export NITERS=${NITERS:="0"}
#export MDVFS=${MDVFS:="0c00 0d00 0e00 0f00 1000 1100 1200 1300 1400 1500 1600 1700 1800 1900 1a00"}
export MDVFS=${MDVFS:="1"}
export ITRS=${ITRS:="1"}
export MRAPL=${MRAPL:="1"}
export FLINK_RATE=${FLINK_RATE:="200000_600000"}
export BUFF=${BUFF:="-1"}
export NCORES=${NCORES:=16}
export TBENCH_SERVER1=${TBENCH_SERVER1:-"10.10.1.1"}
export TBENCH_SERVER2=${TBENCH_SERVER2:-"10.10.1.2"}

echo "[INFO] Input: DVFS ${MDVFS}"
echo "[INFO] Input: ITRS ${ITRS}"
echo "[INFO] Input: MRAPL ${MRAPL}"
echo "[INFO] Input: NITERS ${NITERS}"
echo "[INFO] Input: FLINK_RATE ${FLINK_RATE}"
echo "[INFO] Input: BUFF ${BUFF}"
echo "[INFO] Input: NCORES ${NCORES}"
echo "[INFO] Input: TBENCH_SERVER1 ${TBENCH_SERVER1}"
echo "[INFO] Input: TBENCH_SERVER2 ${TBENCH_SERVER2}"

for fr in $FLINK_RATE; do
    for buff in $BUFF; do
        for itr in $ITRS; do
	    for dvfs in ${MDVFS}; do
 	        for r in ${MRAPL}; do
	            for i in `seq ${BEGIN_ITER} 1 $NITERS`; do
       		        echo "[INFO] Run Experiment"
		      	echo "[INFO] BEGIN: --itr ${itr} --rapl ${r} --dvfs ${dvfs} --nrepeat ${i}"
			echo "[INFO] python3 runexperiment_cloudlab.py --flinkrate ${fr} --bufftimeout ${buff} --itr ${itr} --dvfs ${dvfs} --nrepeat ${i}  --cores ${NCORES} --rapl ${r}"			
			#ssh ${TBENCH_SERVER1} sudo systemctl stop rapl_log
			ssh ${TBENCH_SERVER2} sudo systemctl stop rapl_log
			
			#ssh ${TBENCH_SERVER1} sudo rm /data/rapl_log.log
			ssh ${TBENCH_SERVER2} sudo rm /data/rapl_log.log
			
			#ssh ${TBENCH_SERVER1} sudo systemctl restart rapl_log
			ssh ${TBENCH_SERVER2} sudo systemctl restart rapl_log
	
			python3 -u runexperiment_cloudlab.py --flinkrate ${fr} --bufftimeout ${buff} --itr ${itr} --dvfs ${dvfs} --nrepeat ${i}  --cores ${NCORES} --rapl ${r}
			sleep 1

			## stop power logging
			#ssh ${TBENCH_SERVER1} sudo systemctl stop rapl_log
			ssh ${TBENCH_SERVER2} sudo systemctl stop rapl_log

			loc="./logs/cores${NCORES}_frate${fr}_fbuff${buff}_itr${itr}_dvfs${dvfs}_rapl${r}_repeat${i}"
			#scp -r ${TBENCH_SERVER1}:/data/rapl_log.log ${loc}/server1_rapl.log
			scp -r ${TBENCH_SERVER2}:/data/rapl_log.log ${loc}/server2_rapl.log
			
			echo "[INFO] FINISHED"
		    done
		done
	    done
	done
    done
done
