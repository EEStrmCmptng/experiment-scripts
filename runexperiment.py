from flink_rest_client import FlinkRestClient
import sys, os, time, json, requests, argparse


ROOTDIR=os.path.dirname(os.getcwd())
#FLINKROOT=os.path.dirname(os.getcwd())+'/flink-simplified'
FLINKROOT='/home/tidb/Desktop/data/energy/experiment-scripts/flink-simplified/'
print(FLINKROOT)

# the script will run on bootstrap
# bootstrap='192.168.1.153'   # jobmanager
# victim='192.168.1.11'       # scp logs from victim to bootstrap
bootstrap='192.168.1.180'    # For testing
victim='192.168.1.181'           # For testing
jarpath='./flink-benchmarks/target/kinesisBenchmarkMoc-1.1-SNAPSHOT-jar-with-dependencies.jar'


localip=os.popen("hostname -I").read()
print(localip)

iplist=[]


def stopflink():
    print(os.popen("cp -r ./flink-cfg/* "+FLINKROOT+"/flink-dist/target/flink-1.14.0-bin/flink-1.14.0/conf/").read())
    print("stopping flink...")
    print(os.popen("cd "+FLINKROOT+"/flink-dist/target/flink-1.14.0-bin/flink-1.14.0/bin/ ; ./stop-cluster.sh").read())
    #print(os.popen("rm -rf "+FLINKROOT+"/flinkstate/*").read())
    print("stopped flink")


def startflink():
    print("starting flink...")

    for ip in open('./flink-cfg/workers','r').readlines():
        iplist.append(ip.replace("\n",""))
    for ip in open('./flink-cfg/masters','r').readlines():
        iplist.append(ip.replace("\n","").replace(':8081',''))

    print(os.popen("cp -r ./flink-cfg/* "+FLINKROOT+"/flink-dist/target/flink-1.14.0-bin/flink-1.14.0/conf/").read())

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
        print(os.popen('ssh '+ip+' "cp '+FLINKROOT+'/flink-dist/target/flink-1.14.0-bin/flink-1.14.0/conf/flink-conf.yaml '+FLINKROOT+'/scripts/flink-conf.yaml"').read())    # customscheduler need to read it

    print('-----------------------------------------------------')
    print(os.popen('cd '+FLINKROOT+'/flink-dist/target/flink-1.14.0-bin/flink-1.14.0/bin ; ./start-cluster.sh').read())
    print("started flink")



NREPEAT=0
NCORES=16
ITR=0
RAPL=0
DVFS=0
FLINKRATE='100_10000'
BUFFTIMEOUT='20'
KWD='**'

jmip=bootstrap
jmpt=8081


def runcmd(cmd):
    print('------------------------------------------------------------')
    print(cmd)
    res=os.popen(cmd).read()
    print(res)
    print('------------------------------------------------------------')


# set ITR configurations on victim node
def setITR(v):
    global ITR
    runcmd('ssh ' + victim + ' "/app/ethtool-4.5/ethtool -C eth0 rx-usecs '+v+'"')
    time.sleep(0.5)
    ITR = int(v)

def setRAPL(v):
    global RAPL
    if ITR != 1:
        runcmd('ssh ' + victim + ' "/app/uarch-configure/rapl-read/rapl-power-mod ' + v + '"')
        time.sleep(0.5)
        RAPL = int(v)

def setDVFS(v):
    global DVFS
    if ITR != 1:
        runcmd('ssh ' + victim + ' "wrmsr -a 0x199 ' + v + '"')
        time.sleep(0.5)
    DVFS = v


def init():
    runcmd('mkdir Flinklogs_'+KWD)
    runcmd('mkfir ITRlogs_'+KWD)
    runcmd('mkdir ITRlogs_'+KWD+'/'+bootstrap.replace('.','_'))
    runcmd('mkdir ITRlogs_'+KWD+'/'+victim.replace('.','_'))
    runcmd('mkdir Flinklogs_'+KWD+'/'+bootstrap.replace('.','_'))
    runcmd('mkdir Flinklogs_'+KWD+'/'+victim.replace('.','_'))

# get ITR logs from victim node
def getITRlogs(cores):
    for i in range(cores):
        gcmd="cat /proc/ixgbe_stats/core/"+str(i)+" &> /app/flink_dmesg."+str(i)
        runcmd('ssh ' + victim + ' "' + gcmd + '"')
        gcmd="scp -r "+victim+":/app/flink_dmesg."+str(i)+" ./ITRlogs_"+KWD+"/"+victim.replace('.','_')+"linux.flink.dmesg."+"_"+str(i)
        runcmd(gcmd)

# get Flink logs from victim node
def getFlinkLog():
    gcmd="scp -r "+victim+":"+FLINKROOT+"/flink-dist/target/flink-1.14.0-bin/flink-1.14.0/log/flink-root-taskexecutor* ./Flinklogs_"+KWD+"/"+victim.replace('.','_')+"/"
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


if __name__ == '__main__':
    # python3 runexperiment.py --rapl 50 --itr 10 --dvfs 0xfff --nrepeat 1 --flinkrate 100_10000 --cores 16
    parser = argparse.ArgumentParser()
    parser.add_argument("--cores", help="num of cpu cores")
    parser.add_argument("--rapl", help="Rapl power limit [35, 135]")
    parser.add_argument("--itr", help="Static interrupt delay [10, 500]")
    parser.add_argument("--dvfs", help="DVFS value [0xc00 - 0x1d00]")
    parser.add_argument("--nrepeat", help="repeat value")
    parser.add_argument("--verbose", help="Print mcd raw stats")
    parser.add_argument("--flinkrate", help="input rate of Flink query")
    parser.add_argument("--bufftimeout", help="buffer-Timeout in Flink")
    parser.add_argument("--runcmd", help="runexp/stopflink")
    args = parser.parse_args()

    if args.runcmd:
        if(args.runcmd=='stopflink'):
            stopflink()
            exit(0)

    if args.itr:
        print("ITR = ", args.itr)
        setITR(args.itr)

    if args.dvfs:
        print("DVFS = ", args.dvfs)
        setDVFS(args.dvfs)

    if args.rapl:
        print("RAPL = ", args.rapl)
        setRAPL(args.rapl)

    if args.nrepeat:
        print("NREPEAT = ", args.nrepeat)
        NREPEAT = args.nrepeat

    if args.cores:
        print("NCORES = ", args.cores)
        NCORES = args.cores

    if args.flinkrate:
        print("flinkrate = ", args.flinkrate)
        FLINKRATE = args.flinkrate

    if args.bufftimeout:
        print("BUFFTIMEOUT = ", args.bufftimeout)
        BUFFTIMEOUT = args.bufftimeout

    KWD=str(NREPEAT)+"_"+str(ITR)+"_"+str(DVFS)+"_"+str(RAPL)
    init()

    # run a flink job
    stopflink()
    startflink()
    time.sleep(20)
    #../dependencies/flink-simplified/build-target/bin/flink run ../dependencies/flink-benchmarks/target/kinesisBenchmarkMoc-1.1-SNAPSHOT-jar-with-dependencies.jar --ratelist $1 --buffer-Timeout 20
    rest_client = FlinkRestClient.get(host=jmip, port=jmpt)
    rest_client.overview()
    ur = upload_jar(jarpath)
    jar_id = ur['filename'].split('/')[-1]
    job_id = rest_client.jars.run(jar_id, arguments={'ratelist': FLINKRATE, 'buffer-Timeout': BUFFTIMEOUT})
    job_id = rest_client.jobs.all()[0]['id']
    job = rest_client.jobs.get(job_id=job_id)
    print("deployed job id=", job_id)
    time.sleep(60)

    # get ITR log + flink log
    getITRlogs(NCORES)
    getFlinkLog()

    stopflink()



