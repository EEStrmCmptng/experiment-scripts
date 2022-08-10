import re
import os
from os import path
import sys
import time
import numpy as np
import pandas as pd


if len(sys.argv) != 2:
    exit()
loc = sys.argv[1]

# This specifies for where to write to, the location of the csv file
file_path = '/mnt/eestreaming/datasets/current.csv'
sys.stdout = open(file_path, "a")

'''
dvfs = ["0xd00",
        "0xf00",
        "0x1100",
        "0x1200",
        "0x1300",
        "0x1400",
        "0x1500",
        "0x1700",
        "0x1800",
        "0x1900",
        "0x1a00",
        "0x1b00",
        "0x1c00",
        "0x1d00",
        "0xffff"]

itrs = ["1", "2", "4", "8", "10", "20", "30", "40", "50", "100", "200", "300", "350", "400"]
'''

dvfs=["0x0c00","0x1d00"]
itrs=["50", "100"]

rapls = ["135"]
iters = 3
LINUX_COLS = ['i', 'rx_desc', 'rx_bytes', 'tx_desc', 'tx_bytes', 'instructions', 'cycles', 'ref_cycles', 'llc_miss', 'c0', 'c1', 'c1e', 'c3', 'c6', 'c7', 'joules', 'timestamp']

TIME_CONVERSION_khz = 1./(2899999*1000)
JOULE_CONVERSION = 0.00001526

slatency = 0
mlatency = 0
START_RDTSC = 0
END_RDTSC = 0
tdiff = 0
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

def parseFlink(i, itr, d, rapl):
    global slatency
    global mlatency
    
    def reject_outliers(data, m=2):
        return data[abs(data - np.mean(data)) < m * np.std(data)]

    f1 = f'{loc}/flink-latency.'+str(i)+'_'+itr+'_'+d+'_'+rapl
    f1out = open(f1, 'r')
    context = f1out.read()[1:-1]
    if len(context) == 0:
        mlantecy  = -1
        return
    context = context.split(", ")
    vals = np.array([int(c) for c in context])
    vals = reject_outliers(vals) 
    mlatency = np.around(np.mean(vals),2)
    f1out.close()
    

    #f2 = f'{loc}/flink-latency-slave.'+str(i)+'_'+itr+'_'+d+'_'+rapl
    #f2out = open(f2, 'r')
    #slatency = float(f2out.read())
    #f2out.close()


def parseRdtsc(i, itr, d, rapl):
    global START_RDTSC
    global END_RDTSC
    global tdiff

    f = f'{loc}/linux.mcd.rdtsc.'+str(i)+'_'+itr+'_'+d+'_'+rapl
    frtdsc = open(f, 'r')
    START_RDTSC = 0
    END_RDTSC = 0
    for line in frtdsc:
        tmp = line.strip().split(' ')
        if int(tmp[2]) > START_RDTSC:
            START_RDTSC = int(tmp[2])

        if END_RDTSC == 0:
            END_RDTSC = int(tmp[3])
        elif END_RDTSC < int(tmp[3]):
            END_RDTSC = int(tmp[3])
    frtdsc.close()
    tdiff = round(float((END_RDTSC - START_RDTSC) * TIME_CONVERSION_khz), 2)

def exists(i, itr, d, rapl):
    outf = f'{loc}/linux.mcd.out.'+str(i)+'_'+itr+'_'+d+'_'+rapl
    if not path.exists(outf):
        #print(outf)
        return False

    rf = f'{loc}/linux.mcd.rdtsc.'+str(i)+'_'+itr+'_'+d+'_'+rapl
    if not path.exists(rf):
        #print(rf)
        return False

    for core in range(0, 16):
        fname = f'{loc}/linux.mcd.dmesg.'+str(i)+'_'+str(core)+'_'+itr+'_'+d+'_'+rapl
        if not path.exists(fname):
            #print(fname)
            return False
    return True

for d in dvfs:
    for itr in itrs:
            for rapl in rapls:
                for i in range(0, iters):
                        parseFlink(i, itr, d, rapl)
                        START_RDTSC = 0
                        END_RDTSC = 0
                        tdiff = 0
                        tins = 0
                        tcyc = 0
                        trefcyc = 0
                        tllcm = 0
                        tc3 = 0
                        tc6 = 0
                        tc7 = 0
                        tjoules = 0
                        tc1 = 0
                        tc1e = 0
                        num_interrupts = 0
                        trx_desc = 0
                        trx_bytes = 0
                        ttx_desc = 0
                        ttx_bytes = 0
                        tnum_interrupts = 0
                        for core in range(0, 16):
                            fname = f'{loc}/linux.mcd.dmesg.'+str(i)+'_'+str(core)+'_'+itr+'_'+d+'_'+rapl
                            df = pd.read_csv(fname, sep=' ', names=LINUX_COLS)
                            df_non0j = df[(df['joules']>0) & (df['instructions'] > 0) & (df['ref_cycles'] > 0)].copy()
                            df_non0j['timestamp'] = df_non0j['timestamp'] - df_non0j['timestamp'].min()
                            df_non0j['timestamp'] = df_non0j['timestamp'] * TIME_CONVERSION_khz
                            df_non0j['joules'] = df_non0j['joules'] * JOULE_CONVERSION

                            tmp = df_non0j[['instructions', 'ref_cycles', 'joules', 'c1', 'c1e', 'c3', 'c6', 'c7']].diff()
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
                            #tcyc += df_non0j['cycles_diff'].sum()
                            trefcyc += df_non0j['ref_cycles_diff'].sum()
                            #tllcm += df_non0j['llc_miss_diff'].sum()
                            #tc1 += df_non0j['c1_diff'].sum()
                            #tc1e += df_non0j['c1e_diff'].sum()
                            #tc3 += df_non0j['c3_diff'].sum()
                            #tc6 += df_non0j['c6_diff'].sum()
                            #tc7 += df_non0j['c7_diff'].sum()
                            tnum_interrupts += df.shape[0]

                            #print(f"linux_core_tuned {i} {core} {itr} {d} {rapl} {read_5th} {read_10th} {read_50th} {read_90th} {read_95th} {read_99th} {mqps} {cqps} {tdiff} {round(cjoules, 2)} {df['rx_desc'].sum()} {df['rx_bytes'].sum()} {df['tx_desc'].sum()} {df['tx_bytes'].sum()} {int(df_non0j['instructions_diff'].sum())} {int(df_non0j['ref_cycles_diff'].sum())} {df.shape[0]}")
                        print(f"flink {i} {itr} {d} {rapl} {mlatency} {np.around(tjoules, 2)} {trx_desc} {trx_bytes} {ttx_desc} {ttx_bytes} {tins} {trefcyc} {tnum_interrupts}")

sys.stdout.close()
