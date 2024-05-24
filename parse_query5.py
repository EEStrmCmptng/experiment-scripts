import pandas as pd
import numpy as np
import argparse
import itertools

import re
import os
from os import path
import sys
import time

# Linux dvfs policies: https://www.kernel.org/doc/Documentation/cpu-freq/governors.txt
policies = ["ondemand"]

# total time to run for, in ms
times = [300000, 600000]

# diff flink rates
rates = [3000]

# number of windows
windows = [4, 12]

# window lengths
windowlen = [5, 20, 60]

# not exploring different combo for these yet
itrs = [1]
dvfss = [1]
sources = [1] # num of sources
sinks = [16] # num of sinks
ncores = [16] # num of physical cores to use

df_dict = {
    'i': [], 'itr': [], 'dvfs': [], 'rate': [], 'policy': [], 'nwindows':[],
    'watts_avg': [], 'watts_std': [],
    
    'pollCnt': [], 'c1Cnt': [], 'c1eCnt': [],'c3Cnt': [], 'c6Cnt': [], 
    'rxPackets': [], 'rxBytes': [], 'txPackets': [], 'txBytes': [],
    'erxPackets': [], 'erxBytes':[], 'etxPackets': [], 'etxBytes':[],
    
    'SinknumRecordsInPerSecond_avg': [], 'SinknumRecordsInPerSecond_std': [], 
    'SinknumRecordsOutPerSecond_avg': [], 'SinknumRecordsOutPerSecond_std': [], 
    'SinkbusyTimeMsPerSecond_avg': [], 'SinkbusyTimeMsPerSecond_std': [], 
    'SinkbackPressuredTimeMsPerSecond_avg': [], 'SinkbackPressuredTimeMsPerSecond_std': [], 
    'SinkbusyTime_%': [], 'SinkbackPressuredTime_%': [], 

    'SourcenumRecordsInPerSecond_avg': [], 'SourcenumRecordsInPerSecond_std': [], 
    'SourcenumRecordsOutPerSecond_avg': [], 'SourcenumRecordsOutPerSecond_std': [], 
    'SourcebusyTimeMsPerSecond_avg': [], 'SourcebusyTimeMsPerSecond_std': [], 
    'SourcebackPressuredTimeMsPerSecond_avg': [], 'SourcebackPressuredTimeMsPerSecond_std': [], 
    'SourcebusyTime_%': [], 'SourcebackPressuredTime_%': [], 

    'WindownumRecordsInPerSecond_avg': [], 
    'WindownumRecordsInPerSecond_std': [], 'WindownumRecordsOutPerSecond_avg': [], 
    'WindownumRecordsOutPerSecond_std': [], 'WindowbusyTimeMsPerSecond_avg': [], 
    'WindowbusyTimeMsPerSecond_std': [], 'WindowbackPressuredTimeMsPerSecond_avg': [], 
    'WindowbackPressuredTimeMsPerSecond_std': [],
    'WindowbusyTime_%': [], 'WindowbackPressuredTime_%': [], 'Windowlength': []
}

# print(df_dict)
print("*****************************************************************")

def resetdf():
    global df_dict
    df_dict = {
    'i': [], 'itr': [], 'dvfs': [], 'rate': [], 'policy': [], 'nwindows':[],
    'watts_avg': [], 'watts_std': [],
    
    'SinknumRecordsInPerSecond_avg': [], 'SinknumRecordsInPerSecond_std': [], 
    'SinknumRecordsOutPerSecond_avg': [], 'SinknumRecordsOutPerSecond_std': [], 
    'SinkbusyTimeMsPerSecond_avg': [], 'SinkbusyTimeMsPerSecond_std': [], 
    'SinkbackPressuredTimeMsPerSecond_avg': [], 'SinkbackPressuredTimeMsPerSecond_std': [], 
    'SinkbusyTime_%': [], 'SinkbackPressuredTime_%': [], 

    'SourcenumRecordsInPerSecond_avg': [], 'SourcenumRecordsInPerSecond_std': [], 
    'SourcenumRecordsOutPerSecond_avg': [], 'SourcenumRecordsOutPerSecond_std': [], 
    'SourcebusyTimeMsPerSecond_avg': [], 'SourcebusyTimeMsPerSecond_std': [], 
    'SourcebackPressuredTimeMsPerSecond_avg': [], 'SourcebackPressuredTimeMsPerSecond_std': [], 
    'SourcebusyTime_%': [], 'SourcebackPressuredTime_%': [], 

    'WindownumRecordsInPerSecond_avg': [], 
    'WindownumRecordsInPerSecond_std': [], 'WindownumRecordsOutPerSecond_avg': [], 
    'WindownumRecordsOutPerSecond_std': [], 'WindowbusyTimeMsPerSecond_avg': [], 
    'WindowbusyTimeMsPerSecond_std': [], 'WindowbackPressuredTimeMsPerSecond_avg': [], 
    'WindowbackPressuredTimeMsPerSecond_std': [],
    'WindowbusyTime_%': [], 'WindowbackPressuredTime_%': [], 'Windowlength': []
    }

def parseFile(loc, rate, itr, dvfs, policy, i, window, timems, windowlength):
    file=f"{loc}/summary.csv"

    df_dict['i'].append(i)
    df_dict['itr'].append(itr)
    df_dict['nwindows'].append(window)

    df_dict['dvfs'].append(dvfs)

    df_dict['policy'].append(policy)
    df_dict['rate'].append(rate)
    df_dict['Windowlength'].append(windowlength)

    df = pd.read_csv(file)
    df = df[df.columns.drop(list(df.filter(regex='Cnt')))]
    df = df[df.columns.drop(list(df.filter(regex='Bytes')))]

    dff = df[df['name'].str.contains('Sink')]
    dff.columns = 'Sink' + dff.columns
    cols = dff.columns
    for col in cols[2:]:
        df_dict[col].append(dff.mean(numeric_only=True)[col])

    dff = df[df['name'].str.contains('Source')]
    dff.columns = 'Source' + dff.columns
    cols = dff.columns
    for col in cols[2:]:
        df_dict[col].append(dff.mean(numeric_only=True)[col])

    dff = df[df['name'].str.contains('Window')]
    dff.columns = 'Window' + dff.columns
    cols = dff.columns
    for col in cols[2:]:
        df_dict[col].append(dff.mean(numeric_only=True)[col])

    # server2_rapl.log collects Power (energy/second) data
    jfile = f"{loc}/rapl.log"
    with open(jfile) as file:
        lines = [float(line.rstrip()) for line in file]

        # extract values from 40%-80% of total time to account for warmup time and capture region of compute
        time_in_secs = timems/1000
        stime = int(time_in_secs * 0.4)
        etime = int(time_in_secs * 0.8)

        # get the average Power within this timeslot
        df_dict['watts_avg'].append(float(round(np.mean(lines[stime:etime]), 2)))
        df_dict['watts_std'].append(float(round(np.std(lines[stime:etime]), 2)))
        
def parse(loc1, name, ratetype, checkpointinginterval, checkpointingmode, rocksdbstatebackendenabled):
    nrepeat = 3
    resetdf()
    # print(df_dict)

    # Generate combinations of items from the
    combinations = list(itertools.product(policies, rates, times, itrs, dvfss, windows, ncores, sources, sinks, windowlen))
    combined_file_name = None
    # Print the combinations
    for combo in combinations:
        policy, rate, timems, itr, dvfs, window, cores, source, sink, windowlength = combo
        combined_file_name = f"{loc1}/combined_{rate}_{ratetype}"
        loc  = f"{loc1}/{name}_cores{cores}_frate{rate}_{timems}_fratetype_{ratetype}_fbuff-1_itr{itr}_{policy}dvfs{dvfs}_source{source}_window{window}_sink{sink}_windowlength{windowlength}"
        
        if checkpointinginterval:
            loc = f"{loc}_cpint{checkpointinginterval}"
            combined_file_name = f"{combined_file_name}_{checkpointinginterval}"
        if checkpointingmode:
            loc = f"{loc}_cpmode_{checkpointingmode}"
            combined_file_name = f"{combined_file_name}_{checkpointingmode}"
        if rocksdbstatebackendenabled:
            loc = f"{loc}_cpbckend_rocksdb"
            combined_file_name = f"{combined_file_name}_rocksdb"
        for i in range(nrepeat):
            loc_i = f"{loc}_repeat{i}"
            #print(f"[DEBUG] location: {loc}")
            if not path.exists(loc_i+ "/summary.csv"):
                break
            print(loc_i)
            parseFile(loc_i, rate, itr, dvfs, policy, i, window, timems, windowlength)

    # print(df_dict)
    dd1 = pd.DataFrame(df_dict)
    print(len(dd1.index))    
    dd1.to_csv(f"{combined_file_name}.csv", mode='w')

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--log", help="log location", required=True)
    parser.add_argument("--name", help="ie query1", default="query1", required=True)
    parser.add_argument("--ratetype", help="Input rate type: static, predictable, spike", default="static")
    parser.add_argument("--checkpointinginterval", help="Checkpointing interval")
    parser.add_argument("--checkpointingmode", help="Checkpointing Mode")
    parser.add_argument("--rocksdbstatebackendenabled", help="RocksDb Backend Enabled")
    args = parser.parse_args()

    loc=args.log
    name=args.name

    try:        
        #rates.append(rate)
        parse(loc, name, args.ratetype, args.checkpointinginterval, args.checkpointingmode, args.rocksdbstatebackendenabled)
    except Exception as error:
        print(error)

