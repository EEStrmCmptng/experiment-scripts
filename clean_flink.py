import re
import os
from os import path
import sys
import time
import numpy as np
import pandas as pd

LINUX_COLS = ['i', 'rx_desc', 'rx_bytes', 'tx_desc', 'tx_bytes', 'instructions', 'cycles', 'ref_cycles', 'llc_miss', 'c0', 'c1', 'c1e', 'c3', 'c6', 'c7', 'joules', 'timestamp']

#2600000
#TIME_CONVERSION_khz = 1./(2899999*1000
TIME_CONVERSION_khz = 1./(2600000*1000)
JOULE_CONVERSION = 0.00001526

loc = sys.argv[1]
it = sys.argv[2]
mqps = 0
cqps = 0
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
tnum_interrupts = 0
ttimestamp = 0
itr = re.findall(r'itr\s*(\d+)', loc)
dvfs = re.findall(r'dvfs\s*(0[xX][0-9a-fA-F]+)', loc)


for core in range(0, 16):
    fname = f'{loc}/ITRlogs/linux.flink.dmesg._'+str(core)+"_"+str(it)
    df = pd.read_csv(fname, sep=' ', names=LINUX_COLS)
    df_non0j = df[(df['joules']>0) & (df['instructions'] > 0) & (df['cycles'] > 0) & (df['ref_cycles'] > 0) & (df['llc_miss'\
] > 0)].copy()
    df_non0j['timestamp'] = df_non0j['timestamp'] - df_non0j['timestamp'].min()
    df_non0j['timestamp'] = df_non0j['timestamp'] * TIME_CONVERSION_khz
    df_non0j['ref_cycles'] = df_non0j['ref_cycles'] * TIME_CONVERSION_khz
    df_non0j['joules'] = df_non0j['joules'] * JOULE_CONVERSION
    df_non0j = df_non0j[(df_non0j['timestamp'] > 60) & (df_non0j['timestamp'] < 240)]
    
    tmp = df_non0j[['instructions', 'cycles', 'ref_cycles', 'llc_miss', 'joules', 'c0', 'c1', 'c1e', 'c3', 'c6', 'c7','timestamp']].diff()
    tmp.columns = [f'{c}_diff' for c in tmp.columns]
    df_non0j = pd.concat([df_non0j, tmp], axis=1)
    df_non0j.dropna(inplace=True)
    df.dropna(inplace=True)
    df_non0j = df_non0j[df_non0j['joules_diff'] > 0]
    
    cjoules = df_non0j['joules_diff'].sum()
    if core == 0 or core == 1:
        tjoules += cjoules
        
    trx_desc += df['rx_desc'].sum()
    trx_bytes += df['rx_bytes'].sum()
    ttx_desc += df['tx_desc'].sum()
    ttx_bytes += df['tx_bytes'].sum()
    
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

busy_frac = trefcyc/ttimestamp
op0_busy = pd.read_csv(loc+'/Flinklogs/Operator_Mapper_0',delimiter=';', header = None, skiprows=6, chunksize=24)
op0_busy_df = pd.concat(op0_busy)
op0_busy_df['busy'] = op0_busy_df.iloc[5].str.extract(r"0\.busyTimeMsPerSecond', 'value': '([\d\.]+)'").astype(float)
#print(op0_busy_df[5].str.extract(r"0\.busyTimeMsPerSecond', 'value': '([\d\.]+)'").dropna().mean())
op0_busy_mean = op0_busy_df['busy'].mean()
print(op0_busy_mean)
op1_busy = pd.read_csv(loc+'/Flinklogs/Operator_Mapper_1',delimiter=';', header = None, skiprows=6, chunksize=24)
op1_busy_df=pd.concat(op1_busy)
#print(op1_busy_df[5].str.extract(r"0\.busyTimeMsPerSecond', 'value': '([\d\.]+)'").dropna().mean())
op1_busy_df['busy'] = op1_busy_df.iloc[5].str.extract(r"1\.busyTimeMsPerSecond', 'value': '([\d\.]+)'").astype(float)
op1_busy_mean = op1_busy_df['busy'].mean()

src_back = pd.read_csv(loc+'/Flinklogs/Operator_Source: Bids Source_0',delimiter=';', header = None, skiprows=6, chunksize=24)
src_back_df=pd.concat(src_back)
#print(src_back_df[6].str.extract(r"0.backPressuredTimeMsPerSecond', 'value': '([\d\.]+)'").dropna().mean())
src_back_df['back'] = src_back_df[6].str.extract(r"0.backPressuredTimeMsPerSecond', 'value': '([\d\.]+)'" ).astype(float)
src_back_mean = src_back_df['back'].max()

snk_busy = pd.read_csv(loc+'/Flinklogs/Operator_Latency Sink_0',delimiter=';', header = None, skiprows=6, chunksize=24)
snk_busy_df=pd.concat(snk_busy)
snk_busy_df['busy'] = snk_busy_df.iloc[5].str.extract(r"0\.busyTimeMsPerSecond', 'value': '([\d\.]+)'").astype(float)
snk_busy_mean = snk_busy_df['busy'].mean()
#print(snk_busy_df[5])

print(f"linux_tuned {itr} {dvfs} {round(tjoules, 2)} {trx_desc} {trx_bytes} {ttx_desc} {ttx_bytes} {tins} {tcyc} {trefcyc} {busy_frac} {tllcm} {tc1} {tc1e} {tc3} {tc6} {tc7} {tnum_interrupts} {ttimestamp} {op0_busy_mean} {op1_busy_mean} {snk_busy_mean} {src_back_mean}")
