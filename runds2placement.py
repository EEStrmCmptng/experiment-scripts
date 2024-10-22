from flink_rest_client import FlinkRestClient
import sys, os, time, json, requests, argparse
import numpy as np
import pandas as pd
import datetime
import traceback
import subprocess
import math, random
from subprocess import Popen, PIPE, call
import networkx as nx
from collections import defaultdict

bootstrap='10.10.1.1'   # jobmanager
jmip=bootstrap
jmpt=8081

def gettimestamp():
    return(str(int(time.time())))

def nested_dict():
    return defaultdict(int)

def str2int(str):
    if(str=='NaN'):
        return(-1)
    fstr=float(str)
    istr=int(fstr)
    istr=max(0, istr)
    return(istr)

def str2float(str):
    if(str=='NaN'):
        return(-1.0)
    fstr=float(str)
    return(fstr)

def get_task_metrics_details_multiple(jmip, jmpt, jobid, vid, fieldlist):
    st=time.time()
    _metriclist = get_task_vertix_metrics(jmip, jmpt, jobid, vid)
    metriclist = [d['id'] for d in _metriclist]
    fieldliststr=""
    for fieldid in fieldlist:
        if(fieldid in metriclist):
            fieldliststr=fieldliststr+fieldid+","
    # http://128.105.145.114:8081/jobs/35e375d1885b8b36ae6242319de7b952/vertices/97db730e07d35d6850e3d51339e006de/metrics?get=3.numRecordsInPerSecond,0.numRecordsInPerSecond,0.busyTimeMsPerSecond,
    url = "http://"+jmip+":"+str(jmpt)+"/jobs/{}/vertices/{}/metrics?get={}".format(jobid, vid, fieldliststr)
    response = requests.get(url)
    response.raise_for_status()
    ans=response.json()
    for fieldid in fieldlist:
        if(not (fieldid in metriclist)):
            ans.append({"id":fieldid, "value":0})
    ansdict={}
    for aa in ans:
        ansdict[aa['id']]=aa['value']
    return(ansdict)

def get_task_vertix_metrics(jmip, jmpt, job_id, vid):
    url="http://"+jmip+":"+str(jmpt)+"/jobs/"+job_id+"/vertices/"+vid+"/metrics"
    response = requests.get(url)
    response.raise_for_status()
    ans=response.json()
    return(ans)

def get_task_vertix_details(jmip, jmpt, job_id, vid):
    url="http://"+jmip+":"+str(jmpt)+"/jobs/"+job_id+"/vertices/"+vid
    response = requests.get(url)
    response.raise_for_status()
    ans=response.json()
    return(ans)

def get_task_metrics_details(jmip, jmpt, jobid, vid, fieldid):
    _metriclist = get_task_vertix_metrics(jmip, jmpt, jobid, vid)
    metriclist = [d['id'] for d in _metriclist]
    if(not (fieldid in metriclist)):
        return([{"id":fieldid, "value":0}])
    # http://192.168.1.105:8081/jobs/e81ee095a99bfc431e260d044ff7e03d/vertices/ea632d67b7d595e5b851708ae9ad79d6/metrics?get=4.busyTimeMsPerSecond
    url = "http://"+jmip+":"+str(jmpt)+"/jobs/{}/vertices/{}/metrics?get={}".format(jobid, vid, fieldid)
    response = requests.get(url)
    response.raise_for_status()
    ans=response.json()#[0]['value']
    return(ans)

def get_prometheus_query(jmip, query):
    jmurl = 'http://'+jmip+':9090'
    response = requests.get(f'{jmurl}/api/v1/query', params={'query': query})
    results = response.json()
    return results

def get_prometheus_cpuutil(jmip, tmip):
    query = 'sum(irate(node_cpu_seconds_total{mode="user", instance="'+tmip+':9100"}[30s])) * 100 + sum(irate(node_cpu_seconds_total{mode="system", instance="'+tmip+':9100"}[30s])) * 100'
    # result = get_prometheus_query(jmip, query)
    # # get the sum of cpu user and system utilization (percentage value)
    # cpu=result["data"]["result"][0]['value'][1]
    # return cpu
    attempt_count = 0
    while (attempt_count<=10000):
        try:
            result = get_prometheus_query(jmip, query)
            cpu=result["data"]["result"][0]['value'][1]
            return cpu
        except Exception as e:
            attempt_count += 1
            #print(f"Attempt {attempt_count}: An exception occurred: {e} ", result)
    return(-1)

def get_job_plan_details(jmip, jmpt, jobid):
    # http://192.168.1.105:8081/jobs/e81ee095a99bfc431e260d044ff7e03d/plan
    url = "http://"+jmip+":"+str(jmpt)+"/jobs/{}/plan".format(jobid)
    response = requests.get(url)
    response.raise_for_status()
    ans=response.json()#[0]['value']
    return(ans)

def ds2(mrate=100000, mutil=0.7):
    # initiate a map of workers: pull cpu util metrics
    workerCpuUtils = {}
    for ip in ['10.10.1.2', '10.10.1.3', '10.10.1.4']:
        workerCpuUtils[ip] = []

    srcratelist=[mrate]
    TARGET_UTIL=mutil
    
    rest_client = FlinkRestClient.get(host=jmip, port=jmpt)
    rest_client.overview()
    job_id = rest_client.jobs.all()[0]['id']
    vertex_ids=rest_client.jobs.get_vertex_ids(job_id)
    job = rest_client.jobs.get(job_id=job_id)
    
    tmidlist=[]
    for tm in rest_client.taskmanagers.all():
        tmidlist.append(tm['id'])
        
    print("rest_client.overview(): ", rest_client.overview())
    #print(tmidlist)
    #print(job_id)
    #print(vertex_ids)
    #print(job)
    
    job_plan=get_job_plan_details(jmip, jmpt, job_id)['plan']['nodes']
    #print("job_plan:  ", job_plan)
    
    JobGraph=nx.DiGraph()
    for opr in job_plan:
        oname=opr['description'].replace(' ','_').replace('+','_').replace('-','_').replace(',','_').replace(':','_').replace(';','_').replace('<br/>','').replace('(','_').replace(')','_')
        innodes=[x['id'] for x in opr['inputs']] if ('inputs' in opr) else []
        JobGraph.add_node(opr['id'], parallelism=opr['parallelism'], name=oname, pname=oname,    # vid, parallelism, name of current operator, name to be printed in schedulercfg
                          innodes=innodes,    # vid of upstream operators
                          outboundtype="",    # outbound link type (REBALANCE/HASH/FORWARD)
                          _ttm=np.array([]), _cpuutil=np.array([]), cpuutil=0,
                          _oip=np.array([]), _oop=np.array([]), _tip=np.array([]), _top=np.array([]), _tops=np.array([]), _tips=np.array([]),
                          _busytime=np.array([]), _bkpstime=np.array([]), _idletime=np.array([]), _selectivity=np.array([]),
                          _optimalparallelism=np.array([]), _ioread=np.array([]), _iowrite=np.array([]), _oib=np.array([]), _oob=np.array([]),
                          _pertask=[],
                          oip=0, oop=0,    # aggregated observed input/output records rate among all subtasks
                          tip=0, top=0,    # aggregated true input/output records rate among all subtasks
                          tops=0, tips=0,
                          busytime=0, bkpstime=0, idletime=0, selectivity=0.0,    # average of metric among all subtasks
                          optimalparallelism=0,
                          maxoptimalparallelism=0,
                          ioread=0, iowrite=0,    # aggregated rocksdb IO bytes rate among all subtasks
                          cpcost=0, nwcost=0, iocost=0,    # compute / network cost
                          oib=0, oob=0    # aggregated observed input/output bytes rate among all subtasks
                          )
    for opr in job_plan:
        oid=opr['id']
        if('inputs' in opr):
            for uopr in opr['inputs']:
                uid=uopr['id']
                JobGraph.add_edge(uid, oid)    #uid->oid
                JobGraph.nodes[uid]['outboundtype']=uopr['ship_strategy']

    toposeq=list(nx.topological_sort(JobGraph))    # topological_sort on operators
    #print("topological_sort:    ", toposeq)


    #------------------------------------# run
    for key, value in workerCpuUtils.items():
        value.append(int(str2float(get_prometheus_cpuutil(jmip, key))*10))
        workerCpuUtils[key] = value
    #print("workerCpuUtils:", workerCpuUtils)
    
    JobGraphDict=defaultdict(nested_dict)
    for vid in JobGraph.nodes:
        JobGraphDict[vid]['_cpuutil']=np.array([])
        JobGraphDict[vid]['_oip']=np.array([])
        JobGraphDict[vid]['_oop']=np.array([])
        JobGraphDict[vid]['_tip']=np.array([])
        JobGraphDict[vid]['_top']=np.array([])
        JobGraphDict[vid]['_idletime']=np.array([])
        JobGraphDict[vid]['_bkpstime']=np.array([])
        JobGraphDict[vid]['_busytime']=np.array([])
        JobGraphDict[vid]['_ioread']=np.array([])
        JobGraphDict[vid]['_iowrite']=np.array([])
        JobGraphDict[vid]['_oib']=np.array([])
        JobGraphDict[vid]['_oob']=np.array([])
        JobGraphDict[vid]['parallelism']=JobGraph.nodes[vid]['parallelism']
        JobGraphDict[vid]['name']=JobGraph.nodes[vid]['name']
    
    #------------------------------------# Get profiling data per subtask
    for vid in vertex_ids:    # vid: operator id
        vertix=get_task_vertix_details(jmip, jmpt, job_id, vid)
        #vts=str(vertix['now'])
        _vname=vertix['name']
        vname=_vname.replace(' ','_').replace(',','_').replace(';','_')        # operator name
        #vpall=str(vertix['parallelism'])
        for vtask in vertix['subtasks']:
            ttm=vtask['taskmanager-id']    # taskmanager id of current subtask.  "192.168.1.12:39287-373453"
            tmip=ttm.split(":")[0]
            tid=str(vtask['subtask'])    # subtask id
            # only pull cpu usage for task during profile phase
            #st_cpuutil = -1
            #if (RUNITER==0):
            st_cpuutil = int(str2float(get_prometheus_cpuutil(jmip, tmip))*10)

            st_busytime = str2int(get_task_metrics_details(jmip, jmpt, job_id, vid, tid+'.busyTimeMsPerSecond')[0]['value'])
            st_bkpstime = str2int(get_task_metrics_details(jmip, jmpt, job_id, vid, tid+'.backPressuredTimeMsPerSecond')[0]['value'])
            st_idletime = str2int(get_task_metrics_details(jmip, jmpt, job_id, vid, tid+'.idleTimeMsPerSecond')[0]['value'])
            st_oip = str2int(get_task_metrics_details(jmip, jmpt, job_id, vid, tid+'.numRecordsInPerSecond')[0]['value'])
            st_oop = str2int(get_task_metrics_details(jmip, jmpt, job_id, vid, tid+'.numRecordsOutPerSecond')[0]['value'])
            st_ioread = str2int(get_task_metrics_details(jmip, jmpt, job_id, vid, tid+'.'+_vname+'.rocksdb_bytes_read')[0]['value'])
            st_iowrite = str2int(get_task_metrics_details(jmip, jmpt, job_id, vid, tid+'.'+_vname+'.rocksdb_bytes_written')[0]['value'])
            st_oib = str2int(get_task_metrics_details(jmip, jmpt, job_id, vid, tid+'.numBytesInPerSecond')[0]['value'])
            st_oob = str2int(get_task_metrics_details(jmip, jmpt, job_id, vid, tid+'.numBytesOutPerSecond')[0]['value'])
            if st_busytime==0:
                st_busytime=1    # avoid divide 0 error
            st_tip = st_oip / (st_busytime/1000)
            st_top = st_oop / (st_busytime/1000)

            #if _DEBUG=="d":
            #print("metric per task:  ", vid,'--------'+vname+'_'+tid+"\n", "busytime", st_busytime, "bkpstime", st_bkpstime, "idletime", st_idletime, "oip", st_oip, "oop", st_oop, "tip", st_tip, "top", st_top)
            #print("name:   ", JobGraph.nodes[vid]['name'])
            
            JobGraphDict[vid]['_cpuutil']=np.append(JobGraphDict[vid]['_cpuutil'], st_cpuutil)
            JobGraphDict[vid]['_oip']=np.append(JobGraphDict[vid]['_oip'], st_oip)
            JobGraphDict[vid]['_oop']=np.append(JobGraphDict[vid]['_oop'], st_oop)
            JobGraphDict[vid]['_idletime']=np.append(JobGraphDict[vid]['_idletime'], st_idletime)
            JobGraphDict[vid]['_bkpstime']=np.append(JobGraphDict[vid]['_bkpstime'], st_bkpstime)
            JobGraphDict[vid]['_busytime']=np.append(JobGraphDict[vid]['_busytime'], st_busytime)
            JobGraphDict[vid]['_ioread']=np.append(JobGraphDict[vid]['_ioread'], st_ioread)
            JobGraphDict[vid]['_iowrite']=np.append(JobGraphDict[vid]['_iowrite'], st_iowrite)
            JobGraphDict[vid]['_oib']=np.append(JobGraphDict[vid]['_oib'], st_oib)
            JobGraphDict[vid]['_oob']=np.append(JobGraphDict[vid]['_oob'], st_oob)
            JobGraphDict[vid]['_tip']=np.append(JobGraphDict[vid]['_tip'], st_tip)
            JobGraphDict[vid]['_top']=np.append(JobGraphDict[vid]['_top'], st_top)

    #------------------------------------# Calc optimal parallelism with ds2
    for vid in toposeq:    # calc true input/output rate
        parallelism=JobGraphDict[vid]['parallelism']
        JobGraphDict[vid]['cpuutil']=np.mean(JobGraphDict[vid]['_cpuutil'])
        JobGraphDict[vid]['idletime']=np.mean(JobGraphDict[vid]['_idletime'])    # average of all tasks of an operator
        JobGraphDict[vid]['bkpstime']=np.mean(JobGraphDict[vid]['_bkpstime'])
        JobGraphDict[vid]['busytime']=np.mean(JobGraphDict[vid]['_busytime'])
        JobGraphDict[vid]['oip']=np.sum(JobGraphDict[vid]['_oip'])    # sum of all tasks of an operator
        JobGraphDict[vid]['oop']=np.sum(JobGraphDict[vid]['_oop'])
        JobGraphDict[vid]['oib']=np.sum(JobGraphDict[vid]['_oib'])
        JobGraphDict[vid]['oob']=np.sum(JobGraphDict[vid]['_oob'])
        JobGraphDict[vid]['tip']=np.sum(JobGraphDict[vid]['_tip'])
        JobGraphDict[vid]['top']=np.sum(JobGraphDict[vid]['_top'])
        JobGraphDict[vid]['ioread']=np.sum(JobGraphDict[vid]['_ioread'])
        JobGraphDict[vid]['iowrite']=np.sum(JobGraphDict[vid]['_iowrite'])
        if JobGraphDict[vid]['busytime']<0:    # for source operators, busytime == NaN, true_rate == target_input_rate * source_parallelism
            JobGraphDict[vid]['tip']=0
            for src in srcratelist:
            #    srcname=list(src.keys())[0]
            #    if(srcname in JobGraph.nodes[vid]['name']):
            #JobGraphDict[vid]['top']=src[srcname]*parallelism       # no need for this line
                JobGraphDict[vid]['top']=int(src)*parallelism            
                JobGraphDict[vid]['tops']=JobGraphDict[vid]['top']
        if(JobGraphDict[vid]['oip']>0):
            JobGraphDict[vid]['selectivity']=JobGraphDict[vid]['oop']/JobGraphDict[vid]['oip']
        if JobGraphDict[vid]['tip'] == 0:
            JobGraphDict[vid]['tip'] = 1

    for vid in toposeq:    # calc optimal parallelism for current interval
        parallelism=JobGraphDict[vid]['parallelism']
        selectivity=JobGraphDict[vid]['selectivity']
        innodes=JobGraph.nodes[vid]['innodes']
        if(len(innodes)==0):    # source
            JobGraphDict[vid]['optimalparallelism']=parallelism
        else:
            utops=0    # aggregated target output of its all upstream operator
            for uid in innodes:
                utops+=JobGraphDict[uid]['tops']
            JobGraphDict[vid]['tips']=utops    # target input rate of current operator
            JobGraphDict[vid]['tops']=utops*selectivity    # target output rate of current operator
            JobGraphDict[vid]['optimalparallelism']=math.ceil((utops/(JobGraphDict[vid]['tip']*TARGET_UTIL))*parallelism)
        JobGraph.nodes[vid]['_cpuutil']=np.append(JobGraph.nodes[vid]['_cpuutil'], JobGraphDict[vid]['cpuutil'])
        JobGraph.nodes[vid]['_tops']=np.append(JobGraph.nodes[vid]['_tops'], JobGraphDict[vid]['tops'])
        JobGraph.nodes[vid]['_tips']=np.append(JobGraph.nodes[vid]['_tips'], JobGraphDict[vid]['tips'])
        JobGraph.nodes[vid]['_top']=np.append(JobGraph.nodes[vid]['_top'], JobGraphDict[vid]['top'])
        JobGraph.nodes[vid]['_tip']=np.append(JobGraph.nodes[vid]['_tip'], JobGraphDict[vid]['tip'])
        JobGraph.nodes[vid]['_oop']=np.append(JobGraph.nodes[vid]['_oop'], JobGraphDict[vid]['oop'])
        JobGraph.nodes[vid]['_oip']=np.append(JobGraph.nodes[vid]['_oip'], JobGraphDict[vid]['oip'])
        JobGraph.nodes[vid]['_idletime']=np.append(JobGraph.nodes[vid]['_idletime'], JobGraphDict[vid]['idletime'])
        JobGraph.nodes[vid]['_bkpstime']=np.append(JobGraph.nodes[vid]['_bkpstime'], JobGraphDict[vid]['bkpstime'])
        JobGraph.nodes[vid]['_busytime']=np.append(JobGraph.nodes[vid]['_busytime'], JobGraphDict[vid]['busytime'])
        JobGraph.nodes[vid]['_ioread']=np.append(JobGraph.nodes[vid]['_ioread'], JobGraphDict[vid]['ioread'])
        JobGraph.nodes[vid]['_iowrite']=np.append(JobGraph.nodes[vid]['_iowrite'], JobGraphDict[vid]['iowrite'])
        JobGraph.nodes[vid]['_selectivity']=np.append(JobGraph.nodes[vid]['_selectivity'], JobGraphDict[vid]['selectivity'])
        JobGraph.nodes[vid]['_oob']=np.append(JobGraph.nodes[vid]['_oob'], JobGraphDict[vid]['oob'])
        JobGraph.nodes[vid]['_oib']=np.append(JobGraph.nodes[vid]['_oib'], JobGraphDict[vid]['oib'])
        JobGraph.nodes[vid]['_optimalparallelism']=np.append(JobGraph.nodes[vid]['_optimalparallelism'], JobGraphDict[vid]['optimalparallelism'])
        # _pertaskdict = pd.DataFrame()
        _pertaskdict = {}
        _pertaskdict['_cpuutil'] = JobGraphDict[vid]['_cpuutil']
        _pertaskdict['_top'] = JobGraphDict[vid]['_top']
        _pertaskdict['_tip'] = JobGraphDict[vid]['_tip']
        _pertaskdict['_oop'] = JobGraphDict[vid]['_oop']
        _pertaskdict['_oip'] = JobGraphDict[vid]['_oip']
        _pertaskdict['_oob'] = JobGraphDict[vid]['_oob']
        _pertaskdict['_oib'] = JobGraphDict[vid]['_oib']
        _pertaskdict['_bkpstime'] = JobGraphDict[vid]['_bkpstime']
        _pertaskdict['_busytime'] = JobGraphDict[vid]['_busytime']
        _pertaskdict['_idletime'] = JobGraphDict[vid]['_idletime']
        JobGraph.nodes[vid]['_pertask'].append([_pertaskdict])

        #    if _DEBUG=="d":
        #for vid in JobGraphDict.keys():
        #    print("metric per operator:  ", vid, JobGraphDict[vid])

    #------------------------------------# Average optimal parallelism
    for vid in JobGraph.nodes:
        JobGraph.nodes[vid]['cpuutil']=np.mean(JobGraph.nodes[vid]['_cpuutil'])
        JobGraph.nodes[vid]['tips']=np.mean(JobGraph.nodes[vid]['_tips'])
        JobGraph.nodes[vid]['tops']=np.mean(JobGraph.nodes[vid]['_tops'])
        JobGraph.nodes[vid]['top']=np.mean(JobGraph.nodes[vid]['_top'])
        JobGraph.nodes[vid]['tip']=np.mean(JobGraph.nodes[vid]['_tip'])
        JobGraph.nodes[vid]['oop']=np.mean(JobGraph.nodes[vid]['_oop'])
        JobGraph.nodes[vid]['oip']=np.mean(JobGraph.nodes[vid]['_oip'])
        JobGraph.nodes[vid]['idletime']=np.mean(JobGraph.nodes[vid]['_idletime'])
        JobGraph.nodes[vid]['bkpstime']=np.mean(JobGraph.nodes[vid]['_bkpstime'])
        JobGraph.nodes[vid]['busytime']=np.mean(JobGraph.nodes[vid]['_busytime'])
        JobGraph.nodes[vid]['ioread']=np.mean(JobGraph.nodes[vid]['_ioread'])
        JobGraph.nodes[vid]['iowrite']=np.mean(JobGraph.nodes[vid]['_iowrite'])
        JobGraph.nodes[vid]['selectivity']=np.mean(JobGraph.nodes[vid]['_selectivity'])
        JobGraph.nodes[vid]['oob']=np.mean(JobGraph.nodes[vid]['_oob'])
        JobGraph.nodes[vid]['oib']=np.mean(JobGraph.nodes[vid]['_oib'])
        JobGraph.nodes[vid]['optimalparallelism']=math.ceil(np.mean(JobGraph.nodes[vid]['_optimalparallelism']))
        JobGraph.nodes[vid]['maxoptimalparallelism']=np.amax(JobGraph.nodes[vid]['_optimalparallelism'])
        
    #------------------------------------# Apply?
    for vid in JobGraph.nodes:
        if JobGraph.nodes[vid]['name'] == 'Mapper':
            print(JobGraph.nodes[vid]['name'], 'OptimalParallelism', JobGraph.nodes[vid]['optimalparallelism'])
    
if __name__ == '__main__':
    for i in range(0, 20):
        print(f"ITER {i}")
        ds2(mrate=100000)
        time.sleep(30)
    
