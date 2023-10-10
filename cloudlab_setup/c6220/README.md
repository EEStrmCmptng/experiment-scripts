# Running Flink Query1 with 2 sink, 14 source, 16 mappers

## Assume 3 nodes with IP addresses 10.10.1.1, 10.10.1.2, 10.10.1.3
```

10.10.1.1 -> Source/Sink
10.10.1.2 -> Mapper
10.10.1.3 -> JobManager
```
![Screenshot from 2023-10-10 09-38-30](https://github.com/EEStrmCmptng/experiment-scripts/assets/23284162/60dc741d-0a04-4b32-8b50-5de74d7febaf)

## Update hostname on all 3 nodes
```
10.10.1.1 -> sudo hostname SourceSink10-1
10.10.1.2 -> sudo hostname Mapper10-2
10.10.1.3 -> sudo hostname JobManager10-3
```

## setup on all 3 nodes
```
# first repo to clone on all 3 nodes
git clone --recursive git@github.com:EEStrmCmptng/experiment-scripts.git

# e.g. for node type c6220 on Cloudlab
cd ~/experiment-scripts/cloudlab_setup/c6220

# to set up nodes in a clean state, this downloads libraries and sets up tools
./setup.sh

# set up firewall rules to block all traffic except the ones for Flinl
./set_ufw.sh

# set up msr group so that the user can run rdmsr without being sudo. NOTE: need to log out and log back in for this to take effect
./msr_setup.sh

# set ethtool to run without sudo
sudo setcap cap_net_admin+ep /usr/sbin/ethtool

# setup RAPL power logging
# first need to create the correct directory as the rapl_log.py writes to /data/rapl_log.log
sudo mkdir /data
sudo chmod -R 777 /data

# Open rapl_service/rapl_log.service and rapl_service/rapl_log.py and change path to your user

# this will build the rapl tools and systemctl
./rapl_setup.sh

# to test RAPL power logging
sudo systemctl restart rapl_log
sudo systemctl status rapl_log
tail -f /data/rapl_log.log
sudo systemctl stop rapl_log
```

## setup flink inside experiment-scripts, do this on the JobManager Node only
```
cd ~/experiment-scripts
git clone git@github.com:EEStrmCmptng/flink-simplified.git
cd flink-simplified/scripts
./makeflink.sh

# clone flink-benchmarks and build it
cd ~/experiment-scripts
git clone git@github.com:EEStrmCmptng/flink-benchmarks.git
cd flink-benchmarks
mvn clean package

# setup flink-cfg to run with 16 mappers, 14 sources, 2 sinks - hardcoded for now
cd ~/experiment-scripts && cp ./cloudlab_setup/c6220/flink-cfg/* flink-cfg/
```

## Example run commands
```
NITERS="0" FLINK_RATE="300000_600000" MPOLICY="ondemand performance powersave" ./run_query1.sh dynamic
NITERS="2" FLINK_RATE="200000_180000" ITRS="2 4 80" MDVFS="1800 1900" ./run_query1.sh static
```
