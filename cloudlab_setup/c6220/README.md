# Running Flink Query1 with 2 sink, 14 source, 16 mappers

## Assume 3 nodes with IP addresses 10.10.1.1, 10.10.1.2, 10.10.1.3
```
10.10.1.1 -> Source/Sink
10.10.1.2 -> Mapper
10.10.1.3 -> JobManager
```

## Update hostname
```
10.10.1.1 -> sudo hostname SourceSink10-1
10.10.1.2 -> sudo hostname Mapper10-2
10.10.1.3 -> sudo hostname JobManager10-3
```

## Repos to clone on all 3 nodes
`
git clone --recursive git@github.com:EEStrmCmptng/experiment-scripts.git
`

## setup nodes
```
# to set up nodes in a clean state
./setup.sh

# set up firewall rules
./set_ufw.sh

# set up msr group so that the user can run rdmsr without being sudo
# NOTE: need to log out and log back in for this to take effect
./msr_setup.sh

# setup RAPL power logging

# first need to create the correct directory
sudo mkdir /data
sudo chmod -R 777 /data

# this will build the rapl tools and systemctl
./rapl_setup.sh

# to test RAPL power logging
sudo systemctl restart rapl_log
sudo systemctl status rapl_log
tail -f /data/rapl_log.txt
sudo systemctl stop rapl_log
```

## setup flink inside experiment-scripts, do this on the JobManager Node
```
git clone git@github.com:EEStrmCmptng/flink-simplified.git
cd flink-simplified/scripts
./makeflink.sh

# clone flink-benchmarks and build it
cd experiment-scripts
git clone git@github.com:EEStrmCmptng/flink-benchmarks.git
mvn clean package

# setup flink-cfg
cd experiment-scripts && cp ./cloudlab_setup/c6220/flink-cfg/* flink-cfg/


```
