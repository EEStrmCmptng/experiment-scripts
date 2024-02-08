#!/bin/bash

currdate=`date +%m_%d_%Y_%H_%M_%S`
#set -x

export BEGIN_ITER=${BEGIN_ITER:="0"}
export NITERS=${NITERS:="0"}
#export MDVFS=${MDVFS:="0c00 0d00 0e00 0f00 1000 1100 1200 1300 1400 1500 1600 1700 1800 1900 1a00"}
export MDVFS=${MDVFS:="1"}
export ITRS=${ITRS:="1"}
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
sed -i "s/taskmanager.numberOfTaskSlots:.*/taskmanager.numberOfTaskSlots: $(nproc)/" flink-cfg/flink-conf.yaml

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

function dvfspolicy {
    for i in `seq ${BEGIN_ITER} 1 $NITERS`; do
	for fr in $FLINK_RATE; do
	    echo "[INFO] Run Experiment"
	    echo "[INFO] python3 -u flink_dvfs_policy1.py --flinkrate ${fr} --bufftimeout -1 --nrepeat ${i} --cores 16 --query query1"

	    ssh ${IPMAPPER} sudo systemctl stop rapl_log
	    ssh ${IPMAPPER} sudo rm /data/rapl_log.log
	    ssh ${IPMAPPER} sudo systemctl restart rapl_log

	    python3 -u flink_dvfs_policy1.py --flinkrate ${fr} --bufftimeout -1 --nrepeat ${i} --cores 16 --query query1

	    ssh ${IPMAPPER} sudo systemctl stop rapl_log
 	    loc="./logs/${MQUERY}_cores${NCORES}_frate${fr}_fbuff-1_dvfspolicy1_repeat${i}"
 	    scp -r ${IPMAPPER}:/data/rapl_log.log ${loc}/server2_rapl.log
	    
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
		    ssh ${IPMAPPER} sudo systemctl stop rapl_log
		    ssh ${IPMAPPER} sudo rm /data/rapl_log.log
		    ssh ${IPMAPPER} sudo systemctl restart rapl_log
		    
		    #ssh 10.10.1.1 ethtool -C enp5s0f0 rx-usecs ${itr}
		    
		    python3 -u runexperiment_cloudlab.py --flinkrate ${fr} --bufftimeout -1 --itr ${itr} --dvfs 1 --nrepeat ${i}  --cores ${NCORES} --query ${MQUERY} --policy ${pol}

		    ssh ${IPMAPPER} sudo systemctl stop rapl_log
 		    loc="./logs/${MQUERY}_cores${NCORES}_frate${fr}_fbuff-1_itr${itr}_${pol}dvfs1_repeat${i}"
 		    scp -r ${IPMAPPER}:/data/rapl_log.log ${loc}/server2_rapl.log
		    
 		    echo "[INFO] FINISHED"
		done
	    done
	done
    done
}

function cleanLogs {
    rm -rf /users/hand32/experiment-scripts/flink-simplified/flink-dist/target/flink-1.14.0-bin/flink-1.14.0/log/*.log*
    ssh ${IPSOURCE} rm -rf /users/hand32/experiment-scripts/flink-simplified/flink-dist/target/flink-1.14.0-bin/flink-1.14.0/log/*.log*
    ssh ${IPMAPPER} rm -rf /users/hand32/experiment-scripts/flink-simplified/flink-dist/target/flink-1.14.0-bin/flink-1.14.0/log/*.log*
    ssh ${IPSINK} rm -rf /users/hand32/experiment-scripts/flink-simplified/flink-dist/target/flink-1.14.0-bin/flink-1.14.0/log/*.log*
}

function dynamic {        
    for cfg in $MCFG; do
	echo $cfg
	nsrc=$(echo $cfg | cut -d ";" -f 1)
	nmapper=$(echo $cfg | cut -d ";" -f 2)
	nsink=$(echo $cfg | cut -d ";" -f 3)
	
	echo "[INFO] python runexperiment_cloudlab.py --query ${MQUERY} --runcmd stopflink"
	python runexperiment_cloudlab.py --query ${MQUERY} --runcmd stopflink
	
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

	echo "[INFO] python runexperiment_cloudlab.py --query ${MQUERY} --runcmd startflink"
	python runexperiment_cloudlab.py --query ${MQUERY} --runcmd startflink
	
	for i in `seq ${BEGIN_ITER} 1 $NITERS`; do
	    for fr in $FLINK_RATE; do
		for pol in $MPOLICY; do
		    echo "[INFO] Run Experiment"
		    echo "[INFO] python -u runexperiment_cloudlab.py --flinkrate ${fr} --bufftimeout -1 --itr 1 --dvfs 1 --nrepeat ${i} --cores ${NCORES} --query ${MQUERY} --policy ${pol} --nsource ${nsrc} --nmapper ${nmapper} --nsink ${nsink}"

		    cleanLogs
		    
		    #ssh ${IPMAPPER} sudo systemctl stop rapl_log
		    #ssh ${IPMAPPER} sudo rm /data/rapl_log.log
		    #ssh ${IPMAPPER} sudo systemctl restart rapl_log
		    
		    python -u runexperiment_cloudlab.py --flinkrate ${fr} --bufftimeout -1 --itr 1 --dvfs 1 --nrepeat ${i} --cores ${NCORES} --query ${MQUERY} --policy ${pol} --nsource ${nsrc} --nmapper ${nmapper} --nsink ${nsink}
		    
		    #ssh ${IPMAPPER} sudo systemctl stop rapl_log
 		    #loc="./logs/${MQUERY}_cores${NCORES}_frate${fr}_fbuff-1_itr1_${pol}dvfs1_source${nsrc}_mapper${nmapper}_sink${nsink}_repeat${i}"
 		    #scp -r ${IPMAPPER}:/data/rapl_log.log ${loc}/server2_rapl.log
		    
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

	echo "[INFO] python runexperiment_cloudlab.py --query query1 --runcmd stopflink"
	python runexperiment_cloudlab.py --query query1 --runcmd stopflink
	
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

	echo "[INFO] python runexperiment_cloudlab.py --query query1 --runcmd startflink"
	python runexperiment_cloudlab.py --query query1 --runcmd startflink

	for i in `seq ${BEGIN_ITER} 1 $NITERS`; do
	    for fr in $FLINK_RATE; do
		for itr in $ITRS; do
		    for dvfs in ${MDVFS}; do			
       			echo "[INFO] Run Experiment"
			echo "[INFO] python runexperiment_cloudlab.py --flinkrate ${fr} --bufftimeout -1 --itr ${itr} --dvfs ${dvfs} --nrepeat ${i}  --cores ${NCORES} --query ${MQUERY} --nsource ${nsrc} --nmapper ${nmapper} --nsink ${nsink}"
			
			#ssh ${IPMAPPER} sudo systemctl stop rapl_log
			#ssh ${IPMAPPER} sudo rm /data/rapl_log.log
			#ssh ${IPMAPPER} sudo systemctl restart rapl_log
		    
			python3 -u runexperiment_cloudlab.py --flinkrate ${fr} --bufftimeout -1 --itr ${itr} --dvfs ${dvfs} --nrepeat ${i}  --cores ${NCORES} --query ${MQUERY} --policy userspace --nsource ${nsrc} --nmapper ${nmapper} --nsink ${nsink}
			#sleep 1

			## stop power logging
			#ssh ${IPMAPPER} sudo systemctl stop rapl_log

			#loc="./logs/${MQUERY}_cores${NCORES}_frate${fr}_fbuff-1_itr${itr}_userspacedvfs${dvfs}_repeat${i}"
			#scp -r ${IPMAPPER}:/data/rapl_log.log ${loc}/server2_rapl.log

			scp -r ./logs/* don:/home/handong/flink/11_3_2023_5.15.89_itrlog/
			rm -rf ./logs/*
			echo "[INFO] FINISHED"
		    done
		done
	    done
	done
    done
}

echo "[INFO] END: ${currdate}"

"$@"
