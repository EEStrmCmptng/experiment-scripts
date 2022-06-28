## Requirements
* Access to Han's Bootstrap node

## Steps
* To run the scripts, first ssh to the Bootstrap node using `ssh 10.255.15.3`. 
* Move to the directory by using `/home/like/eestreaming`. In this directory, it includes several sub-directories.
* `dependencies` includes `cloud-provider-benchmarks` referenced from Yuanli and `flink` installed. Additionally, in the `flink`, there is a python file named `output-average-latency.py` which collects all the latency values reported and output an average. 
* `datasets` is the place where the raw-processed data is. 
* `datasets` is the place where the raw-processed data is.
* `scripts` includes all the scripts to run.
