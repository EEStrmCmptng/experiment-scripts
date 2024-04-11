import pandas as pd
import numpy as np
import argparse
import itertools

import re
import os
from os import path
import sys
import time

LINUX_COLS = ['i', 'rx_desc', 'rx_bytes', 'tx_desc', 'tx_bytes', 'instructions', 'cycles', 'ref_cycles', 'llc_miss', 'c0', 'c1', 'c1e', 'c3', 'c6', 'c7', 'joules', 'timestamp']

TIME_CONVERSION_khz = 1./(2599999*1000)
JOULE_CONVERSION = 0.00001526

# Linux dvfs policies: https://www.kernel.org/doc/Documentation/cpu-freq/governors.txt
policies = ["ondemand", "conservative", "performance", "schedutil", "powersave"]

# total time to run for, in ms
times = [300000, 600000]

# diff flink rates
rates = [100000, 200000, 300000, 400000]

# number of mappers
mappers = [4, 8, 12, 16]

# not exploring different combo for these yet
itrs = [1]
dvfss = [1]
sources = [16] # num of sources
sinks = [16] # num of sinks
ncores = [16] # num of physical cores to use

df_dict = {
    'i': [], 'itr': [], 'dvfs': [], 'rate': [], 'policy': [], 'nmappers':[],

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

    'MappernumRecordsInPerSecond_avg': [],
    'MappernumRecordsInPerSecond_std': [], 'MappernumRecordsOutPerSecond_avg': [],
    'MappernumRecordsOutPerSecond_std': [], 'MapperbusyTimeMsPerSecond_avg': [],
    'MapperbusyTimeMsPerSecond_std': [], 'MapperbackPressuredTimeMsPerSecond_avg': [],
    'MapperbackPressuredTimeMsPerSecond_std': [],
    'MapperbusyTime_%': [], 'MapperbackPressuredTime_%': []
}

df_dict2 = {
    'i': [], 'itr': [], 'dvfs': [], 'rate': [], 'policy': [], 'joules': [], 'joulesMax': [], 'joulesMin': [], 'nmappers': [],
    'rxDescIntLog': [], 'rxBytesIntLog': [], 'txDescIntLog': [], 'txBytesIntLog': [],
    'instructions': [], 'cycles': [],
    'ref_cycles': [], 'llc_miss': [], 
    'num_interrupts': [], 'time': []
}

df_dict3 = {
    'i': [], 'itr': [], 'dvfs': [], 'rate': [], 'policy': [], 'nmappers': []
}

print("*****************************************************************")

def resetdf():
    global df_dict
    global df_dict2
    
    for k in df_dict.keys():
        df_dict[k] = []
    for k in df_dict2.keys():
        df_dict2[k] = []
    for k in df_dict3.keys():
        df_dict3[k] = []

def parseFile(loc, rate, itr, dvfs, policy, i, mapper, timems):
    file=f"{loc}/summary.csv"

    df_dict['i'].append(i)
    df_dict['itr'].append(itr)
    df_dict['nmappers'].append(mapper)

    df_dict['dvfs'].append(dvfs)

    df_dict['policy'].append(policy)
    df_dict['rate'].append(rate)

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

    dff = df[df['name'].str.contains('Mapper')]
    dff.columns = 'Mapper' + dff.columns
    cols = dff.columns
    for col in cols[2:]:
        df_dict[col].append(dff.mean(numeric_only=True)[col])

def parseIntLog(loc, rate, itr, dvfs, policy, i, mapper, timems, cores):
    tins = 0
    tcyc = 0
    trefcyc = 0
    tllcm = 0
    tc3 = 0
    tc6 = 0
    tc7 = 0
    tc1 = 0
    tc1e = 0
    trx_desc = 0
    trx_bytes = 0
    ttx_desc = 0
    ttx_bytes = 0
    tjoules = 0.0
    minjoules = 9999999.0
    maxjoules = 0.0
    tnum_interrupts = 0
    ttimestamp = 0
    # extract values from 30%-80% of total time to account for warmup time and capture region of compute
    time_in_secs = timems/1000
    stime = int(time_in_secs * 0.3)
    etime = int(time_in_secs * 0.8)

            
    for core in range(0, cores):
        fname=f"{loc}/ITRlogs/linux.flink.dmesg._{core}_{i}"
        df = pd.read_csv(fname, sep=' ', names=LINUX_COLS)
        df_non0j = df[(df['joules']>0) & (df['instructions'] > 0) & (df['cycles'] > 0) & (df['ref_cycles'] > 0) & (df['llc_miss'] > 0)].copy()
        df_non0j['timestamp'] = df_non0j['timestamp'] - df_non0j['timestamp'].min()
        df_non0j['timestamp'] = df_non0j['timestamp'] * TIME_CONVERSION_khz

        df_non0j['ref_cycles'] = df_non0j['ref_cycles'] * TIME_CONVERSION_khz
        df_non0j['joules'] = df_non0j['joules'] * JOULE_CONVERSION
        
        ## only consider data between 40%-80% of total run
        df_non0j = df_non0j[(df_non0j['timestamp'] > stime) & (df_non0j['timestamp'] < etime)]

        tmp = df_non0j[['instructions', 'cycles', 'ref_cycles', 'llc_miss', 'joules', 'c0', 'c1', 'c1e', 'c3', 'c6', 'c7', 'timestamp']].diff()
        tmp.columns = [f'{c}_diff' for c in tmp.columns]
        df_non0j = pd.concat([df_non0j, tmp], axis=1)
        df_non0j.dropna(inplace=True)
        df.dropna(inplace=True)
        df_non0j = df_non0j[df_non0j['joules_diff'] > 0]
        
        cjoules = df_non0j['joules_diff'].sum()
        #print(f"core {core} : {round(cjoules, 2)} Joules")
        maxjoules = max(maxjoules, cjoules)
        minjoules = min(minjoules, cjoules)

        for metric in ['rx_desc', 'rx_bytes', 'tx_desc', 'tx_bytes', 'instructions_diff', 'cycles_diff', 'ref_cycles_diff', 'llc_miss_diff']:
            tmpv = df_non0j[metric].sum()
            if f"core{core}_{metric}" in df_dict2.keys():                
                df_dict2[f"core{core}_{metric}"].append(tmpv)
            else:
                df_dict2[f"core{core}_{metric}"] = [tmpv]
    
        if f"core{core}_num_interrupts" in df_dict2.keys():
            df_dict2[f"core{core}_num_interrupts"].append(df.shape[0])
        else:
            df_dict2.update({f"core{core}_num_interrupts" : [df.shape[0]]})
                
        #print(f"core{core}_num_interrupts:", df_dict2[f"core{core}_num_interrupts"])
        
        trx_desc += df_non0j['rx_desc'].sum()
        trx_bytes += df_non0j['rx_bytes'].sum()
        ttx_desc += df_non0j['tx_desc'].sum()
        ttx_bytes += df_non0j['tx_bytes'].sum()

        tins += df_non0j['instructions_diff'].sum()
        tcyc += df_non0j['cycles_diff'].sum()
        trefcyc += df_non0j['ref_cycles_diff'].sum()

        tllcm += df_non0j['llc_miss_diff'].sum()
        tc1 += df_non0j['c1_diff'].sum()
        tc1e += df_non0j['c1e_diff'].sum()
        tc3 += df_non0j['c3_diff'].sum()
        tc6 += df_non0j['c6_diff'].sum()
        tc7 += df_non0j['c7_diff'].sum()
        tnum_interrupts += df.shape[0] 
        ttimestamp += df_non0j['timestamp_diff'].sum()
        tjoules = minjoules+maxjoules
    #print(df_dict2)
    #print("tnum_interrupts", tnum_interrupts)
    
    df_dict2['i'].append(i)
    df_dict2['itr'].append(itr)
    df_dict2['nmappers'].append(mapper)
    df_dict2['dvfs'].append(dvfs)
    df_dict2['policy'].append(policy)
    df_dict2['rate'].append(rate)
    df_dict2['joules'].append(round(tjoules, 2))
    df_dict2['joulesMax'].append(round(maxjoules, 2))
    df_dict2['joulesMin'].append(round(minjoules, 2))
    df_dict2['rxDescIntLog'].append(trx_desc)
    df_dict2['rxBytesIntLog'].append(trx_bytes)
    df_dict2['txDescIntLog'].append(ttx_desc)
    df_dict2['txBytesIntLog'].append(ttx_bytes)
    df_dict2['instructions'].append(tins)
    df_dict2['cycles'].append(tcyc)
    df_dict2['ref_cycles'].append(trefcyc)
    df_dict2['llc_miss'].append(int(tllcm))
    df_dict2['num_interrupts'].append(tnum_interrupts)
    df_dict2['time'].append(ttimestamp)
    print(f"Package: {round(tjoules, 2)} Joules")

def parseCstate(loc, rate, itr, dvfs, policy, i, mapper, timems, cores):
    fname=f"{loc}/flink_cpuidle_START480.csv"
    fnames=f"{loc}/flink_cpuidle_START180.csv"
    colnames = []
    for c in range(0, cores):
        for s in range(0, 5):
            for metric in ["above", "below", "power", "time", "usage", "rejected"]:
                colnames.append(f"core{c}_state{s}_{metric}")

    ## data for between 30%-80% of total run
    dfEND = pd.read_csv(fname, sep=',', names=colnames, index_col=False)
    dfSTART = pd.read_csv(fnames, sep=',', names=colnames, index_col=False)
    df = dfEND-dfSTART
    
    df_dict3['i'].append(i)
    df_dict3['itr'].append(itr)
    df_dict3['nmappers'].append(mapper)
    df_dict3['dvfs'].append(dvfs)
    df_dict3['policy'].append(policy)
    df_dict3['rate'].append(rate)
    #print(df_dict3)
    #print(df.to_dict("list"))

    if len(df_dict3.keys()) < 10:
        df_dict3.update(df.to_dict("list"))
    else:
        d = df.to_dict("list")
        for k, v in d.items():
            df_dict3[k].append(v[0])
    
def parse(loc1, name):
    nrepeat = 10
    resetdf()

    # Generate combinations of items from the
    combinations = list(itertools.product(policies, rates, times, itrs, dvfss, mappers, ncores, sources, sinks))

    # Print the combinations
    for combo in combinations:
        policy, rate, timems, itr, dvfs, mapper, cores, source, sink = combo

        for i in range(nrepeat):
            loc=f"{loc1}/{name}_cores{cores}_frate{rate}_{timems}_fbuff-1_itr{itr}_{policy}dvfs{dvfs}_source{source}_mapper{mapper}_sink{sink}_repeat{i}/"
            if not path.exists(loc):
                break
            print(loc)
            parseFile(loc, rate, itr, dvfs, policy, i, mapper, timems)
            parseIntLog(loc, rate, itr, dvfs, policy, i, mapper, timems, cores)
            parseCstate(loc, rate, itr, dvfs, policy, i, mapper, timems, cores)
            
    #print(df_dict)
    dd1 = pd.DataFrame(df_dict)
    print(len(dd1.index))

    #print(df_dict2)
    dd2 = pd.DataFrame(df_dict2)
    print(len(dd2.index))

    #print(df_dict3)
    dd3 = pd.DataFrame(df_dict3)
    print(len(dd3.index))
    
    dd4 = dd1.merge(dd2, on=['i', 'itr', 'dvfs', 'rate', 'policy', 'nmappers'])        
    dd5 = dd4.merge(dd3, on=['i', 'itr', 'dvfs', 'rate', 'policy', 'nmappers']) 
    dd5.to_csv(f"{loc1}/combined.csv", mode='w')

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--log", help="log location", required=True)
    parser.add_argument("--name", help="ie query1", default="query1", required=True)
    args = parser.parse_args()

    loc=args.log
    name=args.name

    try:
        parse(loc, name)
    except Exception as error:
        print(error)
