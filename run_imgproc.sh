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

export NSOURCES=${NSOURCES:="4 8 12 16 24 32 64"}
export NMAPPERS=${NMAPPERS:="4 8 12 16 24 32 64"}
export NSINKS=${NSINKS:="4 8 12 16 24 32 64"}

# The assumption is we use 4 nodes that are identical in terms of hardware
# For now, we assume both the Source and Sink nodes use all available cores, i.e. why $(nproc) below 
export NCORES=${NCORES:=$(nproc)}
export MCFG=${MCFG:="$(nproc);4;$(nproc)"} # Sources; Mappers; Sinks
export SLEEPDISABLE=${SLEEPDISABLE:="0"} # Enable/Disable Cstates on mapper. 0 = cstates enabled

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
echo "[INFO] Input: SLEEPDISABLE ${SLEEPDISABLE}"

function cleanLogs {
    rm -rf /users/hand32/experiment-scripts/flink-simplified/flink-dist/target/flink-1.14.0-bin/flink-1.14.0/log/*.log*
    ssh ${IPSOURCE} rm -rf /users/hand32/experiment-scripts/flink-simplified/flink-dist/target/flink-1.14.0-bin/flink-1.14.0/log/*.log*
    ssh ${IPMAPPER} rm -rf /users/hand32/experiment-scripts/flink-simplified/flink-dist/target/flink-1.14.0-bin/flink-1.14.0/log/*.log*
    ssh ${IPSINK} rm -rf /users/hand32/experiment-scripts/flink-simplified/flink-dist/target/flink-1.14.0-bin/flink-1.14.0/log/*.log*
}

function comboSMS
{
    for nsrc in $NSOURCES; do
	for nmapper in $NMAPPERS; do
	    for nsink in $NSINKS; do		
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
			    python -u runexperiment_cloudlab.py --flinkrate "100_300000" --bufftimeout -1 --itr 1 --dvfs 1 --nrepeat 0 --cores ${NCORES} --query ${MQUERY} --policy ${pol} --nsource ${nsrc} --nmapper ${nmapper} --nsink ${nsink} --sleepdisable ${SLEEPDISABLE}
		
			    echo "[INFO] Run Experiment"
			    echo "🟢 [INFO] python -u runexperiment_cloudlab.py --flinkrate ${fr} --bufftimeout -1 --itr 1 --dvfs 1 --nrepeat ${i} --cores ${NCORES} --query ${MQUERY} --policy ${pol} --nsource ${nsrc} --nmapper ${nmapper} --nsink ${nsink} --sleepdisable ${SLEEPDISABLE}🟢"

			    cleanLogs			    
			    ssh ${IPMAPPER} sudo systemctl stop rapl_log
			    ssh ${IPMAPPER} sudo rm /tmp/rapl.log
			    ssh ${IPMAPPER} sudo systemctl restart rapl_log
			    sleep 1
			    python -u runexperiment_cloudlab.py --flinkrate ${fr} --bufftimeout -1 --itr 1 --dvfs 1 --nrepeat ${i} --cores ${NCORES} --query ${MQUERY} --policy ${pol} --nsource ${nsrc} --nmapper ${nmapper} --nsink ${nsink} --sleepdisable ${SLEEPDISABLE}
			    sleep 1			    
			    ssh ${IPMAPPER} sudo systemctl stop rapl_log
 			    loc="./logs/${MQUERY}_cores${NCORES}_frate${fr}_fbuff-1_itr1_${pol}dvfs1_source${nsrc}_mapper${nmapper}_sink${nsink}_repeat${i}"
 			    scp -r ${IPMAPPER}:/tmp/rapl.log ${loc}/rapl.log
			    #scp -r $loc kd:/home/handong/sesadata/flink/3_16_2024_d430_imgproc/
 			    echo "[INFO] FINISHED"
			done
		    done
		done
	    done
	done
    done    
}

comboSMS

echo "[INFO] END: ${currdate}"

"$@"
