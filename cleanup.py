import re
import os
from os import path, system
import sys
import time
import numpy as np
import pandas as pd
from runexperiment import *

loc = '/mnt/eestreaming-refactor/experiment-scripts'
bootstrap='192.168.1.153'   
bootstrap_='192_168_1_153'
victim='192.168.1.11'       
victim_='192_168_1_11'

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


def exists(i, itr, d, rapl, core):
    '''
    outf = f'{loc}/linux.mcd.out.'+str(i)+'_'+itr+'_'+d+'_'+rapl
    if not path.exists(outf):
        #print(outf)
        return False
'''
    rf = f'{loc}/logs/'+KWD+'ITRlogs/linux.flink.rdtsc.'+str(i)+'_'+itr+'_'+d+'_'+rapl
    if not path.exists(rf):
        #print(rf)
        return False

    for core in range(0, 16):
        fname = f'{loc}/logs/'+KWD+'ITRlogs/linux.flink.dmesg.'+str(i)+'_'+str(core)+'_'+itr+'_'+d+'_'+rapl
        if not path.exists(fname):
            #print(fname)
            return False
    return True




def cleanup(NREPEAT, NCORES, ITR, RAPL, DVFS, FLINKRATE, BUFFTIMEOUT):
    KWD=FLINKRATE+"_"+BUFFTIMEOUT+'_'+str(ITR)+"_"+str(DVFS)+'_'+str(RAPL)+'_'+str(NREPEAT)
    #file_path = loc+'/logs/clean/'+str(FLINKRATE)+'_'+str(BUFFTIMEOUT)+'_'+str(ITR)+'_'+str(DVFS)+'.csv'
    #sys.stdout = open(file_path, "a")
    LINUX_COLS = ['i', 'rx_desc', 'rx_bytes', 'tx_desc', 'tx_bytes', 'instructions', 'cycles', 'ref_cycles', 'llc_miss', 'c0', 'c1', 'c1e', 'c3', 'c6', 'c7', 'joules', 'timestamp']
    '''
    system("$datadir='/mnt/eestreaming-refactor/experiment-scripts/logs/'")
    #system("sudo bpftrace -e 'BEGIN { printf("%u", *kaddr(\"tsc_khz\")); exit(); }' > ${datadir}/tsc.txt")
    system("cat /sys/devices/system/cpu/cpu0/cpufreq/cpuinfo_max_freq > $datadir/max_freq.txt")
    system("cat /proc/cpuinfo > $datadir/cpuinfo.txt")
    system("ifconfig > $datadir/ifconfig.txt")
    system("cp /proc/cmdline $datadir/cmdline.txt")
    system("sudo cp -r /sys/devices/system/cpu $datadir/sys-devices-system-cpu 2> /dev/null")
    system("sudo tar -czf $datadir/sys-devices-system-cpu.tgz $datadir/sys-devices-system-cpu")
    system("sudo rm -rf $datadir/sys-devices-system-cpu")

    file_in = open(loc+'/logs/max_freq.txt', 'r')
    for y in file_in.read():
         max_freq = float(y)
    '''
    TIME_CONVERSION_khz = 1./(2899999*1000)
    JOULE_CONVERSION = 0.00001526 ##WHERE ARE WE GETTING THIS FROM

    latency = 0
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


    for i in range(0, NREPEAT):
        fnames=os.listdir(loc+'/logs/'+KWD+'/Flinklogs/'+bootstrap_+'/')
        latency_list={}
        latency_avg={}
        final_latency={}
        for ff in fnames:
            latency_list[ff] = parseFlinkLatency(loc+'/logs/'+KWD+'/Flinklogs/'+bootstrap_+'/'+ff)
            if latency_list[ff] != []:
                latency_avg[ff]=np.average(latency_list[ff]) 
                final_latency[i]=latency_avg[ff]
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


        for core in range(0, NCORES):
            fname = f'{loc}/logs/'+KWD+'/ITRlogs/linux.flink.dmesg.'+'_'+str(core)
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
            print(f"flink {i} {ITR} {DVFS} {RAPL} {latency} {np.around(tjoules, 2)} {trx_desc} {trx_bytes} {ttx_desc} {ttx_bytes} {tins} {trefcyc} {tnum_interrupts} {final_latency[i]}",file=sys.stdout)


if __name__ == '__main__':
    # python3 cleanup.py --rapl 50 --itr 10 --dvfs 0xfff --nrepeat 1 --flinkrate 100_100000 --cores 16
    parser = argparse.ArgumentParser()
    parser.add_argument("--cores", help="num of cpu cores")
    parser.add_argument("--rapl", help="Rapl power limit [35, 135]")
    parser.add_argument("--itr", help="Static interrupt delay [2, 1024]")
    parser.add_argument("--dvfs", help="Static DVFS value [0xc00 - 0x1d00]")
    parser.add_argument("--nrepeat", help="repeat value")
    parser.add_argument("--verbose", help="Print mcd raw stats")
    parser.add_argument("--flinkrate", help="input rate of Flink query")
    parser.add_argument("--bufftimeout", help="buffer-Timeout in Flink")
    parser.add_argument("--runcmd", help="runexp/stopflink/plot")
    args = parser.parse_args()
 
    if args.itr:
        #print("ITR = ", args.itr)
        ITR=int(args.itr)

    if args.dvfs:
        #print("DVFS = ", args.dvfs)
        DVFS=args.dvfs

    if args.rapl:
        #print("RAPL = ", args.rapl)
        RAPL=int(args.rapl)

    if args.nrepeat:
        #print("NREPEAT = ", args.nrepeat)
        NREPEAT = int(args.nrepeat)

    if args.cores:
        #print("NCORES = ", args.cores)
        NCORES = int(args.cores)

    if args.flinkrate:
        #print("flinkrate = ", args.flinkrate)
        FLINKRATE = args.flinkrate

    if args.bufftimeout:
        #print("BUFFTIMEOUT = ", args.bufftimeout)
        BUFFTIMEOUT = args.bufftimeout

    cleanup(NREPEAT, NCORES, ITR, RAPL, DVFS, FLINKRATE, BUFFTIMEOUT)

    sys.stdout.close()

