#!/bin/bash

currdate=`date +%m_%d_%Y_%H_%M_%S`
#set -x

export BEGIN_ITER=${BEGIN_ITER:="0"}
export NITERS=${NITERS:="0"}
#export MDVFS=${MDVFS:="0c00 0d00 0e00 0f00 1000 1100 1200 1300 1400 1500 1600 1700 1800 1900 1a00"}
export MDVFS=${MDVFS:="0c00 0e00 1000 1200 1400 1600 1800 1a00"}
#export MDVFS=${MDVFS:="1"}
#export ITRS=${ITRS:="1"}
#export ITRS=${ITRS:="2 100 150 200 250 300 350 400 450 500 550 600 650 700 750 800 850 900 950 1000"}
export ITRS=${ITRS:="2 100 200 300 400 500 600 700 800 900 1000"}
export FLINK_RATE=${FLINK_RATE:="200000_600000"} # 200K records-per-second for 10 minutes
export BUFF=${BUFF:="-1"}

export IPSINK=${IPSINK:="10.10.1.4"}
export IPMAPPER=${IPMAPPER:="10.10.1.3"}
export IPSOURCE=${IPSOURCE:="10.10.1.2"}
export MQUERY=${MQUERY:="query1"}
export MPOLICY=${MPOLICY:="ondemand"} # Other policies: conservative powersave performance schedutil"

# The assumption is we use 4 nodes that are identical in terms of hardware
# For now, we assume both the Source and Sink nodes use all available cores, i.e. why $(nproc) below 
export NCORES=${NCORES:=$(nproc)}
export MCFG=${MCFG:="$(nproc);4;$(nproc)"} # Sources; Mappers; Sinks

# This is to ensure number of task slots is never less than the amount of cores
# No work gets done by flink if taskmanager.numberOfTaskSlots <  max(Sources or Mappers or Sinks)
#sed -i "s/taskmanager.numberOfTaskSlots:.*/taskmanager.numberOfTaskSlots: $(nproc)/" flink-cfg/flink-conf.yaml
sed -i "s/taskmanager.numberOfTaskSlots:.*/taskmanager.numberOfTaskSlots: 64/" flink-cfg/flink-conf.yaml

echo "[INFO] START: ${currdate}"
echo "[INFO] Input: MPOLICY ${MPOLICY}"
echo "[INFO] Input: MQUERY ${MQUERY}"
echo "[INFO] Input: DVFS ${MDVFS}"
echo "[INFO] Input: ITRS ${ITRS}"
echo "[INFO] Input: NITERS ${NITERS}"
echo "[INFO] Input: FLINK_RATE ${FLINK_RATE}"
echo "[INFO] Input: BUFF ${BUFF}"
echo "[INFO] Input: NCORES ${NCORES}"
echo "[INFO] Input: IPMAPPER ${IPMAPPER}"
echo "[INFO] Input: MCFG ${MCFG}"
echo "[INFO] Input: NSOURCES ${NSOURCES}"
echo "[INFO] Input: NMAPPERS ${NMAPPERS}"
echo "[INFO] Input: NSINKS ${NSINKS}"

function dynamic {
    for cfg in $MCFG; do
	echo $cfg
	nsrc=$(echo $cfg | cut -d ";" -f 1)
	nmapper=$(echo $cfg | cut -d ";" -f 2)
	nsink=$(echo $cfg | cut -d ";" -f 3)

	rm flink-cfg/schedulercfg
	for t in `seq 1 1 $nsrc`; do
	    echo "Source; ${IPSOURCE}" >> flink-cfg/schedulercfg
	done
	for t in `seq 1 1 $nmapper`; do
	    echo "Mapper; ${IPMAPPER}" >> flink-cfg/schedulercfg
	done
	for t in `seq 1 1 $nsink`; do
	    echo "Sink; ${IPSINK}" >> flink-cfg/schedulercfg
	done		
	
	for i in `seq ${BEGIN_ITER} 1 $NITERS`; do
	    for fr in $FLINK_RATE; do
		for pol in $MPOLICY; do
		    echo "[INFO] python runexperiment_cloudlab.py --query ${MQUERY} --runcmd stopflink"
		    python runexperiment_cloudlab.py --query ${MQUERY} --runcmd stopflink

		    echo "[INFO] python runexperiment_cloudlab.py --query ${MQUERY} --runcmd startflink"
		    python runexperiment_cloudlab.py --query ${MQUERY} --runcmd startflink
			    
		    # Doing a warmup run first
		    python -u runexperiment_cloudlab.py --flinkrate "666_6666" --bufftimeout -1 --itr 1 --dvfs 1 --nrepeat 0 --cores ${NCORES} --query ${MQUERY} --policy "ondemand" --nsource ${nsrc} --nmapper ${nmapper} --nsink ${nsink}
		
		    echo "[INFO] Run Experiment"
		    echo "🟢 [INFO] python -u runexperiment_cloudlab.py --flinkrate ${fr} --bufftimeout -1 --itr 1 --dvfs 1 --nrepeat ${i} --cores ${NCORES} --query ${MQUERY} --policy ${pol} --nsource ${nsrc} --nmapper ${nmapper} --nsink ${nsink} 🟢"

		    cleanLogs			    
		    ssh ${IPMAPPER} sudo systemctl stop rapl_log
		    ssh ${IPMAPPER} sudo rm /tmp/rapl.log
		    ssh ${IPMAPPER} sudo systemctl restart rapl_log
		    sleep 1
		    python -u runexperiment_cloudlab.py --flinkrate ${fr} --bufftimeout -1 --itr 1 --dvfs 1 --nrepeat ${i} --cores ${NCORES} --query ${MQUERY} --policy ${pol} --nsource ${nsrc} --nmapper ${nmapper} --nsink ${nsink}
		    sleep 1			    
		    ssh ${IPMAPPER} sudo systemctl stop rapl_log
 		    loc="./logs/${MQUERY}_cores${NCORES}_frate${fr}_fbuff-1_itr1_${pol}dvfs1_source${nsrc}_mapper${nmapper}_sink${nsink}_repeat${i}"
 		    scp -r ${IPMAPPER}:/tmp/rapl.log ${loc}/rapl.log
		    scp -r $loc kd:/home/handong/sesadata/flink/query1_7_3_2024/
 		    echo "[INFO] FINISHED"
		done
	    done
	done    
    done
}

function static {
    for cfg in $MCFG; do
	echo $cfg
	nsrc=$(echo $cfg | cut -d ";" -f 1)
	nmapper=$(echo $cfg | cut -d ";" -f 2)
	nsink=$(echo $cfg | cut -d ";" -f 3)

	rm flink-cfg/schedulercfg
	for t in `seq 1 1 $nsrc`; do
	    echo "Source; ${IPSOURCE}" >> flink-cfg/schedulercfg
	done
	for t in `seq 1 1 $nmapper`; do
	    echo "Mapper; ${IPMAPPER}" >> flink-cfg/schedulercfg
	done
	for t in `seq 1 1 $nsink`; do
	    echo "Sink; ${IPSINK}" >> flink-cfg/schedulercfg
	done		
	
	for i in `seq ${BEGIN_ITER} 1 $NITERS`; do
	    for fr in $FLINK_RATE; do
		for itr in $ITRS; do
		    for dvfs in $MDVFS; do			
		    echo "[INFO] python runexperiment_cloudlab.py --query ${MQUERY} --runcmd stopflink"
		    python runexperiment_cloudlab.py --query ${MQUERY} --runcmd stopflink

		    echo "[INFO] python runexperiment_cloudlab.py --query ${MQUERY} --runcmd startflink"
		    python runexperiment_cloudlab.py --query ${MQUERY} --runcmd startflink
			    
		    # Doing a warmup run first
		    python -u runexperiment_cloudlab.py --flinkrate "666_6666" --bufftimeout -1 --itr 1 --dvfs 1 --nrepeat 0 --cores ${NCORES} --query ${MQUERY} --policy "ondemand" --nsource ${nsrc} --nmapper ${nmapper} --nsink ${nsink}
		
		    echo "[INFO] Run Experiment"
		    echo "🟢 [INFO] python -u runexperiment_cloudlab.py --flinkrate ${fr} --bufftimeout -1 --itr 1 --dvfs 1 --nrepeat ${i} --cores ${NCORES} --query ${MQUERY} --policy userspace --nsource ${nsrc} --nmapper ${nmapper} --nsink ${nsink} 🟢"

		    cleanLogs			    
		    ssh ${IPMAPPER} sudo systemctl stop rapl_log
		    ssh ${IPMAPPER} sudo rm /tmp/rapl.log
		    ssh ${IPMAPPER} sudo systemctl restart rapl_log
		    sleep 1
		    python -u runexperiment_cloudlab.py --flinkrate ${fr} --bufftimeout -1 --itr ${itr} --dvfs ${dvfs} --nrepeat ${i} --cores ${NCORES} --query ${MQUERY} --policy "userspace" --nsource ${nsrc} --nmapper ${nmapper} --nsink ${nsink}
		    sleep 1			    
		    ssh ${IPMAPPER} sudo systemctl stop rapl_log
 		    loc="./logs/${MQUERY}_cores${NCORES}_frate${fr}_fbuff-1_itr${itr}_userspacedvfs${dvfs}_source${nsrc}_mapper${nmapper}_sink${nsink}_repeat${i}"
 		    scp -r ${IPMAPPER}:/tmp/rapl.log ${loc}/rapl.log
		    scp -r $loc kd:/home/handong/sesadata/flink/query1_7_3_2024/
 		    echo "[INFO] FINISHED"
		    done
		done
	    done    
	done
    done
}

"$@"
