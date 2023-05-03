#!/bin/bash
currdate=`date +%m_%d_%Y_%H_%M_%S`

export NITERS=${NITERS:='9'}
export BEGIN_ITER=${BEGIN_ITER:='0'}
export FLINK_RATE=${FLINK_RATE:="100000_300000"}
export BUFF=${BUFF:="-1"}
export NCORES=${NCORES:=16}

echo "[INFO] Input: RATE_LIST ${RATE}"
echo "[INFO] Input: Linux DYNAMIC"
echo "[INFO] Input: NITERS ${NITERS}"
echo "[INFO] Input: FLINK_RATE ${FLINK_RATE}"
echo "[INFO] Input: BUFF ${BUFF}"
echo "[INFO] Input: NCORES ${NCORES}"
echo "[INFO] Input: mkdir ${currdate}"
mkdir ./logs/clean/${currdate}
touch ./logs/clean/${currdate}/${FLINK_RATE}_${BUFF}.csv
for fr in $FLINK_RATE; do
    for buff in $BUFF; do
	for i in `seq ${BEGIN_ITER} 1 $NITERS`; do
       	    echo "[INFO] Run Experiment"
	    echo "[INFO] BEGIN: --itr 1 --rapl 135 --dvfs 0xffff --nrepeat ${i}"
	    python3 runexperiment.py --flinkrate ${fr} --bufftimeout ${buff} --itr "1" --dvfs "0xffff" --nrepeat ${i}  --cores ${NCORES} --rapl "135"
	    sleep 1
	    echo "[INFO] FINISHED"
	done
    done
done
