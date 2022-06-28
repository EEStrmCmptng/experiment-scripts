# Energy Efficient Streaming

## Prilimary Knowledge
* `Bootstrap Node`: Linux Machine, Local IP Address: `10.255.15.3`, scripts shall be executed from here
* `Victim Node`: Linux Machine, with specific device driver modified, IP Address: `192.168.1.9`, energy data is collected from here
* `Benchmarks`: Example queries that we used for running experiment. The detailed description for what each query does is in [CASP Benchmark Application for AWS Kinesis](https://github.com/CASP-Systems-BU/cloud-provider-benchmarks)

## Experiment Settings
* `Flink Configuration`: 
  * flink cluster starts on `bootstrap node`
  * one task-executor at `bootstrap node` 
  * one task-executor at `victim node`
* `Logging Frequency`: 
  * Currently the energy logs per network interrupt
  * It can also changed to logging per millisecond.

## Direcotry Layout
* `/datasets`: This directory contains all the parsed csv files for analytical purposes
* `/dependencies` This directory contains all the softwares we used to run the experiment, currently includes `cloud-provider-benchmarks` and `flink`
* `/scripts`: This directory contains all the binary to launch experiment, change config, etc
* `/raw-data`: This directory contains all the raw data files, grouped by experiment datatime

## Requirements
* Everything needs to be running on `Bootstrap Node`, therefore ssh access to bootstrap node is required

## Set Up Experiment Environment
* Connect to `bootstrap Node` by `ssh 10.255.15.3`
* Clone the repo and run `make` to set up the environment 
  * (**not yet inplemented**, do `cd /home/like/eestreaming` instead)
* Check if `victim node` is on by `ping 192.168.1.9`
  * if not and initrd has modification, run `./boot_victim.sh` to re-pack the initrd and boot the victim node. 
  * if not and initrd is not modified, run `./boot_victim_only.sh` to boot the victim with pre-packed initrd. (**Not yet Implemented**)
* Now it is ready to run experiment

## Quick Start
* run `./run-example.sh` will launch one round of example experiment
  * Benchmark: Query 1
  * 1000 queries per second with the 5 minutes lasting time
  * Default hardware setting
  * **DO NOT MODIFY** `clean-sys-log-one.py` and `run_flink_one.sh`, as they were used only for example run
  
## Customized Experiment
* Setup the different hardware paraemters wanted to test on by modifying `clean-sys-log.py` and `run_flink.sh`
  * detailed range of values are listed inside each files 
  * The parameters in these two files must match up, otherwise it will fail
* Setup the Query input rate and lasting time by modifying `run-flink-workload.sh`
  * template is `--ratelist [<rate>_<duration>]^n`
* run `./run-experiment.sh {EXAMPLE NUM}` to launch the experiment
  * The possible EXAMPLE NUM are 1, 3, 5, 8
  
## Results
* The raw data will be stored at `/raw-data` under the experiment start time
* The parsed dataset is stored at `/dataset/tmp2.csv`
  * The location of where the data can be change by modifying `clean-sys-log.py`
* All data are backed up in Google drive.

  


