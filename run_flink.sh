#! /bin/bash

currdate=`date +%m_%d_%Y_%H_%M_%S_$1`

export NITERS=${NITERS:='2'}
export BEGIN_ITER=${BEGIN_ITER:='0'}
export MDVFS=${MDVFS:="0x0c00 0x1d00"}
export ITRS=${ITRS:="50 100"}
export MRAPL=${MRAPL:-"135"}

RATE="$1"

function runFlinkPython {
    timeout 600 python3 -u run-flink.py "$@"
}
    echo "[INFO] Input: RATE_LIST ${RATE}"
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
			echo "[INFO] Deploy Flink"
			./start-flink.sh
		      	echo "[INFO] BEGIN: --itr ${itr} --rapl ${r} --dvfs ${dvfs} --nrepeat ${i}"
			runFlinkPython --itr ${itr} --rapl ${r} --dvfs ${dvfs} --nrepeat ${i} --rate $1
			sleep 1
			mv linux.mcd.* ${currdate}/
			mv ../dependencies/flink-simplified/build-target/log/* ${currdate}/
			rename flink-root flink-root-${itr}-${dvfs}-${r} ${currdate}/flink-root*
			mv flink-latency* ${currdate}/
			sleep 1
			echo "[INFO] FINISHED: --itr ${itr} --rapl ${r} --dvfs ${dvfs} --nrepeat ${i}"
			sleep 1
		done
	    done
	done
    done
    mv ${currdate} ../raw-data/
    echo "[INFO] Parsing data into csv file"
    touch ../datasets/current.csv
    python3 clean-sys-log.py ../raw-data/${currdate}
    if [ -f "../datasets/$RATE.csv" ]; then
	cat ../datasets/current.csv >> ../datasets/$RATE.csv
    else
	cp ../datasets/headers.csv ../datasets/$RATE.csv
	cat ../datasets/current.csv >> ../datasets/$RATE.csv
    fi
    rm -f ../datasets/current.csv
