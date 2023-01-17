currdate=`date +%m_%d_%Y_%H_%M_%S`

export NITERS=${NITERS:='2'}
export BEGIN_ITER=${BEGIN_ITER:='0'}
export MDVFS=${MDVFS:="0x0c00 0x1d00"}
export ITRS=${ITRS:="50 100"}
export MRAPL=${MRAPL:-"135"}
export FLINK_RATE=${FLINK_RATE:="1000_100000"}
export BUFF=${BUFF:="100000"}
export NCORES=${NCORES:="16"}
RATE="$1"
    
echo "[INFO] Input: RATE_LIST ${RATE}"
echo "[INFO] Input: DVFS ${MDVFS}"
echo "[INFO] Input: ITRS ${ITRS}"
echo "[INFO] Input: MRAPL ${MRAPL}"
echo "[INFO] Input: NITERS ${NITERS}"
echo "[INFO] Input: FLINK_RATE ${FLINK_RATE}"
echo "[INFO] Input: BUFF ${BUFF}"
echo "[INFO] Input: NCORES ${NCORES}"
echo "[INFO] Input: mkdir ${currdate}"
mkdir ${currdate}
for fr in $FLINK_RATE; do
    for buff in $BUFF; do
        for itr in $ITRS; do
	    for dvfs in ${MDVFS}; do
 	        for r in ${MRAPL}; do
	            for i in `seq ${BEGIN_ITER} 1 $NITERS`; do
       		        echo "[INFO] Run Experiment"
		      	echo "[INFO] BEGIN: --itr ${itr} --rapl ${r} --dvfs ${dvfs} --nrepeat ${i}"
			python3 runexperiment.py --flinkrate ${fr} --bufftimeout ${buff} --itr ${itr} --dvfs ${dvfs} --nrepeat ${NITERS}  --cores ${NCORES} --rapl ${RAPL}
			sleep 1
			echo "[INFO] FINISHED
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
		      python3 cleanup.py --flinkrate ${fr} --bufftimeout ${buff} --itr ${itr} --dvfs ${dvfs} --nrepeat ${NITERS}  --cores ${NCORES} --rapl ${RAPL}
		      sleep 1
		      echo "[INFO] FINISHED
		    done
		done
	    done
	done
    done
done

mv ./logs/clean/${FLINK_RATE}_${BUFF} ./logs/clean/${currdate}
