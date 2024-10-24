#!/bin/bash

currdate=$(date +%m_%d_%Y_%H_%M_%S)
#set -x

export BEGIN_ITER=${BEGIN_ITER:="0"}
export NITERS=${NITERS:="0"}
#export MDVFS=${MDVFS:="0c00 0d00 0e00 0f00 1000 1100 1200 1300 1400 1500 1600 1700 1800 1900 1a00"}
export MDVFS=${MDVFS:="0c00 0e00 1000 1200 1400 1600 1800 1a00"}
#export MDVFS=${MDVFS:="1"}
#export ITRS=${ITRS:="1"}
export ITRS=${ITRS:="2 100 200 300 400 500 600 700 800 900 1000"}
export FLINK_RATE=${FLINK_RATE:="200000_600000"} # 200K records-per-second for 600000 milliseconds or 10 minutes
export BUFF=${BUFF:="-1"}
export FLINK_RATE_TYPE=${FLINK_RATE_TYPE:="static"} # Set rate type to static, predictable or spiking

export IPSINK=${IPSINK:="10.10.1.4"}
export IPWINDOW=${IPWINDOW:="10.10.1.3"}
export IPSOURCE=${IPSOURCE:="10.10.1.2"}
export WINDOW_LENGTH=${WINDOW_LENGTH:="0"}
export MQUERY=${MQUERY:="query5"}
export MPOLICY=${MPOLICY:="ondemand"} # Other policies: conservative powersave performance schedutil

# Checkpointing
export FLINK_CHECKPOINTING_ENABLED=${FLINK_CHECKPOINTING_ENABLED:="false"}
export FLINK_CHECKPOINTING_INTERVAL=${FLINK_CHECKPOINTING_INTERVAL:="10000"}
export FLINK_CHECKPOINTING_MODE=${FLINK_CHECKPOINTING_MODE:="exactly_once"}  # exactly_once, atleast_once
export FLINK_ROCKSDB_STATE_BACKEND_ENABLED=${FLINK_ROCKSDB_STATE_BACKEND_ENABLED:="false"}

# The assumption is we use 4 nodes that are identical in terms of hardware
# For now, we assume both the Source and Sink nodes use all available cores, i.e. why $(nproc) below
export NCORES=${NCORES:=$(nproc)}
export MCFG=${MCFG:="$(nproc);4;$(nproc)"} # Sources; Windows; Sinks

# This is to ensure number of task slots is never less than the amount of cores
# No work gets done by flink if taskmanager.numberOfTaskSlots <  max(Sources or Windows or Sinks)
sed -i "s/taskmanager.numberOfTaskSlots:.*/taskmanager.numberOfTaskSlots: $(nproc)/" flink-query5-cfg/flink-conf.yaml

# If not rocksdb then just comment out the backend props, default to heap implementation
if [[ "$FLINK_ROCKSDB_STATE_BACKEND_ENABLED" == "true" ]]; then
	sed -i '/state\.backend:/s/.*/state.backend: rocksdb/' flink-query5-cfg/flink-conf.yaml
else
	sed -i '/state\.backend:/s/.*/# state.backend: /' flink-query5-cfg/flink-conf.yaml
fi

echo "[INFO] START: ${currdate}"
echo "[INFO] Input: MPOLICY ${MPOLICY}"
echo "[INFO] Input: MQUERY ${MQUERY}"
echo "[INFO] Input: DVFS ${MDVFS}"
echo "[INFO] Input: ITRS ${ITRS}"
echo "[INFO] Input: NITERS ${NITERS}"
echo "[INFO] Input: FLINK_RATE ${FLINK_RATE}"
echo "[INFO] Input: FLINK_RATE_TYPE ${FLINK_RATE_TYPE}"

echo "[INFO] Input: BUFF ${BUFF}"
echo "[INFO] Input: NCORES ${NCORES}"
echo "[INFO] Input: IPWINDOW ${IPWINDOW}"
echo "[INFO] Input: MCFG ${MCFG}"
echo "[INFO] Input: WINDOW_LENGTH ${WINDOW_LENGTH}"


echo "[INFO] Input: FLINK_CHECKPOINTING_ENABLED ${FLINK_CHECKPOINTING_ENABLED}"
echo "[INFO] Input: FLINK_CHECKPOINTING_INTERVAL ${FLINK_CHECKPOINTING_INTERVAL}"
echo "[INFO] Input: FLINK_CHECKPOINTING_MODE ${FLINK_CHECKPOINTING_MODE}"
echo "[INFO] Input: FLINK_ROCKSDB_STATE_BACKEND_ENABLED ${FLINK_ROCKSDB_STATE_BACKEND_ENABLED}"

function cleanLogs {
	rm -rf /users/$(whoami)/experiment-scripts/flink-simplified/flink-dist/target/flink-1.14.0-bin/flink-1.14.0/log/*.log*
        rm -rf ~/flink-experiments/flink-simplified/flinkstate/*

	ssh ${IPSOURCE} rm -rf /users/$(whoami)/experiment-scripts/flink-simplified/flink-dist/target/flink-1.14.0-bin/flink-1.14.0/log/*.log*
	ssh ${IPWINDOW} rm -rf /users/$(whoami)/experiment-scripts/flink-simplified/flink-dist/target/flink-1.14.0-bin/flink-1.14.0/log/*.log*
	ssh ${IPSINK} rm -rf /users/$(whoami)/experiment-scripts/flink-simplified/flink-dist/target/flink-1.14.0-bin/flink-1.14.0/log/*.log*

	ssh ${IPSOURCE} rm -rf /tmp/*.jar
	ssh ${IPSOURCE} rm -rf /tmp/rocksdb-lib-*.jar
	ssh ${IPSOURCE} rm -rf ~/flink-experiments/flink-simplified/flinkstate/*

	ssh ${IPWINDOW} rm -rf /tmp/*.jar
	ssh ${IPWINDOW} rm -rf /tmp/rocksdb-lib-*.jar
	ssh ${IPWINDOW} rm -rf ~/flink-experiments/flink-simplified/flinkstate/*

	ssh ${IPSINK} rm -rf /tmp/*.jar
	ssh ${IPSINK} rm -rf /tmp/rocksdb-lib-*.jar
	ssh ${IPSINK} rm -rf ~/flink-experiments/flink-simplified/flinkstate/*
}

function dynamic {
	for cfg in $MCFG; do
		echo $cfg
		nsrc=$(echo $cfg | cut -d ";" -f 1)
		nwindow=$(echo $cfg | cut -d ";" -f 2)
		nsink=$(echo $cfg | cut -d ";" -f 3)
		
		rm flink-query5-cfg/schedulercfg
		for t in $(seq 1 1 $nsrc); do
			echo "Source; ${IPSOURCE}" >> flink-query5-cfg/schedulercfg
		done
		for t in $(seq 1 1 $nwindow); do
			echo "Window; ${IPWINDOW}" >> flink-query5-cfg/schedulercfg
		done
		for t in $(seq 1 1 $nsink); do
			echo "Sink; ${IPSINK}" >> flink-query5-cfg/schedulercfg
		done

		for i in $(seq ${BEGIN_ITER} 1 $NITERS); do
			for fr in $FLINK_RATE; do
			    for pol in $MPOLICY; do
				# stops pre-existing flink cluster and cleans up state
				echo "[INFO] python runexperiment_cloudlab.py --query ${MQUERY} --runcmd stopflink"
				python run_query5.py --query ${MQUERY} --runcmd stopflink
				
				# starts flink cluster
				echo "[INFO] python run_query5.py --query ${MQUERY} --runcmd startflink"
				python run_query5.py --query ${MQUERY} --runcmd startflink

				# Doing a warmup run first
				python -u run_query5.py --flinkrate 666_6666 --flinkratetype ${FLINK_RATE_TYPE} --bufftimeout -1 --itr 1 --dvfs 1 --nrepeat ${i} --cores ${NCORES} --query ${MQUERY} --policy ${pol} --nsource ${nsrc} --nwindow ${nwindow} --nsink ${nsink} --windowlength ${WINDOW_LENGTH} --checkpointingenabled ${FLINK_CHECKPOINTING_ENABLED} --checkpointinginterval ${FLINK_CHECKPOINTING_INTERVAL} --checkpointingmode ${FLINK_CHECKPOINTING_MODE} --rocksdbstatebackendenabled ${FLINK_ROCKSDB_STATE_BACKEND_ENABLED}
				
				
				echo "[INFO] Run Experiment"
				echo "[INFO] python -u run_query5.py --flinkrate ${fr} --flinkratetype ${FLINK_RATE_TYPE} --bufftimeout -1 --itr 1 --dvfs 1 --nrepeat ${i} --cores ${NCORES} --query ${MQUERY} --policy ${pol} --nsource ${nsrc} --nwindow ${nwindow} --nsink ${nsink} --windowlength ${WINDOW_LENGTH} --checkpointingenabled ${FLINK_CHECKPOINTING_ENABLED} --checkpointinginterval ${FLINK_CHECKPOINTING_INTERVAL} --checkpointingmode ${FLINK_CHECKPOINTING_MODE} --rocksdbstatebackendenabled ${FLINK_ROCKSDB_STATE_BACKEND_ENABLED}"

				cleanLogs
				
				# enable power logging
				ssh ${IPWINDOW} sudo systemctl stop rapl_log
				ssh ${IPWINDOW} sudo rm /tmp/rapl.log
				ssh ${IPWINDOW} sudo systemctl restart rapl_log

				# start logging CPU usage
				#ssh ${IPWINDOW} sudo rm -f /data/cpu.txt
				#ssh ${IPWINDOW} "sudo sar -u 15 > /data/cpu.txt 2>&1 < /dev/null &"
				
				python -u run_query5.py --flinkrate ${fr} --flinkratetype ${FLINK_RATE_TYPE} --bufftimeout -1 --itr 1 --dvfs 1 --nrepeat ${i} --cores ${NCORES} --query ${MQUERY} --policy ${pol} --nsource ${nsrc} --nwindow ${nwindow} --nsink ${nsink} --windowlength ${WINDOW_LENGTH} --checkpointingenabled ${FLINK_CHECKPOINTING_ENABLED} --checkpointinginterval ${FLINK_CHECKPOINTING_INTERVAL} --checkpointingmode ${FLINK_CHECKPOINTING_MODE} --rocksdbstatebackendenabled ${FLINK_ROCKSDB_STATE_BACKEND_ENABLED}
				
				# retrieve power data from window node
				ssh ${IPWINDOW} sudo systemctl stop rapl_log
				
				loc="./logs/${MQUERY}_cores${NCORES}_frate${fr}_fratetype_${FLINK_RATE_TYPE}_fbuff-1_itr1_${pol}dvfs1_source${nsrc}_window${nwindow}_sink${nsink}"
				

				if [ "$WINDOW_LENGTH" != "0" ]; then
				    loc="${loc}_windowlength${WINDOW_LENGTH}"
				fi
				
				if [[ "$FLINK_CHECKPOINTING_ENABLED" == "true" ]]; then
				    loc="${loc}_cpint${FLINK_CHECKPOINTING_INTERVAL}_cpmode_${FLINK_CHECKPOINTING_MODE}"				    
				fi

				if [[ "$FLINK_ROCKSDB_STATE_BACKEND_ENABLED" == "true" ]]; then
				    loc="${loc}_cpbckend_rocksdb"
				fi
				
				loc="${loc}_repeat${i}"
				scp -r ${IPWINDOW}:/tmp/rapl.log ${loc}/rapl.log
				
				# Retrieve cpu usage from window node
				#ssh ${IPWINDOW} "sudo pkill -9 -f sar"
				#scp -r ${IPWINDOW}:/data/cpu.txt ${loc}/cpu.txt
				
				echo "[INFO] FINISHED"
			    done
			done
		done
	done
}

function checkpoints {
    for cfg in $MCFG; do
	echo $cfg
	nsrc=$(echo $cfg | cut -d ";" -f 1)
	nwindow=$(echo $cfg | cut -d ";" -f 2)
	nsink=$(echo $cfg | cut -d ";" -f 3)
	
	rm flink-query5-cfg/schedulercfg
	for t in $(seq 1 1 $nsrc); do
	    echo "Source; ${IPSOURCE}" >> flink-query5-cfg/schedulercfg
	done
	for t in $(seq 1 1 $nwindow); do
	    echo "Window; ${IPWINDOW}" >> flink-query5-cfg/schedulercfg
	done
	for t in $(seq 1 1 $nsink); do
	    echo "Sink; ${IPSINK}" >> flink-query5-cfg/schedulercfg
	done

	for i in $(seq ${BEGIN_ITER} 1 $NITERS); do
	    for fr in $FLINK_RATE; do
		for pol in $MPOLICY; do
		    for checkpoint_interval in $FLINK_CHECKPOINTING_INTERVAL; do
			for checkpoint_mode in $FLINK_CHECKPOINTING_MODE; do
			    # stops pre-existing flink cluster and cleans up state
			    echo "[INFO] python runexperiment_cloudlab.py --query ${MQUERY} --runcmd stopflink"
			    python run_query5.py --query ${MQUERY} --runcmd stopflink
		    
			    # starts flink cluster
			    echo "[INFO] python run_query5.py --query ${MQUERY} --runcmd startflink"
			    python run_query5.py --query ${MQUERY} --runcmd startflink
			    
			    # Doing a warmup run first
			    python -u run_query5.py --flinkrate 666_6666 --flinkratetype ${FLINK_RATE_TYPE} --bufftimeout -1 --itr 1 --dvfs 1 --nrepeat ${i} --cores ${NCORES} --query ${MQUERY} --policy ${pol} --nsource ${nsrc} --nwindow ${nwindow} --nsink ${nsink} --windowlength ${WINDOW_LENGTH} --checkpointingenabled ${FLINK_CHECKPOINTING_ENABLED} --checkpointinginterval ${checkpoint_interval} --checkpointingmode ${checkpoint_mode} --rocksdbstatebackendenabled ${FLINK_ROCKSDB_STATE_BACKEND_ENABLED}
		    
		    
			    echo "[INFO] Run Experiment"
			    echo "[INFO] python -u run_query5.py --flinkrate 666_6666 --flinkratetype ${FLINK_RATE_TYPE} --bufftimeout -1 --itr 1 --dvfs 1 --nrepeat ${i} --cores ${NCORES} --query ${MQUERY} --policy ${pol} --nsource ${nsrc} --nwindow ${nwindow} --nsink ${nsink} --windowlength ${WINDOW_LENGTH} --checkpointingenabled ${FLINK_CHECKPOINTING_ENABLED} --checkpointinginterval ${checkpoint_interval} --checkpointingmode ${checkpoint_mode} --rocksdbstatebackendenabled ${FLINK_ROCKSDB_STATE_BACKEND_ENABLED}"
			    
			    cleanLogs
			    
			    # enable power logging
			    ssh ${IPWINDOW} sudo systemctl stop rapl_log
			    ssh ${IPWINDOW} sudo rm /tmp/rapl.log
			    ssh ${IPWINDOW} sudo systemctl restart rapl_log
			    
			    # start logging CPU usage
			    #ssh ${IPWINDOW} sudo rm -f /data/cpu.txt
			    #ssh ${IPWINDOW} "sudo sar -u 15 > /data/cpu.txt 2>&1 < /dev/null &"
		    
			    python -u run_query5.py --flinkrate ${fr} --flinkratetype ${FLINK_RATE_TYPE} --bufftimeout -1 --itr 1 --dvfs 1 --nrepeat ${i} --cores ${NCORES} --query ${MQUERY} --policy ${pol} --nsource ${nsrc} --nwindow ${nwindow} --nsink ${nsink} --windowlength ${WINDOW_LENGTH} --checkpointingenabled ${FLINK_CHECKPOINTING_ENABLED} --checkpointinginterval ${checkpoint_interval} --checkpointingmode ${checkpoint_mode} --rocksdbstatebackendenabled ${FLINK_ROCKSDB_STATE_BACKEND_ENABLED}
		    
			    # retrieve power data from window node
			    ssh ${IPWINDOW} sudo systemctl stop rapl_log
		    
			    loc="./logs/${MQUERY}_cores${NCORES}_frate${fr}_fratetype_${FLINK_RATE_TYPE}_fbuff-1_itr1_${pol}dvfs1_source${nsrc}_window${nwindow}_sink${nsink}"
			    
		    
			    if [ "$WINDOW_LENGTH" != "0" ]; then
				loc="${loc}_windowlength${WINDOW_LENGTH}"
			    fi
			    
			    if [[ "$FLINK_CHECKPOINTING_ENABLED" == "true" ]]; then
				loc="${loc}_cpint${checkpoint_interval}_cpmode_${checkpoint_mode}"				    
			    fi
		    
			    if [[ "$FLINK_ROCKSDB_STATE_BACKEND_ENABLED" == "true" ]]; then
				loc="${loc}_cpbckend_rocksdb"
			    fi
			    
			    loc="${loc}_repeat${i}"
			    scp -r ${IPWINDOW}:/tmp/rapl.log ${loc}/rapl.log
			    
			    # Retrieve cpu usage from window node
			    #ssh ${IPWINDOW} "sudo pkill -9 -f sar"
			    #scp -r ${IPWINDOW}:/data/cpu.txt ${loc}/cpu.txt
			    
			    echo "[INFO] FINISHED"
			done
		    done
		done
	    done
	done
    done
}

function static {
    for cfg in $MCFG; do
	echo $cfg
	nsrc=$(echo $cfg | cut -d ";" -f 1)
	nwindow=$(echo $cfg | cut -d ";" -f 2)
	nsink=$(echo $cfg | cut -d ";" -f 3)
	
	rm flink-query5-cfg/schedulercfg
	for t in $(seq 1 1 $nsrc); do
	    echo "Source; ${IPSOURCE}" >> flink-query5-cfg/schedulercfg
	done
	for t in $(seq 1 1 $nwindow); do
	    echo "Window; ${IPWINDOW}" >> flink-query5-cfg/schedulercfg
	done
	for t in $(seq 1 1 $nsink); do
	    echo "Sink; ${IPSINK}" >> flink-query5-cfg/schedulercfg
	done

	for i in $(seq ${BEGIN_ITER} 1 $NITERS); do
	    for fr in $FLINK_RATE; do
		for itr in $ITRS; do
		    for dvfs in $MDVFS; do			
			# stops pre-existing flink cluster and cleans up state
			echo "[INFO] python runexperiment_cloudlab.py --query ${MQUERY} --runcmd stopflink"
			python run_query5.py --query ${MQUERY} --runcmd stopflink
			
			# starts flink cluster
			echo "[INFO] python run_query5.py --query ${MQUERY} --runcmd startflink"
			python run_query5.py --query ${MQUERY} --runcmd startflink

			# Doing a warmup run first
			python -u run_query5.py --flinkrate 666_6666 --flinkratetype ${FLINK_RATE_TYPE} --bufftimeout -1 --itr 1 --dvfs 1 --nrepeat ${i} --cores ${NCORES} --query ${MQUERY} --policy "userspace" --nsource ${nsrc} --nwindow ${nwindow} --nsink ${nsink} --windowlength ${WINDOW_LENGTH} --checkpointingenabled ${FLINK_CHECKPOINTING_ENABLED} --checkpointinginterval ${FLINK_CHECKPOINTING_INTERVAL} --checkpointingmode ${FLINK_CHECKPOINTING_MODE} --rocksdbstatebackendenabled ${FLINK_ROCKSDB_STATE_BACKEND_ENABLED}
			
			
			echo "[INFO] Run Experiment"
			echo "[INFO] python -u run_query5.py --flinkrate ${fr} --flinkratetype ${FLINK_RATE_TYPE} --bufftimeout -1 --itr 1 --dvfs 1 --nrepeat ${i} --cores ${NCORES} --query ${MQUERY} --policy userspace --nsource ${nsrc} --nwindow ${nwindow} --nsink ${nsink} --windowlength ${WINDOW_LENGTH} --checkpointingenabled ${FLINK_CHECKPOINTING_ENABLED} --checkpointinginterval ${FLINK_CHECKPOINTING_INTERVAL} --checkpointingmode ${FLINK_CHECKPOINTING_MODE} --rocksdbstatebackendenabled ${FLINK_ROCKSDB_STATE_BACKEND_ENABLED}"

			cleanLogs
			
			# enable power logging
			ssh ${IPWINDOW} sudo systemctl stop rapl_log
			ssh ${IPWINDOW} sudo rm /tmp/rapl.log
			ssh ${IPWINDOW} sudo systemctl restart rapl_log

			# start logging CPU usage
			#ssh ${IPWINDOW} sudo rm -f /data/cpu.txt
			#ssh ${IPWINDOW} "sudo sar -u 15 > /data/cpu.txt 2>&1 < /dev/null &"
			
			python -u run_query5.py --flinkrate ${fr} --flinkratetype ${FLINK_RATE_TYPE} --bufftimeout -1 --itr ${itr} --dvfs ${dvfs} --nrepeat ${i} --cores ${NCORES} --query ${MQUERY} --policy "userspace" --nsource ${nsrc} --nwindow ${nwindow} --nsink ${nsink} --windowlength ${WINDOW_LENGTH} --checkpointingenabled ${FLINK_CHECKPOINTING_ENABLED} --checkpointinginterval ${FLINK_CHECKPOINTING_INTERVAL} --checkpointingmode ${FLINK_CHECKPOINTING_MODE} --rocksdbstatebackendenabled ${FLINK_ROCKSDB_STATE_BACKEND_ENABLED}
			
			# retrieve power data from window node
			ssh ${IPWINDOW} sudo systemctl stop rapl_log
			
			loc="./logs/${MQUERY}_cores${NCORES}_frate${fr}_fratetype_${FLINK_RATE_TYPE}_fbuff-1_itr${itr}_userspacedvfs${dvfs}_source${nsrc}_window${nwindow}_sink${nsink}"
			

			if [ "$WINDOW_LENGTH" != "0" ]; then
			    loc="${loc}_windowlength${WINDOW_LENGTH}"
			fi
			
			if [[ "$FLINK_CHECKPOINTING_ENABLED" == "true" ]]; then
			    loc="${loc}_cpint${FLINK_CHECKPOINTING_INTERVAL}_cpmode_${FLINK_CHECKPOINTING_MODE}"
			fi

			if [[ "$FLINK_ROCKSDB_STATE_BACKEND_ENABLED" == "true" ]]; then
			    loc="${loc}_cpbckend_rocksdb"
			fi
			
			loc="${loc}_repeat${i}"
			scp -r ${IPWINDOW}:/tmp/rapl.log ${loc}/rapl.log
			#scp -r $loc kd:/home/handong/sesadata/flink/query5_7_10_2024/
			
			# Retrieve cpu usage from window node
			#ssh ${IPWINDOW} "sudo pkill -9 -f sar"
			#scp -r ${IPWINDOW}:/data/cpu.txt ${loc}/cpu.txt
			
			echo "[INFO] FINISHED"
		    done
		done
	    done
	done
    done
}

echo "[INFO] END: ${currdate}"

"$@"

