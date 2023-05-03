#!/bin/bash
currdate=`date +%m_%d_%Y_%H_%M_%S`

export NITERS=${NITERS:='9'}
export BEGIN_ITER=${BEGIN_ITER:='0'}
export MDVFS=${MDVFS:="0x0c00 0x1100 0x1d00"}
export ITRS=${ITRS:="10 300 600"}
export MRAPL=${MRAPL:-"135"}
export FLINK_RATE=${FLINK_RATE:="100000_300000"}
export BUFF=${BUFF:="-1"}
export NCORES=${NCORES:=16}
    
echo "[INFO] Input: RATE_LIST ${RATE}"
echo "[INFO] Input: DVFS ${MDVFS}"
echo "[INFO] Input: ITRS ${ITRS}"
echo "[INFO] Input: MRAPL ${MRAPL}"
echo "[INFO] Input: NITERS ${NITERS}"
echo "[INFO] Input: FLINK_RATE ${FLINK_RATE}"
echo "[INFO] Input: BUFF ${BUFF}"
echo "[INFO] Input: NCORES ${NCORES}"
echo "[INFO] Input: mkdir ${currdate}"
mkdir ./logs/clean/${currdate}
touch ./logs/clean/${currdate}/${FLINK_RATE}_${BUFF}.csv
for fr in $FLINK_RATE; do
    for buff in $BUFF; do
        for itr in $ITRS; do
	    for dvfs in ${MDVFS}; do
 	        for r in ${MRAPL}; do
	            for i in `seq ${BEGIN_ITER} 1 $NITERS`; do
       		        echo "[INFO] Run Experiment"
		      	echo "[INFO] BEGIN: --itr ${itr} --rapl ${r} --dvfs ${dvfs} --nrepeat ${i}"
			python3 runexperiment.py --flinkrate ${fr} --bufftimeout ${buff} --itr ${itr} --dvfs ${dvfs} --nrepeat ${i}  --cores ${NCORES} --rapl ${r}
			sleep 1
			echo "[INFO] FINISHED"
		    done
		done
	    done
	done
    done
done

for fr in $FLINK_RATE; do
   for buff in $BUFF; do
       for itr in $ITRS; do
	   for dvfs in ${MDVFS}; do
               for r in ${MRAPL}; do
	           for i in `seq ${BEGIN_ITER} 1 $NITERS`; do
		      echo "[INFO] Run Experiment"
		      echo "[INFO] BEGIN: --itr ${itr} --rapl ${r} --dvfs ${dvfs} --nrepeat ${i}"
		      python3 clean_flink.py cores${NCORES}_frate${fr}_fbuff${buff}_itr${itr}_dvfs${dvfs}_rapl${r}_repeat${i} $i >> logs/clean/${currdate}/${FLINK_RATE}_${BUFF}.csv
		      sleep 1
		      echo "[INFO] FINISHED"
		    done
		done
	    done
	done
    done
done
