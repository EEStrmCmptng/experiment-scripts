from flink_rest_client import FlinkRestClient
import sys, os, time, json, requests, argparse


# the script will run on bootstrap
# bootstrap='192.168.1.153'   # jobmanager
# victim='192.168.1.11'       # scp logs from victim to bootstrap
bootstrap='192.168.1.180'   # jobmanager
victim='192.168.1.181'       # scp logs from victim to bootstrap

NREPEAT=0
NCORES=16

ITR=0
RAPL=0
DVFS=0
KWD='**'

jarpath='./flink-benchmarks/target/kinesisBenchmarkMoc-1.1-SNAPSHOT-jar-with-dependencies.jar'
ratelist='100_10000'
bufftimeout='20'
flinkpath='./flink-simplified'
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
    runcmd('mkdir flinklogs_'+KWD)
    runcmd('mkfir ITRlogs_'+KWD)
    runcmd('mkdir flinklogs_'+KWD+'/'+bootstrap.replace('.','_'))
    runcmd('mkdir flinklogs_'+KWD+'/'+victim.replace('.','_'))

# get ITR logs from victim node
def getITRlogs(cores):
    for i in range(cores):
        gcmd="cat /proc/ixgbe_stats/core/"+str(i)+" &> /app/flink_dmesg."+str(i)
        runcmd('ssh ' + victim + ' "' + gcmd + '"')
        gcmd="scp -r "+victim+":/app/flink_dmesg."+str(i)+" ./ITRlogs_"+KWD+"/linux.flink.dmesg."+"_"+str(i)
        runcmd(gcmd)

# get Flink logs from victim node
def getFlinkLog():
    gcmd="scp -r "+victim+":/mnt/eestreaming/dependencies/flink-simplified/flink-dist/target/flink-1.14.0-bin/flink-1.14.0/log/flink-root-taskexecutor* ./flinklogs_"+KWD+"/"+victim.replace('.','_')
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
    parser = argparse.ArgumentParser()
    parser.add_argument("--rapl", help="Rapl power limit [35, 135]")
    parser.add_argument("--itr", help="Static interrupt delay [10, 500]")
    parser.add_argument("--dvfs", help="DVFS value [0xc00 - 0x1d00]")
    parser.add_argument("--nrepeat", help="repeat value")
    parser.add_argument("--verbose", help="Print mcd raw stats")
    parser.add_argument("--rate")
    args = parser.parse_args()

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

    if args.rate:
        print("rate = ", args.rate)
        RATE = args.rate

    KWD=str(NREPEAT)+"_"+str(ITR)+"_"+str(DVFS)+"_"+str(RAPL)

    # run a flink job
    runcmd('python3 deployflink.py start')
    time.sleep(20)
    #../dependencies/flink-simplified/build-target/bin/flink run ../dependencies/flink-benchmarks/target/kinesisBenchmarkMoc-1.1-SNAPSHOT-jar-with-dependencies.jar --ratelist $1 --buffer-Timeout 20
    rest_client = FlinkRestClient.get(host=jmip, port=jmpt)
    rest_client.overview()
    ur = upload_jar(jarpath)
    jar_id = ur['filename'].split('/')[-1]
    job_id = rest_client.jars.run(jar_id, arguments={'ratelist': ratelist, 'buffer-Timeout': bufftimeout})
    job_id = rest_client.jobs.all()[0]['id']
    job = rest_client.jobs.get(job_id=job_id)
    print("deployed job id=", job_id)
    time.sleep(60)

    # get ITR log + flink log
    getITRlogs(NCORES)
    getFlinkLog()

    runcmd('python3 deployflink.py stop')

