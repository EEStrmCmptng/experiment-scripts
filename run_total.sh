#!/bin/bash
currdate=`date +%m_%d_%Y_%H_%M_%S`

export NITERS=${NITERS:='2'}
export BEGIN_ITER=${BEGIN_ITER:='0'}
export MDVFS=${MDVFS:="0x0c00 0x0e00 0x1000 0x1200 0x1400 0x1600 0x1800 0x1a00 0x1c00"}
export ITRS=${ITRS:="2 4 8 16 20 30 50 100 150 200 250 300 350 400"}
export MRAPL=${MRAPL:-"135"}
export FLINK_RATE=${FLINK_RATE:="1000_100000"}
export BUFF=${BUFF:="100000"}
export NCORES=16
    
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
			python3 runexperiment.py --flinkrate ${fr} --bufftimeout ${buff} --itr ${itr} --dvfs ${dvfs} --nrepeat ${NITERS}  --cores ${NCORES} --rapl ${r}
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
		      python3 cleanup.py --flinkrate ${fr} --bufftimeout ${buff} --itr ${itr} --dvfs ${dvfs} --nrepeat ${NITERS}  --cores ${NCORES} --rapl ${r} >> logs/clean/${currdate}/${FLINK_RATE}_${BUFF}.csv
		      sleep 1
		      echo "[INFO] FINISHED"
		    done
		done
	    done
	done
    done
done
