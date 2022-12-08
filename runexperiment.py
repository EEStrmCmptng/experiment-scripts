from flink_rest_client import FlinkRestClient
import sys, os, time, json, requests, argparse
import numpy as np


ROOTDIR=os.path.dirname(os.getcwd())
#FLINKROOT=os.path.dirname(os.getcwd())+'/flink-simplified'
FLINKROOT='/mnt/eestreaming-refactor/experiment-scripts/flink-simplified/'
print(FLINKROOT)

# the script will run on bootstrap
bootstrap='192.168.1.153'   # jobmanager
victim='192.168.1.11'       # scp logs from victim to bootstrap
jarpath='./flink-benchmarks/target/kinesisBenchmarkMoc-1.1-SNAPSHOT-jar-with-dependencies.jar'

jmip=bootstrap
jmpt=8081

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


# set ITR configurations on victim node
def setITR(v):
    runcmd('ssh ' + victim + ' "/app/ethtool-4.5/ethtool -C eth0 rx-usecs '+v+'"')
    time.sleep(0.5)
    ITR = int(v)

def setRAPL(v):
    if ITR != 1:
        runcmd('ssh ' + victim + ' "/app/uarch-configure/rapl-read/rapl-power-mod ' + v + '"')
        time.sleep(0.5)
        RAPL = int(v)

def setDVFS(v):
    if ITR != 1:
        runcmd('ssh ' + victim + ' "wrmsr -a 0x199 ' + v + '"')
        time.sleep(0.5)
    DVFS = v


def init(KWD):
    runcmd('mkdir logs')
    runcmd('mkdir logs/Flinklogs_'+KWD)
    runcmd('mkdir logs/ITRlogs_'+KWD)
    runcmd('mkdir logs/Flinklogs_'+KWD+'/'+bootstrap.replace('.','_'))
    runcmd('mkdir logs/Flinklogs_'+KWD+'/'+victim.replace('.','_'))

# get ITR logs from victim node
def getITRlogs(KWD, cores):
    for i in range(cores):
        gcmd="cat /proc/ixgbe_stats/core/"+str(i)+" &> /app/flink_dmesg."+str(i)
        runcmd('ssh ' + victim + ' "' + gcmd + '"')
        gcmd="scp -r "+victim+":/app/flink_dmesg."+str(i)+" ./logs/ITRlogs_"+KWD+"/"+"linux.flink.dmesg."+"_"+str(i)
        runcmd(gcmd)

# get Flink logs 
def getFlinkLog(KWD, rest_client, job_id, edir, _clock, interval):
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
                    ff=open(edir+'/'+vname+'_'+tid, 'a')
                    ff.write(vts +'; '+ vname +'; '+ vpall +'; '+ ttm +'; '+ tid +'; '+ t_busytime +'; '+ t_backpressure +'; '+ t_idletime +'; '+ t_opsin +'; '+ t_opsout+'; '+t_duration+'; '+t_rbytes+'; '+t_wbytes+'; '+t_rrec+'; '+t_wrec+'  \n')
        time.sleep(interval)
        clock-=interval

    gcmd="scp -r "+victim+":"+FLINKROOT+"/flink-dist/target/flink-1.14.0-bin/flink-1.14.0/log/* ./logs/Flinklogs_"+KWD+"/"+victim.replace('.','_')+"/"
    runcmd(gcmd)
    gcmd="scp -r "+bootstrap+":"+FLINKROOT+"/flink-dist/target/flink-1.14.0-bin/flink-1.14.0/log/* ./logs/Flinklogs_"+KWD+"/"+bootstrap.replace('.','_')+"/"
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


def upload_jar(fpath):
    fname=fpath.split('/')[-1]
    print(fname)
    jfile = {"file": (fname, (open(fpath, "rb")), "application/x-java-archive")}
    url="http://"+jmip+":"+str(jmpt)+"/jars/upload"
    response = requests.request(method="POST", url=url, files=jfile)
    return(response.json())


def runexperiment(NREPEAT, NCORES, ITR, RAPL, DVFS, FLINKRATE, BUFFTIMEOUT):
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

    KWD=str(NREPEAT)+"_"+str(ITR)+"_"+str(DVFS)+"_"+str(RAPL)
    init(KWD)

    # run a flink job
    stopflink()
    startflink()
    time.sleep(20)
    #./flink-simplified/build-target/bin/flink run ./flink-benchmarks/target/kinesisBenchmarkMoc-1.1-SNAPSHOT-jar-with-dependencies.jar --ratelist 100_1000 --buffer-Timeout 20
    rest_client = FlinkRestClient.get(host=jmip, port=jmpt)
    rest_client.overview()
    ur = upload_jar(jarpath)
    jar_id = ur['filename'].split('/')[-1]
    job_id = rest_client.jars.run(jar_id, arguments={'ratelist': FLINKRATE, 'buffer-Timeout': BUFFTIMEOUT})
    job_id = rest_client.jobs.all()[0]['id']
    job = rest_client.jobs.get(job_id=job_id)
    print("deployed job id=", job_id)
    # time.sleep(60)

    # get ITR log + flink log
    getFlinkLog(KWD, rest_client, job_id, "./logs/Flinklogs_"+KWD+"/", _flinkdur, 10)    # run _flinkdur sec, and record metrics every 10 sec
    getITRlogs(KWD, NCORES)

    stopflink()

    flinklogdir="./logs/Flinklogs_"+KWD+"/"+bootstrap.replace('.','_')+"/"
    fnames=os.listdir(flinklogdir)
    latency_list={}
    latency_avg={}
    for ff in fnames:
        latency_list[ff]=parseFlinkLatency(flinklogdir+ff)
        latency_avg[ff]=np.average(latency_list[ff])

    print(latency_list)
    print(latency_avg)



if __name__ == '__main__':
    # python3 runexperiment.py --rapl 50 --itr 10 --dvfs 0xfff --nrepeat 1 --flinkrate 100_100000 --cores 16
    parser = argparse.ArgumentParser()
    parser.add_argument("--cores", help="num of cpu cores")
    parser.add_argument("--rapl", help="Rapl power limit [35, 135]")
    parser.add_argument("--itr", help="Static interrupt delay [10, 500]")
    parser.add_argument("--dvfs", help="DVFS value [0xc00 - 0x1d00]")
    parser.add_argument("--nrepeat", help="repeat value")
    parser.add_argument("--verbose", help="Print mcd raw stats")
    parser.add_argument("--flinkrate", help="input rate of Flink query")
    parser.add_argument("--bufftimeout", help="buffer-Timeout in Flink")
    parser.add_argument("--runcmd", help="runexp/stopflink/plot")
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

