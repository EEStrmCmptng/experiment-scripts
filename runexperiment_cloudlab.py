from flink_rest_client import FlinkRestClient
import sys, os, time, json, requests, argparse
import numpy as np
import pandas as pd
import datetime
import traceback
import subprocess
from subprocess import Popen, PIPE, call

dvfs_dict = {
    "0x0c00" : 1.2,
    "0x0d00" : 1.3,
    "0x0e00" : 1.4,
    "0x0f00" : 1.5,
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
    "0xffff" : 3.0,
}

ROOTDIR=os.path.dirname(os.getcwd())
#FLINKROOT=os.path.dirname(os.getcwd())+'/flink-simplified'
FLINKROOT='~/experiment-scripts/flink-simplified'
#print(FLINKROOT)
MAXCORES=16    # num of cores. 16C32T
CPUIDS=[[0,16],[1,17],[2,18],[3,19],[4,20],[5,21],[6,22],[7,23],[8,24],[9,25],[10,26],[11,27],[12,28],[13,29],[14,30],[15,31]]

# the script will run on bootstrap
bootstrap='10.10.1.1'   # jobmanager
victim='10.10.1.3'       # scp logs from victim to bootstrap
#jarpath='./flink-benchmarks/target/Query1-jar-with-dependencies.jar'
jarpath_q1='./flink-benchmarks/target/Query1tsc-jar-with-dependencies.jar'
jarpath_imgproc='./flink-benchmarks/target/Imgproc-jar-with-dependencies.jar'
#jarpath='./flink-benchmarks/target/Query5-jar-with-dependencies.jar'

jmip=bootstrap
jmpt=8081

# Global vars
GITR=1
GDVFS=""
GQUERY=""
GPOLICY="ondemand"
GRERUNFLINK=False
GSOURCE=14
GMAPPER=16
GSINK=16

# global sleep state counter
GPOLL=0
GC1=0
GC1E=0
GC3=0
GC6=0

# global rxtx
GRXP=0
GRXB=0
GTXP=0
GTXB=0
GERXP=0
GERXB=0
GETXP=0
GETXB=0

def stopflink():
    print(os.popen("cp -r ./flink-cfg/* "+FLINKROOT+"/flink-dist/target/flink-1.14.0-bin/flink-1.14.0/conf/").read())
    print("stopping flink...")
    print("cd "+FLINKROOT+"/flink-dist/target/flink-1.14.0-bin/flink-1.14.0/bin/ ; ./stop-cluster.sh")
    print(os.popen("cd "+FLINKROOT+"/flink-dist/target/flink-1.14.0-bin/flink-1.14.0/bin/ ; ./stop-cluster.sh").read())
    #print(os.popen("rm -rf "+FLINKROOT+"/flinkstate/*").read())
    print("stopped flink")


def startflink():
    localip=os.popen("hostname -I").read()
    print(localip)
    iplist=[]
    print("starting flink...")

    for ip in open('./flink-cfg/workers','r').readlines():
        iplist.append(ip.replace("\n",""))
    # for ip in open('./flink-cfg/masters','r').readlines():
    #     iplist.append(ip.replace("\n","").replace(':8081',''))

    print(iplist)
    for ip in iplist:
        print(os.popen("cp ./flink-cfg/flink-conf.yaml ./flink-cfg/flink-conf.yaml"+ip.replace('.','')).read())
        ff=open('./flink-cfg/flink-conf.yaml'+ip.replace('.',''), 'r').read().replace('WORKERIP',ip)
        wf=open('./flink-cfg/flink-conf.yaml'+ip.replace('.',''), 'w').write(ff)

    print(os.popen("cp ./flink-cfg/* "+FLINKROOT+"/flink-dist/target/flink-1.14.0-bin/flink-1.14.0/conf/").read())
    print(os.popen("cp ./flink-cfg/* "+FLINKROOT+"/scripts/").read())

    for ip in iplist:
        print(os.popen('ssh '+ip+' "rm -rf '+FLINKROOT+'/flink-dist/target/flink-1.14.0-bin/flink-1.14.0/log/*"').read())

    for ip in iplist:
        if not (ip in localip):
            print('-----------------------------------------------------')
            print(ip)
            print(os.popen('ssh '+ip+' "rm -rf '+FLINKROOT+'/flink-dist/target"').read())
            print(os.popen('ssh '+ip+' "rm -rf '+FLINKROOT+'/flinkstate/"').read())
            print(os.popen('ssh '+ip+' "mkdir '+FLINKROOT+'/"').read())
            print(os.popen('ssh '+ip+' "mkdir '+FLINKROOT+'/scripts/"').read())
            print(os.popen('ssh '+ip+' "mkdir '+FLINKROOT+'/flinkstate/"').read())
            print(os.popen('ssh '+ip+' "mkdir '+FLINKROOT+'/flink-dist"').read())
            print(os.popen('ssh '+ip+' "mkdir '+FLINKROOT+'/flink-dist/target"').read())
            print(os.popen('scp -r '+FLINKROOT+'/flink-dist/target/flink-1.14.0-bin/ '+ip+':'+FLINKROOT+'/flink-dist/target/').read())

    for ip in iplist:
        print(ip)
        print(os.popen('ssh '+ip+' "cd '+FLINKROOT+'/flink-dist/target/flink-1.14.0-bin/flink-1.14.0/conf ; cp flink-conf.yaml'+ip.replace('.','')+' flink-conf.yaml"').read())
        print(os.popen('ssh '+ip+' "cp '+FLINKROOT+'/flink-dist/target/flink-1.14.0-bin/flink-1.14.0/conf/flink-conf.yaml '+FLINKROOT+'/scripts/flink-conf.yaml"').read())    # customscheduler need to read it

    print('-----------------------------------------------------')
    print(os.popen('cd '+FLINKROOT+'/flink-dist/target/flink-1.14.0-bin/flink-1.14.0/bin ; ./start-cluster.sh').read())
    print("started flink")


def get_task_metrics_details(jobid, taskid, fieldid):
    # http://192.168.1.105:8081/jobs/e81ee095a99bfc431e260d044ff7e03d/vertices/ea632d67b7d595e5b851708ae9ad79d6/metrics?get=4.busyTimeMsPerSecond
    url = "http://"+jmip+":"+str(jmpt)+"/jobs/{}/vertices/{}/metrics?get={}".format(jobid, taskid, fieldid)
    response = requests.get(url)
    response.raise_for_status()
    ans=response.json()#[0]['value']
    return(str(ans))

def runRemoteCommandGet(com, server):
    p1 = Popen(["ssh", server, com], stdout=PIPE)
    return p1.communicate()[0].strip()

def runGetCmd(cmd):
    print('------------------------------------------------------------')
    print(cmd)
    res=os.popen(cmd).read()
    return res
    print('------------------------------------------------------------')
    
def runcmd(cmd):
    print('------------------------------------------------------------')
    print(cmd)
    res=os.popen(cmd).read()
    print(res)
    print('------------------------------------------------------------')


def resetAllCores():
    # turn on all cores
    for _i in range(MAXCORES):
        cpus=CPUIDS[_i]
        for i in cpus:
            runcmd('ssh ' + victim + ' "echo 1 > /sys/devices/system/cpu/cpu'+ str(i) +'/online"')
    time.sleep(10)

def setCores(nc):
    # only keep N cores online on victim
    for _i in range(MAXCORES):
        if(_i>=nc):
            cpus=CPUIDS[_i]
        else:
            cpus=[CPUIDS[_i][1]]
        for i in cpus:
            runcmd('ssh ' + victim + ' "echo 0 > /sys/devices/system/cpu/cpu'+ str(i) +'/online"')
    time.sleep(10)
    catcpustr='for file in /sys/devices/system/cpu/cpu*/online; do echo "$file: $(cat $file)"; done'
    print(" -------------------- setCores on victim --------------------")
    runcmd('ssh ' + victim + " '"+catcpustr+"' ")

# set ITR configurations on victim node
# dynamic ITR = 1
# HOWTO check ITR value: ssh 192.168.1.11 /app/ethtool-4.5/ethtool -c eth0
def setITR(v):
    global GITR
    print(" -------------------- setITR on victim --------------------")
    ieth = runRemoteCommandGet("ifconfig | grep -B1 10.10.1 | grep -o '^\w*'", victim).decode()
    print(f"ssh {victim} ethtool -C {ieth} rx-usecs {v}")
    runcmd(f"ssh {victim} ethtool -C {ieth} rx-usecs {v}")
    time.sleep(1)
    runcmd(f"ssh {victim} ethtool -c {ieth}")
    print("")

# HOWTO check DVFS policy: ssh 192.168.1.11 /app/perf/display_dvfs_governors.sh
def setDVFS(s):
    global GDVFS, GPOLICY

    if GDVFS == "1":
        # existing policies
        runcmd(f"ssh {victim} ~/experiment-scripts/cloudlab_setup/c6220/set_dvfs.sh {GPOLICY}")
    else:
        runcmd(f"ssh {victim} ~/experiment-scripts/cloudlab_setup/c6220/set_dvfs.sh userspace")
        v = "0x10000"+s
        print(" -------------------- setDVFS on victim --------------------")
        runcmd('ssh ' + victim + ' "sudo wrmsr -a 0x199 ' + v + '"')
        time.sleep(0.5)
        print('ssh ' + victim + ' "sudo wrmsr -a 0x199 ' + v + '"')
        # print CPU frequency across all cores
        runcmd('ssh ' + victim + ' "sudo rdmsr -a 0x199"')
        print("")
    
    '''
    if GLOBAL_ITR != 1:
        # dynamic DVFS = userspace
        runcmd('ssh ' + victim + ' "/app/perf/set_dvfs_governor.sh userspace"')
        time.sleep(0.5)
        
        runcmd('ssh ' + victim + ' "wrmsr -a 0x199 ' + v + '"')
        time.sleep(0.5)
        print('ssh ' + victim + ' "wrmsr -a 0x199 ' + v + '"')
    else:
        # dynamic DVFS = ondemand
        runcmd('ssh ' + victim + ' "/app/perf/set_dvfs_governor.sh ondemand"')
        time.sleep(0.5)
        print('ssh ' + victim + ' "/app/perf/set_dvfs_governor.sh ondemand"')
        runcmd('ssh ' + victim + ' "/app/perf/display_dvfs_governors.sh"')
    '''

# get ITR logs from victim node
def cleanITRlogs():
    runGetCmd(f"ssh {victim} cat /proc/ixgbe_stats/core/*")
    print("cleanITRlogs....")
    
def getITRlogs(KWD, cores, itrlogsdir, NREPEAT):
    for i in range(cores):
        gcmd="cat /proc/ixgbe_stats/core/"+str(i)+" &> ~/flink_dmesg."+str(i)+"_"+str(NREPEAT)
        runcmd('ssh ' + victim + ' "' + gcmd + '"')
        gcmd="scp -r "+victim+":~/flink_dmesg."+str(i)+"_"+str(NREPEAT)+" "+itrlogsdir+"linux.flink.dmesg."+"_"+str(i)+"_"+str(NREPEAT)
        runcmd(gcmd)

# get Flink logs 
def getFlinkLog(KWD, rest_client, job_id, flinklogdir, _clock, interval):
    global GPOLL, GC1, GC1E, GC3, GC6, GRXP, GRXB, GTXP, GTXB, GERXP, GERXB, GETXP, GETXB
    
    tmid=[]
    for tm in rest_client.taskmanagers.all():
        tmid.append(tm['id'])

    clock=_clock
    #jstackCount=0
    print("starting...")
    while(clock>0):
        print("clock", clock, "-------------------------------------------------------------")
        if(interval!=-1):
            vertex_ids=rest_client.jobs.get_vertex_ids(job_id)
            for vid in vertex_ids:
                jvurl="http://"+jmip+":"+str(jmpt)+"/jobs/"+job_id+"/vertices/"+vid
                res=requests.get(jvurl).json()
                #print(res)
                vts=str(res['now'])
                vname=res['name']
                vpall=str(res['parallelism'])
                for vtask in res['subtasks']:
                    ttm=vtask['taskmanager-id']
                    tid=str(vtask['subtask'])
                    t_duration=str([{'id':'duration','value':vtask['duration']}])
                    t_rbytes=str([{'id':'read-bytes','value':vtask['metrics']['read-bytes']}])
                    t_wbytes=str([{'id':'write-bytes','value':vtask['metrics']['write-bytes']}])
                    t_rrec=str([{'id':'read-records','value':vtask['metrics']['read-records']}])
                    t_wrec=str([{'id':'write-records','value':vtask['metrics']['write-records']}])
                    t_busytime=get_task_metrics_details(job_id, vid, tid+'.busyTimeMsPerSecond')
                    t_backpressure=get_task_metrics_details(job_id, vid, tid+'.backPressuredTimeMsPerSecond')
                    t_idletime=get_task_metrics_details(job_id, vid, tid+'.idleTimeMsPerSecond')
                    t_opsin=get_task_metrics_details(job_id, vid, tid+'.numRecordsInPerSecond')
                    t_opsout=get_task_metrics_details(job_id, vid, tid+'.numRecordsOutPerSecond')
                    #print(vts, vname, vpall, ttm, tid, t_busytime, t_backpressure, t_idletime, t_opsin, t_opsout)
                    
                    ff=open(flinklogdir+'/Operator_'+vname+'_'+tid, 'a')
                    ff.write(vts +'; '+ vname +'; '+ vpall +'; '+ ttm +'; '+ tid +'; '+ t_busytime +'; '+ t_backpressure +'; '+ t_idletime +'; '+ t_opsin +'; '+ t_opsout+'; '+t_duration+'; '+t_rbytes+'; '+t_wbytes+'; '+t_rrec+'; '+t_wrec+'  \n')

        tPOLL, tC1, tC1E, tC3, tC6, tRXP, tRXB, tTXP, tTXB, tERXP, tERXB, tETXP, tETXB = getStats()
        
        t_poll=str(tPOLL-GPOLL)
        GPOLL = tPOLL
        t_c1=str(tC1-GC1)
        GC1 = tC1
        t_c1e=str(tC1E-GC1E)
        GC1E = tC1E
        t_c3=str(tC3-GC3)
        GC3 = tC3
        t_c6=str(tC6-GC6)
        GC6 = tC6

        t_rxp=str(tRXP-GRXP)
        GRXP = tRXP
        t_rxb=str(tRXB-GRXB)
        GRXB = tRXB
        
        t_txp=str(tTXP-GTXP)
        GTXP = tTXP
        t_txb=str(tTXB-GTXB)
        GTXB = tTXB

        t_erxp=str(tERXP-GERXP)
        GERXP = tERXP
        t_erxb=str(tERXB-GERXB)
        GERXB = tERXB

        t_etxp=str(tETXP-GETXP)
        GETXP = tETXP
        t_etxb=str(tETXB-GETXB)
        GETXB = tETXB

        ff=open(flinklogdir+'/../stats.csv', 'a')
        ff.write(f"{t_poll}, {t_c1}, {t_c1e}, {t_c3}, {t_c6}, {t_rxp}, {t_rxb}, {t_txp}, {t_txb}, {t_erxp}, {t_erxb}, {t_etxp}, {t_etxb}\n")
        ff.close()

        #jstackCount+=interval
        #tPOLL, tC1, tC1E, tC3, tC6, tRXP, tRXB, tTXP, tTXB, tERXP, tERXB, tETXP, tETXB = getStats()
        #ff=open(f"{flinklogdir}/../stats{jstackCount}.csv", "w")
        #ff.write(f"{tPOLL}, {tC1}, {tC1E}, {tC3}, {tC6}, {tRXP}, {tRXB}, {tTXP}, {tTXB}, {tERXP}, {tERXB}, {tETXP}, {tERXB}\n")
        #ff.close()
        time.sleep(interval)
        
        # every min
        #if jstackCount % 60 == 0:
        #    jpid = int(runGetCmd(f"ssh {victim} pgrep -f java"))
        #    runcmd(f"ssh {victim} jstack {jpid} > {flinklogdir}/../jstack{jstackCount}.raw")
            
        clock-=interval

    gcmd="scp -r "+victim+":"+FLINKROOT+"/flink-dist/target/flink-1.14.0-bin/flink-1.14.0/log/* "+flinklogdir+"/"+victim.replace('.','_')+"/"
    runcmd(gcmd)
    gcmd="scp -r "+bootstrap+":"+FLINKROOT+"/flink-dist/target/flink-1.14.0-bin/flink-1.14.0/log/* "+flinklogdir+"/"+bootstrap.replace('.','_')+"/"
    runcmd(gcmd)


def parseFlinkLatency(filename):
    f = open(filename, 'r')
    lines = f.readlines()
    draft = []
    result = []
    for i in range(len(lines)):
        if "[] - %latency%" in lines[i]:
            draft.append(lines[i][lines[i].index("[] - %latency%")+len("[] - %latency%"):])
    for i in range(len(draft)):
        result.append(int(draft[i][:draft[i].index("%")]))
    f.close()
    return result

def parseFlinkMetrics(flinklogdir):
    fnames=os.listdir(flinklogdir)
    print("--------------------------------------------------------------------------------------")
    print("parseFlinkMetrics on : "+flinklogdir)
    explist=[]
    for fn in fnames:
        #if('Operator_' in fn):
        if(os.path.isfile(flinklogdir+'/'+fn)):
            print("------------------------------------------------------------------------------------------")
            kwlist={'numRecordsInPerSecond':[], 'numRecordsOutPerSecond':[], 'busyTimeMsPerSecond':[], 'backPressuredTimeMsPerSecond':[]}
            ff=open(flinklogdir+'/'+fn, 'r').readlines()
            fcnt=0
            for _ll, _lc in enumerate(ff):
                for lc in _lc.split('; '):
                    for kw in kwlist.keys():
                        if(kw in lc):
                            ldict=eval(lc.replace('[','').replace(']',''))
                            kwlist[kw].append(float(ldict['value']))
                            fcnt+=1
            print(fn,fcnt)
            exp=dict()
            exp['name']=fn
            for kw in kwlist.keys():
                exp[kw+'_avg']=np.average(np.nan_to_num(np.array(kwlist[kw])))
                #print(kw, kwlist[kw])
            explist.append(exp)
    expdf=pd.DataFrame(explist).fillna(0)
    # expdf['true_input_rate']=expdf['numRecordsInPerSecond_avg']/(expdf['busyTimeMsPerSecond_avg']/1000)
    # expdf=expdf.sort_values(by = ['numRecordsOutPerSecond_avg', 'latency_avg', 'latency_max'], ascending = [True, True, True])
    print("-------------------------------------------------------------------------------------")
    print(expdf)


def parseFlinkMetricsMod(flinklogdir, loc="", ignore_mins=5):
    fnames=os.listdir(flinklogdir)
    ignore_param = int((ignore_mins*60)/10);
    print("--------------------------------------------------------------------------------------")
    print(f"parseFlinkMetricsMod on : {flinklogdir}, Ignore data from first {ignore_mins} mins")    
    explist=[]
    for fn in fnames:
        #if('Operator_' in fn):
        if(os.path.isfile(flinklogdir+'/'+fn)):
            print("------------------------------------------------------------------------------------------")
            kwlist={'numRecordsInPerSecond':[], 'numRecordsOutPerSecond':[], 'busyTimeMsPerSecond':[], 'backPressuredTimeMsPerSecond':[]}
            ff=open(flinklogdir+'/'+fn, 'r').readlines()
            fcnt=0
            for _ll, _lc in enumerate(ff):
                for lc in _lc.split('; '):
                    for kw in kwlist.keys():
                        if(kw in lc):
                            ldict=eval(lc.replace('[','').replace(']',''))
                            kwlist[kw].append(float(ldict['value']))
                            fcnt+=1
            #print(fn,fcnt)
            exp=dict()
            exp['name']=fn
            for kw in kwlist.keys():
                exp[kw+'_avg']=np.average(np.nan_to_num(np.array(kwlist[kw][ignore_param:])))
                exp[kw+'_std']=np.std(np.nan_to_num(np.array(kwlist[kw][ignore_param:])))
                #print(kw, kwlist[kw])
            explist.append(exp)
    expdf=pd.DataFrame(explist).fillna(0)
    # expdf['true_input_rate']=expdf['numRecordsInPerSecond_avg']/(expdf['busyTimeMsPerSecond_avg']/1000)
    # expdf=expdf.sort_values(by = ['numRecordsOutPerSecond_avg', 'latency_avg', 'latency_max'], ascending = [True, True, True])    
    expdf['busyTime_%'] = expdf['busyTimeMsPerSecond_avg']/1000.0*100.0
    expdf['backPressuredTime_%'] = expdf['backPressuredTimeMsPerSecond_avg']/1000.0*100.0
    expdf=expdf.sort_values(by = ['name'])
    #print("-------------------------------------------------------------------------------------")
    #print(expdf)
    print(expdf[['name', 'numRecordsInPerSecond_avg', 'numRecordsOutPerSecond_avg', 'busyTime_%', 'backPressuredTime_%']].to_string(index=False))
    print("Writing to .... "+"./logs/"+loc+"/summary.csv")
    expdf.to_csv("./logs/"+loc+"/summary.csv")

def upload_jar(fpath):
    fname=fpath.split('/')[-1]
    print(fname)
    jfile = {"file": (fname, (open(fpath, "rb")), "application/x-java-archive")}
    url="http://"+jmip+":"+str(jmpt)+"/jars/upload"
    response = requests.request(method="POST", url=url, files=jfile)
    return(response.json())

def getCStates():
    '''
    /sys/devices/system/cpu/cpu3/cpuidle/state0/name:POLL
    /sys/devices/system/cpu/cpu3/cpuidle/state1/name:C1
    /sys/devices/system/cpu/cpu3/cpuidle/state2/name:C1E
    /sys/devices/system/cpu/cpu3/cpuidle/state3/name:C3
    /sys/devices/system/cpu/cpu3/cpuidle/state4/name:C6
    '''
    ncores = int(runGetCmd(f"ssh {victim} nproc"))
    stateslist = [0, 0, 0, 0, 0]
    for core in range(0, ncores):
        for state in range(0, 5):
            stateslist[state] += int(runGetCmd(f"ssh {victim} cat /sys/devices/system/cpu/cpu{core}/cpuidle/state{state}/usage"))
    return stateslist[0], stateslist[1], stateslist[2], stateslist[3], stateslist[4]
    #return stateslist   
    #print(ncores)

def getStats():
    ret = runGetCmd(f"ssh {victim} ~/experiment-scripts/cloudlab_setup/c6220/getStats.sh")
    llx = []
    for x in ret.split(','):
        if x == '' or x == ' ' or x == '\n':
            llx.append(0)
        else:
            llx.append(int(x))
    return llx

def getRX():
    ret = runGetCmd(f"ssh {victim} ifconfig | grep -A5 10.10.1 | grep 'RX packets' | grep '\w*'")
    retlist = str(ret).strip().split(" ")
    rxpackets = int(retlist[2])
    rxbytes = int(retlist[5])
    return rxpackets, rxbytes

def getTX():
    ret = runGetCmd(f"ssh {victim} ifconfig | grep -A9 10.10.1 | grep 'TX packets' | grep '\w*'")
    retlist = str(ret).strip().split(" ")
    txpackets = int(retlist[2])
    txbytes = int(retlist[5])
    return txpackets, txbytes
    
def runexperiment(NREPEAT, NCORES, ITR, DVFS, FLINKRATE, BUFFTIMEOUT, SLEEPDISABLE):
    global GPOLL, GC1, GC1E, GC3, GC6, GRXP, GRXB, GTXP, GTXB, GERXP, GERXB, GETXP, GETXB, GQUERY, GPOLICY, GRERUNFLINK, GSOURCE, GSINK, GMAPPER
    #resetAllCores()
    #setCores(NCORES)

    setITR(ITR)
    setDVFS(DVFS)

    _flinkrate=FLINKRATE.split('_')
    _flinkdur=0
    for i in range(len(_flinkrate)):
        if(i%2!=0):
            _flinkdur+=int(_flinkrate[i])

    _flinkdur=int(_flinkdur/1000)
    print("Flink job duration: ", _flinkdur)

    KWD=f"{GQUERY}_cores{NCORES}_frate{FLINKRATE}_fbuff{BUFFTIMEOUT}_itr{ITR}_{GPOLICY}dvfs{DVFS}_source{GSOURCE}_mapper{GMAPPER}_sink{GSINK}_repeat{NREPEAT}"
    if SLEEPDISABLE == 1:
        KWD=f"disabled_{GQUERY}_cores{NCORES}_frate{FLINKRATE}_fbuff{BUFFTIMEOUT}_itr{ITR}_{GPOLICY}dvfs{DVFS}_source{GSOURCE}_mapper{GMAPPER}_sink{GSINK}_repeat{NREPEAT}"
    #KWD=GQUERY+"_"+"cores"+str(NCORES)+"_frate"+str(FLINKRATE)+"_fbuff"+str(BUFFTIMEOUT)+'_itr'+str(ITR)+"_"+str(GPOLICY)+"dvfs"+str(DVFS)+'_repeat'+str(NREPEAT)
    flinklogdir="./logs/"+KWD+"/Flinklogs/"
    itrlogsdir="./logs/"+KWD+"/ITRlogs/"
    runcmd('mkdir logs')
    runcmd('mkdir logs/'+KWD)
    runcmd('mkdir '+flinklogdir)
    runcmd('mkdir '+itrlogsdir)
    runcmd('mkdir '+flinklogdir+'/'+bootstrap.replace('.','_'))
    runcmd('mkdir '+flinklogdir+'/'+victim.replace('.','_'))
    
    # run a flink job
    if GRERUNFLINK == True:
        stopflink()
        startflink()
    with open("time.txt", "a") as f:
        ct = datetime.datetime.now()
        print("Time flink started:",ct,file=f)
    time.sleep(20)
        
    ## running the work
    #./flink-simplified/build-target/bin/flink run ./flink-benchmarks/target/kinesisBenchmarkMoc-1.1-SNAPSHOT-jar-with-dependencies.jar --ratelist 100_1000 --bufferTimeout 20
    rest_client = FlinkRestClient.get(host=jmip, port=jmpt)
    rest_client.overview()
    if GQUERY == "query1":
        ur = upload_jar(jarpath_q1)
    elif GQUERY == "imgproc":
        ur = upload_jar(jarpath_imgproc)
    jar_id = ur['filename'].split('/')[-1]


    if GQUERY == "query1":
        ## for query1 only
        job_id = rest_client.jars.run(jar_id, arguments={'ratelist': FLINKRATE, 'bufferTimeout': BUFFTIMEOUT, 'p-map': GMAPPER, 'p-source': GSOURCE, 'p-sink': GSINK, 'blurstep': 2})
    elif GQUERY == "imgproc":
        ## for imgproc only
        job_id = rest_client.jars.run(jar_id, arguments={'ratelist': FLINKRATE, 'bufferTimeout': BUFFTIMEOUT, 'pmap': GMAPPER, 'psrc': GSOURCE, 'psink': GSINK, 'blurstep': 2, 'batchSize': 1})
        
    job_id = rest_client.jobs.all()[0]['id']
    job = rest_client.jobs.get(job_id=job_id)
    print("deployed job id=", job_id)
    time.sleep(30)

    #GPOLL, GC1, GC1E, GC3, GC6, GRXP, GRXB, GTXP, GTXB, GERXP, GERXB, GETXP, GETXB = getStats()
    #cleanITRlogs()
    
    # get ITR log + flink log
    getFlinkLog(KWD, rest_client, job_id, flinklogdir, _flinkdur , 10)    # run _flinkdur sec, and record metrics every 10 sec
    #getITRlogs(KWD, NCORES, itrlogsdir, NREPEAT)
        
    ## get ifconfig RX, TX Bytes
    #rxpackets2, rxbytes2 = getRX()
    #txpackets2, txbytes2 = getTX()
    #with open(itrlogsdir+"/ifconfigRXTX.log","w") as f:
    #    print(f"RX_packets, {rxpackets2-rxpackets1}", file=f)
    #    print(f"RX_bytes, {rxbytes2-rxbytes1}", file=f)
    #    print(f"TX_packets, {txpackets2-txpackets1}", file=f)
    #    print(f"TX_bytes, {txbytes2-txbytes1}", file=f)

    #stateslist2 = getCStates()
    #with open(itrlogsdir+"/sleepstates.log","w") as f:
    #    subt = [e2 - e1 for (e1, e2) in zip(stateslist1, stateslist2)]
    #    print(f"POLL, C1, C1E, C3, C6", file=f)
    #    print(f"{subt}", file=f)

    if GRERUNFLINK == True:
        stopflink()
    with open("time.txt","a") as f:
        ct2 = datetime.datetime.now()
        print("Time flink stopped:",ct2, file=f)
    fnames=os.listdir(flinklogdir+bootstrap.replace('.','_')+"/")
    latency_list={}
    latency_avg={}
    for ff in fnames:
        latency_list[ff]=parseFlinkLatency(flinklogdir+bootstrap.replace('.','_')+"/"+ff)
        latency_avg[ff]=np.average(latency_list[ff])

    print('latency in flink log: ', latency_list)
    print('average latency in flink log', latency_avg)

    parseFlinkMetricsMod(flinklogdir, loc=KWD, ignore_mins=2)

if __name__ == '__main__':    
    parser = argparse.ArgumentParser()
    parser.add_argument("--cores", help="num of cpu cores")
    parser.add_argument("--rapl", help="Rapl power limit [35, 135]")
    parser.add_argument("--itr", help="Static interrupt delay [2, 1024]")
    parser.add_argument("--dvfs", help="Static DVFS value [0xc00 - 0x1d00]")
    parser.add_argument("--nrepeat", help="repeat value")
    parser.add_argument("--verbose", help="Print mcd raw stats")
    parser.add_argument("--flinkrate", help="input rate of Flink query")
    parser.add_argument("--bufftimeout", help="bufferTimeout in Flink")
    parser.add_argument("--runcmd", help="startflink/stopflink")
    parser.add_argument("--nsource", help="num of source")
    parser.add_argument("--nsink", help="num of sink")
    parser.add_argument("--nmapper", help="num of mapper")
    parser.add_argument("--query", help="query to run (i.e. query1, quer5y, imgproc)", required=True)
    #conservative, ondemand, userspace, powersave, performance, schedutil
    parser.add_argument("--policy", help="dvfs policy", choices=['conservative', 'ondemand', 'powersave', 'performance', 'schedutil', 'userspace'])
    parser.add_argument("--sleepdisable", help="enable/disable cstate sleep states")
    args = parser.parse_args()

    if args.runcmd:
        if(args.runcmd=='stopflink'):
            stopflink()
            exit(0)
        if(args.runcmd=='startflink'):
            stopflink()
            startflink()
            exit(0)

    if args.itr:
        print("ITR = ", args.itr)
        ITR=args.itr
        GITR=int(ITR)

    if args.dvfs:
        print("DVFS = ", args.dvfs)
        DVFS=args.dvfs
        GDVFS=DVFS

    if args.nrepeat:
        print("NREPEAT = ", args.nrepeat)
        NREPEAT = int(args.nrepeat)

    if args.cores:
        print("NCORES = ", args.cores)
        NCORES = int(args.cores)

    if args.flinkrate:
        print("flinkrate = ", args.flinkrate)
        FLINKRATE = args.flinkrate

    if args.bufftimeout:
        print("BUFFTIMEOUT = ", args.bufftimeout)
        BUFFTIMEOUT = args.bufftimeout

    if args.query:
        print(f"QUERY = {args.query}")        
        GQUERY = args.query

    if args.policy:
        print(f"POLICY = {args.policy}")
        GPOLICY = args.policy

    if args.nsource:
        print(f"Source = {args.nsource}")
        GSOURCE = int(args.nsource)
    if args.nsink:
        print(f"Sink = {args.nsink}")
        GSINK = int(args.nsink)
    if args.nmapper:
        print(f"Mapper = {args.nmapper}")
        GMAPPER = int(args.nmapper)

    if args.sleepdisable:
        print(f"Sleep Disabled = {args.sleepdisable}")
        SLEEPDISABLE = int(args.sleepdisable)
    else:
        SLEEPDISABLE = 0
        
    try:
        #GPOLL, GC1, GC1E, GC3, GC6, GRXP, GRXB, GTXP, GTXB = getStats()
        runexperiment(NREPEAT, NCORES, ITR, DVFS, FLINKRATE, BUFFTIMEOUT, SLEEPDISABLE)
    except Exception as error:
        print(error)
        traceback.print_exc()
        ## stop flink on any errors
        stopflink()
        exit(0)
