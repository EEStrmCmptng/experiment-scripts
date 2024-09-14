import pandas as pd
import numpy as np
import argparse
import itertools

import re
import os
from os import path
import sys
import time

# DVFS to CPU frequency map
dvfs_dict = {
    "0x1" : 1,
    "0x0c00" :  1.2,
    "0x0d00" :  1.3,
    "0x0e00" :  1.4,
    "0x0f00" :  1.5,
    "0x1000" : 1.6,
    "0x1100" : 1.7,
    "0x1200" : 1.8,
    "0x1300" : 1.9,
    "0x1400" : 2.0,
    "0x1500" : 2.1,
    "0x1600" : 2.2,
    "0x1700" : 2.3,
    "0x1800" : 2.4,
    "0x1900" : 2.5,
    "0x1a00" : 2.6,
    "0x1b00" : 2.7,
    "0x1c00" : 2.8,
    "0x1d00" : 2.9,
}

# Linux dvfs policies: https://www.kernel.org/doc/Documentation/cpu-freq/governors.txt
#policies = ["ondemand", "conservative", "performance", "schedutil", "powersave", "userspace"]
policies = ["ondemand", "userspace"]

# total time to run for, in ms
times = [300000, 600000]

# diff flink rates
#rates = [i for i in range(100000,2100000,10000)] #2100 because python excludes last value.
#rates = [i for i in range(1000,50000,1000)] #2100 because python excludes last value.
#rates = [2000, 4000]
rates = [6000, 12000, 18000, 24000]
#rates = [i for i in range(10000,200000,10000)] #2100 because python excludes last value.

# window lengths
windowlen = [20, 60]

# not exploring different combo for these yet
#itrs = [1, 2, 50, 100, 150, 200, 250, 300, 350, 400, 450, 500, 550, 600, 650, 700, 750, 800, 850, 900, 950, 1000]
#dvfss = ['1', '0c00', '0d00', '0e00', '0f00', '1000', '1100', '1200', '1300', '1400', '1500', '1600', '1700', '1800', '1900', '1a00']
itrs = [1]
dvfss = ['1']
sources = [1] # num of sources
windows = [4, 8, 12, 16] # number of windows
sinks = [16] # num of sinks
ncores = [16] # num of physical cores to use

df_dict = {
    'i': [], 'itr': [], 'dvfs': [], 'rate': [], 'policy': [], 'nwindows':[],
    'pkg_watts_avg': [], 'pkg_watts_std': [], 'ram_watts_avg': [], 'ram_watts_std':[],
    
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
        'i': [], 'itr': [], 'dvfs': [], 'rate': [], 'policy': [], 'nwindows':[], 'CheckpointInterval': [], 'CheckpointMode': [],
        'pkg_watts_avg': [], 'pkg_watts_std': [], 'ram_watts_avg': [], 'ram_watts_std':[],
        
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

def parseFile(loc, rate, itr, dvfs, policy, i, window, timems, windowlength, cpinterval, cpmode):
    file=f"{loc}/summary.csv"

    df_dict['i'].append(i)
    df_dict['itr'].append(itr)
    df_dict['nwindows'].append(window)
    df_dict['CheckpointInterval'].append(cpinterval)
    df_dict['CheckpointMode'].append(cpmode)
    
    if '0x'+str(dvfs) in dvfs_dict:
        df_dict['dvfs'].append(dvfs_dict['0x'+str(dvfs)])
    else:
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
    print(jfile)
    with open(jfile) as file:
        lines = [line.rstrip() for line in file]
        # extract values from 40%-80% of total time to account for warmup time and capture region of compute
        time_in_secs = timems/1000
        stime = int(time_in_secs * 0.4)
        etime = int(time_in_secs * 0.8)
        split_lines = [line.split() for line in lines]
        pkg_vals = [float(val[0]) for val in split_lines]
        ram_vals = [float(val[1]) for val in split_lines]        
        # get the average Power within this timeslot
        df_dict['pkg_watts_avg'].append(float(round(np.mean(pkg_vals[stime:etime]), 2)))
        df_dict['pkg_watts_std'].append(float(round(np.std(pkg_vals[stime:etime]), 2)))
        
        df_dict['ram_watts_avg'].append(float(round(np.mean(ram_vals[stime:etime]), 2)))
        df_dict['ram_watts_std'].append(float(round(np.std(ram_vals[stime:etime]), 2)))
                
def parse(loc1, name, ratetype, checkpointinginterval, checkpointingmode, rocksdbstatebackendenabled):
    nrepeat = 1
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

        #/users/hand32/dataset/micro/query5/different_checkpoint/rocksdb/windowlength20/data/query5_cores16_frate18000_300000_fratetype_static_fbuff-1_itr750_ondemanddvfs1100_source1_window12_sink16_windowlength60_cpint5000_cpmode_exactly_once_cpbckend_rocksdb_repeat0
        
        #query5_cores16_frate6000_300000_fratetype_static_fbuff-1_itr1_ondemanddvfs1_source1_window8_sink16_windowlength20_cpint5000_cpmode_atleast_once_cpbckend_rocksdb_repeat0
        cpinterval=-1
        cpmode="null"
        if checkpointinginterval:
            loc_i = f"{loc}_cpint{checkpointinginterval}"
            combined_file_name = f"{combined_file_name}_{checkpointinginterval}"
            cpinterval = int(checkpointinginterval)
        if checkpointingmode:
            loc_i = f"{loc_i}_cpmode_{checkpointingmode}"
            combined_file_name = f"{combined_file_name}_{checkpointingmode}"
            cpmode = str(checkpointingmode)
        if rocksdbstatebackendenabled:
            loc_i = f"{loc_i}_cpbckend_rocksdb"
            combined_file_name = f"{combined_file_name}_rocksdb"
            
        for i in range(nrepeat):
            loc_i = f"{loc_i}_repeat{i}"
            #print(f"[DEBUG] location: {loc_i}")
            if not path.exists(loc_i+ "/summary.csv"):
                break
            print(loc_i)
            parseFile(loc_i, rate, itr, dvfs, policy, i, window, timems, windowlength, cpinterval, cpmode)

    # print(df_dict)
    dd1 = pd.DataFrame(df_dict)
    print(len(dd1.index))    
    dd1.to_csv(f"{loc1}/combined.csv", mode='a')

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

