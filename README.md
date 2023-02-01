
## Clone repo

```
git clone --branch refactor git@github.com:EEStrmCmptng/experiment-scripts.git
cd experiment-scripts
git clone git@github.com:EEStrmCmptng/flink-benchmarks.git
git clone --branch energy git@github.com:pentium3/cs551-flink.git flink-simplified
```


## Compile

Compile Flink

```
cd flink-simplified/scripts
./makeflink.sh
```

Compile Query

```
cd flink-benchmarks
python3 build.py 1
```

## set configuration

In `flink-cfg`

## run experiment

eg: 

`python3 runexperiment.py --rapl 50 --itr 10 --dvfs 0xfff --nrepeat 1 --flinkrate 100_100000 --cores 16`

## run cleanup script

eg: 

`python3 cleanup.py --rapl 50 --itr 10 --dvfs 0xfff --nrepeat 1 --flinkrate 100_100000 --cores 16`

## run both

Add all sweep values at the top of `run_total.sh`
Run `./run_total.sh`
