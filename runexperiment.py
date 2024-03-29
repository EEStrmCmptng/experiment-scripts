from flink_rest_client import FlinkRestClient
import sys, os, time, json, requests, argparse
import numpy as np
import pandas as pd
import datetime

ROOTDIR=os.path.dirname(os.getcwd())
#FLINKROOT=os.path.dirname(os.getcwd())+'/flink-simplified'
FLINKROOT='/mnt/eestreaming-refactor/experiment-scripts/flink-simplified/'
#print(FLINKROOT)
MAXCORES=16    # num of cores. 16C32T
CPUIDS=[[0,16],[1,17],[2,18],[3,19],[4,20],[5,21],[6,22],[7,23],[8,24],[9,25],[10,26],[11,27],[12,28],[13,29],[14,30],[15,31]]

# the script will run on bootstrap
bootstrap='192.168.1.153'   # jobmanager
victim='192.168.1.11'       # scp logs from victim to bootstrap
jarpath='./flink-benchmarks/target/Imgproc-jar-with-dependencies.jar'

jmip=bootstrap
jmpt=8081
GLOBAL_ITR=1

def stopflink():
    print(os.popen("cp -r ./flink-cfg/* "+FLINKROOT+"/flink-dist/target/flink-1.14.0-bin/flink-1.14.0/conf/").read())
    print("stopping flink...")
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
    global GLOBAL_ITR
    
    runcmd('ssh ' + victim + ' "/app/ethtool-4.5/ethtool -C eth0 rx-usecs '+v+'"')
    time.sleep(0.5)
    GLOBAL_ITR = int(v)
    print(" -------------------- setITR on victim --------------------")
    print('ssh ' + victim + ' "/app/ethtool-4.5/ethtool -C eth0 rx-usecs '+str(GLOBAL_ITR)+'"')
    runcmd('ssh ' + victim + ' "/app/ethtool-4.5/ethtool -c eth0"')
    print("")

def setRAPL(v):
    global GLOBAL_ITR
    
    if GLOBAL_ITR != 1:
        runcmd('ssh ' + victim + ' "/app/uarch-configure/rapl-read/rapl-power-mod ' + v + '"')
        time.sleep(0.5)

# HOWTO check DVFS policy: ssh 192.168.1.11 /app/perf/display_dvfs_governors.sh
def setDVFS(v):
    global GLOBAL_ITR
    
    print(" -------------------- setDVFS on victim --------------------")
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

    # print CPU frequency across all cores
    runcmd('ssh ' + victim + ' "rdmsr -a 0x199"')
    print("")


# get ITR logs from victim node
def getITRlogs(KWD, cores, itrlogsdir,NREPEAT):
    for i in range(cores):
        gcmd="cat /proc/ixgbe_stats/core/"+str(i)+" &> /app/flink_dmesg."+str(i)+"_"+str(NREPEAT)
        runcmd('ssh ' + victim + ' "' + gcmd + '"')
        gcmd="scp -r "+victim+":/app/flink_dmesg."+str(i)+"_"+str(NREPEAT)+" "+itrlogsdir+"linux.flink.dmesg."+"_"+str(i)+"_"+str(NREPEAT)
        runcmd(gcmd)

# get Flink logs 
def getFlinkLog(KWD, rest_client, job_id, flinklogdir, _clock, interval):
    tmid=[]
    for tm in rest_client.taskmanagers.all():
        tmid.append(tm['id'])

    clock=_clock
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
        time.sleep(interval)
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
                print(kw, kwlist[kw])
            explist.append(exp)
    expdf=pd.DataFrame(explist).fillna(0)
    # expdf['true_input_rate']=expdf['numRecordsInPerSecond_avg']/(expdf['busyTimeMsPerSecond_avg']/1000)
    # expdf=expdf.sort_values(by = ['numRecordsOutPerSecond_avg', 'latency_avg', 'latency_max'], ascending = [True, True, True])
    print("-------------------------------------------------------------------------------------")
    print(expdf)


def upload_jar(fpath):
    fname=fpath.split('/')[-1]
    print(fname)
    jfile = {"file": (fname, (open(fpath, "rb")), "application/x-java-archive")}
    url="http://"+jmip+":"+str(jmpt)+"/jars/upload"
    response = requests.request(method="POST", url=url, files=jfile)
    return(response.json())


def runexperiment(NREPEAT, NCORES, ITR, RAPL, DVFS, FLINKRATE, BUFFTIMEOUT):
    resetAllCores()
    setCores(NCORES)
    setITR(ITR)
    setDVFS(DVFS)
    setRAPL(RAPL)

    _flinkrate=FLINKRATE.split('_')
    _flinkdur=0
    for i in range(len(_flinkrate)):
        if(i%2!=0):
            _flinkdur+=int(_flinkrate[i])

    _flinkdur=int(_flinkdur/1000)
    print("Flink job duration: ", _flinkdur)

    KWD="cores"+str(NCORES)+"_frate"+str(FLINKRATE)+"_fbuff"+str(BUFFTIMEOUT)+'_itr'+str(ITR)+"_dvfs"+str(DVFS)+"_rapl"+str(RAPL)+'_repeat'+str(NREPEAT)
    flinklogdir="./logs/"+KWD+"/Flinklogs/"
    itrlogsdir="./logs/"+KWD+"/ITRlogs/"
    runcmd('mkdir logs')
    runcmd('mkdir logs/'+KWD)
    runcmd('mkdir '+flinklogdir)
    runcmd('mkdir '+itrlogsdir)
    runcmd('mkdir '+flinklogdir+'/'+bootstrap.replace('.','_'))
    runcmd('mkdir '+flinklogdir+'/'+victim.replace('.','_'))

    # run a flink job
    stopflink()
    startflink()
    with open("time.txt", "a") as f:
        ct = datetime.datetime.now()
        print("Time flink started:",ct,file=f)
    time.sleep(20)
    #./flink-simplified/build-target/bin/flink run ./flink-benchmarks/target/kinesisBenchmarkMoc-1.1-SNAPSHOT-jar-with-dependencies.jar --ratelist 100_1000 --bufferTimeout 20
    rest_client = FlinkRestClient.get(host=jmip, port=jmpt)
    rest_client.overview()
    ur = upload_jar(jarpath)
    jar_id = ur['filename'].split('/')[-1]
    job_id = rest_client.jars.run(jar_id, arguments={'ratelist': FLINKRATE, 'bufferTimeout': BUFFTIMEOUT, 'pmap': 16, 'psrc': 14, 'psink': 2, 'cmpSize': 28, 'blurstep': 2})
    job_id = rest_client.jobs.all()[0]['id']
    job = rest_client.jobs.get(job_id=job_id)
    print("deployed job id=", job_id)
    time.sleep(30)

    # get ITR log + flink log
    getFlinkLog(KWD, rest_client, job_id, flinklogdir, _flinkdur, 10)    # run _flinkdur sec, and record metrics every 10 sec
    getITRlogs(KWD, NCORES, itrlogsdir, NREPEAT)

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

    parseFlinkMetrics(flinklogdir)


if __name__ == '__main__':
    # python3 runexperiment.py --rapl 50 --itr 10 --dvfs 0xfff --nrepeat 1 --flinkrate 100_100000 --cores 16
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

    if args.dvfs:
        print("DVFS = ", args.dvfs)
        DVFS=args.dvfs

    if args.rapl:
        print("RAPL = ", args.rapl)
        RAPL=args.rapl

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

    runexperiment(NREPEAT, NCORES, ITR, RAPL, DVFS, FLINKRATE, BUFFTIMEOUT)
    resetAllCores()
