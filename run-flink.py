import math
import random
import subprocess
from subprocess import Popen, PIPE, call
import time
from datetime import datetime
import sys
import os
import getopt
import numpy as np
import itertools
import argparse
import shutil
from glob import glob

MASTER = "192.168.1.9"
CSERVER = "192.168.1.11"
CSERVER2 = "192.168.1.9"
ITR = 1
DCA = 0
RAPL = 135
DVFS = '0xffff'
VERBOSE = 0
NREPEAT = 0



def runLocalCommandOut(com):
    #print(com)
    p1 = Popen(list(filter(None, com.strip().split(' '))), stdout=PIPE)
    p1.communicate()
    #print("\t"+com, "->\n", p1.communicate()[0].strip())
    
def runRemoteCommandOut(com):
    #print(com)
    p1 = Popen(["ssh", MASTER, com], stdout=PIPE)
    p1.communicate()
    #print("\tssh "+MASTER, com, "->\n", p1.communicate()[0].strip())

def runLocalCommand(com):
    #print(com)
    p1 = Popen(list(filter(None, com.strip().split(' '))), stdout=PIPE)
    
def runRemoteCommand(com):
    #print(com)
    p1 = Popen(["ssh", MASTER, com])

def runRemoteCommands(com, server):
    #print(com)
    p1 = Popen(["ssh", server, com])

def runRemoteCommandGet(com, server):
    #print(com)
    p1 = Popen(["ssh", server, com], stdout=PIPE)
    return p1.communicate()[0].strip()

def setITR(v):
    global ITR
    p1 = Popen(["ssh", CSERVER2, "/app/ethtool-4.5/ethtool -C eth0 rx-usecs", v], stdout=PIPE, stderr=PIPE)
    p1.communicate()    
    time.sleep(0.5)
    ITR = int(v)

def setRAPL(v):
    global RAPL
    
    if ITR != 1:
        p1 = Popen(["ssh", CSERVER2, "/app/uarch-configure/rapl-read/rapl-power-mod", v], stdout=PIPE, stderr=PIPE)
        p1.communicate()
        time.sleep(0.5)
    RAPL = int(v)

def setDVFS(v):
    global DVFS

    if ITR != 1:
        p1 = Popen(["ssh", CSERVER2, "wrmsr -a 0x199", v], stdout=PIPE, stderr=PIPE)
        p1.communicate()
        time.sleep(0.5)
    DVFS = v

def cleanLogs():
    runRemoteCommands("rm -rf /home/like/eestreaming/dependencies/flink/log/*", CSERVER2)
    for i in range(0, 16):                    
        runRemoteCommandGet("cat /proc/ixgbe_stats/core/"+str(i)+" &> /dev/null", "192.168.1.9")
        if VERBOSE:
            print("cleanLogs", i)
    

def printLogs():
    for i in range(0, 16):
        runRemoteCommandGet("cat /proc/ixgbe_stats/core/"+str(i)+" &> /app/mcd_dmesg."+str(i), "192.168.1.9")
        if VERBOSE:
            print("printLogs", i)    

def getLogs():
    for i in range(0, 16):
        runLocalCommandOut("scp -r 192.168.1.9:/app/mcd_dmesg."+str(i)+" linux.mcd.dmesg."+str(NREPEAT)+"_"+str(i)+"_"+str(ITR)+"_"+str(DVFS)+"_"+str(RAPL))        
        if VERBOSE:
            print("getLogs", i)

def parseLatency(filename):
    f = open(filename, 'r')
    lines = f.readlines()
    average = 0
    draft = []
    result = []
    for i in range(len(lines)):
        if "[] - %latency%" in lines[i]:
            draft.append(lines[i][lines[i].index("[] - %latency%")+len("[] - %latency%"):])
    for i in range(len(draft)):
        result.append(int(draft[i][:draft[i].index("%")]))
    if len(result) == 0:
        average = -1.0
    else:
        average = np.round(sum(result)/len(result))
    return average

def getFlinkLog():
    runLocalCommand("scp -r 192.168.1.9:/home/like/eestreaming/dependencies/flink/log/flink-root-taskexecutor-0-neu-5-9.log ../dependencies/flink/log/")
    time.sleep(1)

    # The sink may change

    files = glob("../dependencies/flink/log/flink-root-taskexecutor-1*.log")
    if len(files) == 0:
    #file did not find
        sys.exit()
    latency_result = parseLatency(files[0])
    file_latency = open("flink-latency."+str(NREPEAT)+"_"+str(ITR)+"_"+str(DVFS)+"_"+str(RAPL), "w+")
    file_latency.write(str(latency_result))
    file_latency.close()
    

def runFlink():
    ## dump logs to /dev/null first
    cleanLogs()

    ## run workload
    subprocess.call(['sh', './run-flink-workload.sh'])
    
    
    printLogs()
    getLogs()
    getFlinkLog()

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--rapl", help="Rapl power limit [35, 135]")
    parser.add_argument("--itr", help="Static interrupt delay [10, 500]")
    parser.add_argument("--dvfs", help="DVFS value [0xc00 - 0x1d00]")
    parser.add_argument("--nrepeat", help="repeat value")
    parser.add_argument("--verbose", help="Print mcd raw stats")
    
    args = parser.parse_args()

    if args.itr:
        #print("ITR = ", args.itr)
        setITR(args.itr)

    if args.dvfs:
        setDVFS(args.dvfs)
        
    if args.rapl:
        #print("RAPL = ", args.rapl)
        setRAPL(args.rapl)
    
    
    if args.nrepeat:
        NREPEAT = args.nrepeat
        
        
    if args.verbose:
        VERBOSE = 1

    runFlink()


