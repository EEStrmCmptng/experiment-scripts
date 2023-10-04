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
```
