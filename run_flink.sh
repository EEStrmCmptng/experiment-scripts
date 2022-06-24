#! /bin/bash

currdate=`date +%m_%d_%Y_%H_%M_%S`

export NITERS=${NITERS:='0'}
export BEGIN_ITER=${BEGIN_ITER:='0'}
export MDVFS=${MDVFS:="0x1d00 0x1b00"}
export ITRS=${ITRS:="1 4"}
export MRAPL=${MRAPL:-"135"}

function runFlinkPython {
    timeout 600 python3 -u run-flink.py "$@"
}

function runFlink {
    echo "[INFO] Input: DVFS ${MDVFS}"
    echo "[INFO] Input: ITRS ${ITRS}"
    echo "[INFO] Input: MRAPL ${MRAPL}"
    echo "[INFO] Input: NITERS ${NITERS}"
    echo "[INFO] Input: mkdir ${currdate}"
    mkdir ${currdate}

    for itr in $ITRS; do
	for dvfs in ${MDVFS}; do
 	    for r in ${MRAPL}; do
		for i in `seq ${BEGIN_ITER} 1 $NITERS`; do
		      	echo "[INFO] BEGIN: --itr ${itr} --rapl ${r} --dvfs ${dvfs} --nrepeat ${i}"
			echo "[INFO] Remove all previous flink logs"
			rm -rf ../dependencies/flink/log/*
			runFlinkPython --itr ${itr} --rapl ${r} --dvfs ${dvfs} --nrepeat ${i}
			sleep 1
			mv linux.mcd.* ${currdate}/
			mv ../dependencies/flink/log/* ${currdate}/
			mv flink-latency-* ${currdate}/
			sleep 1
			echo "[INFO] FINISHED: --itr ${itr} --rapl ${r} --dvfs ${dvfs} --nrepeat ${i}"
			sleep 1
		done
	    done
	done
    done
    mv ${currdate} ../raw-data/
    echo "[INFO] Parsing data into csv file"
    python3 clean-sys-log.py ../raw-data/${currdate}
}

"$@"

