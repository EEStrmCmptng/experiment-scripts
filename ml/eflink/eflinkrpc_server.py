import time
import asyncio
from concurrent import futures
import logging

import grpc
import eflinkrpc_pb2
import eflinkrpc_pb2_grpc

from subprocess import Popen, PIPE, call
from ax.service.ax_client import AxClient, ObjectiveProperties
import pandas as pd
import numpy as np


DEFAULT_IP = 'localhost'
DEFAULT_PORT = 10000
MAPPERIP = '10.10.1.3'

#logging.basicConfig(level=logging.INFO,
#                    format='%(asctime)s | %(levelname)s | %(filename)-10s | %(funcName)-20s || %(message)s',
                    #format='%(asctime)s | %(levelname)-6s | %(filename)-10s | %(funcName)-20s || %(message)s',
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
# create file handler which logs even debug messages
fh = logging.FileHandler(f"server.log")
fh.setLevel(logging.INFO)
# create console handler with a higher log level
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)

# create formatter and add it to the handlers
formatter = logging.Formatter('%(asctime)s | %(levelname)s | %(filename)-10s | %(funcName)-20s || %(message)s',
                              datefmt='%m-%d %H:%M:%S')
fh.setFormatter(formatter)
ch.setFormatter(formatter)
# add the handlers to the logger
logger.addHandler(fh)
logger.addHandler(ch)

class GRPCUtility(eflinkrpc_pb2_grpc.UtilityMessagingServicer):
    def __init__(self,
                 oqueue: asyncio.Queue):
        self.oqueue = oqueue
        super(eflinkrpc_pb2_grpc.UtilityMessagingServicer, self).__init__()
        
    def PublishUtility(self, request, context):
        #logger.info(f"{request.srcrps}, {request.power}")
        self.oqueue.put_nowait(request)
        return eflinkrpc_pb2.UtilityAck(retcode=0)

class GRPCServer():
    def __init__(self,
                 oqueue: asyncio.Queue,
                 sport: int):
        self.oqueue = oqueue
        self.sport = sport
        self.server = grpc.aio.server(futures.ThreadPoolExecutor(max_workers=10))
        eflinkrpc_pb2_grpc.add_UtilityMessagingServicer_to_server(
            GRPCUtility(self.oqueue), self.server)
        self.server.add_insecure_port(f'[::]:{self.sport}')
        
    async def grpcloop(self):
        logger.info(f"Starts to wait for events....")
        await self.server.start()
        await self.server.wait_for_termination()

    def __del__(self):
        self.server.stop(grace=0)

class BayOptFlink:
    def __init__(self,
                 oqueue: asyncio.Queue):
        self.oqueue = oqueue
        self.ax_client = AxClient(enforce_sequential_optimization=False, verbose_logging=True)

        """ Setup ITR-DVFS tuning """
        self.ieth = self.runRemoteCommandGet(f"ifconfig | grep -B1 {MAPPERIP} | grep -o '^\w*'", MAPPERIP).decode()
        ret = self.runRemoteCommandGet("~/experiment-scripts/cloudlab_setup/c6220/set_dvfs.sh userspace", MAPPERIP)
        logger.info(ret)
        
        """ Setup Axe experiment """
        self.pname = "BayOptFlink"
        #itr_vals = [*range(2, 1000, 2)]
        #dvfs_vals = [*range(3072, 6656, 1)]        
        self.ax_client.create_experiment(
            name=self.pname,
            parameters=[
                {
                    "name": "itr",
                    "type": "range",
                    "value_type": "int",  # Optional, defaults to inference from type of "bounds".
                    "log_scale": False,  # Optional, defaults to False.
                    "bounds": [2, 1000],
                },
                {
                    "name": "dvfs",
                    "type": "range",
                    "value_type": "int",
                    "log_scale": False,
                    "bounds": [3072, 6656],
                },
            ],
            objectives={self.pname: ObjectiveProperties(minimize=True)},
            choose_generation_strategy_kwargs={"max_parallelism_override": 16},
        )
        
    def int2hexstr(self, int_in):
        s = str(hex(int_in))
        s2 = s[2:]
        if len(s2) == 3:
            s2 = "0"+s2
        assert len(s2) == 4
        return s2

    def runRemoteCommandGet(self, com, server):
        logger.info(f"ssh {server} {com}")
        p1 = Popen(["ssh", server, com], stdout=PIPE)
        return p1.communicate()[0].strip()

    def setITR(self, itr):
        self.runRemoteCommandGet(f"ethtool -C {self.ieth} rx-usecs {itr}", MAPPERIP)

    def setDVFS(self, dvfs):
        v = "0x10000"+dvfs
        self.runRemoteCommandGet(f"sudo wrmsr -a 0x199 {v}", MAPPERIP)

    def empty_queue(self):
        if self.oqueue.empty():
            return
        ## drain the number of existing items in the queue        
        nitems = self.oqueue.qsize()
        for i in range(0, nitems):
            self.oqueue.get_nowait()
            self.oqueue.task_done()
        logger.info(f"Drained {nitems} from queue.")
    
    async def evalflink(self, params):
        reward = 0.0
        
        # get and set itr-dvfs
        itr = params['itr']
        dvfs = self.int2hexstr(int(params['dvfs']))
        self.setITR(itr)
        self.setDVFS(dvfs)

        ## sleep 10 seconds for settings to take effect
        logger.info("Sleep 10 seconds for settings to take effect.")
        time.sleep(10)
        ## quickly drain all (old) data in the queue - not needed since grpc client is blocked till we ack
        ## self.empty_queue()                

        arrpkge = []
        arrperf = []
        logger.info("Fetch 10 rounds of data.")
        for i in range(0, 10):
            request = await self.oqueue.get()
            logger.info(f"Fetching {i}: {round(request.srcrps, 3)}, {round(request.power, 3)}")
            arrperf.append(float(request.srcrps))
            arrpkge.append(float(request.power))

        ## ignore first 2 entries
        pkge = np.mean(arrpkge[2:])
        perf = np.mean(arrperf[2:])
        
        ## if the source cannot keep up with rate - less than 95% 
        if perf < 0.95:
            reward = 200.0
        else:
            reward = pkge            
        logger.info(f"ITR:{itr} DVFS:{dvfs} MeanPower:{round(pkge,3)} MeanPerf:{round(perf,3)} Reward:{round(reward, 3)}")
        res = {
            self.pname: (reward, 0.0)
        }
        return res
        
    async def bloop(self, it):
        for i in range(0, it):
            parameterization, trial_index = self.ax_client.get_next_trial()
            res = await self.evalflink(parameterization)
            self.ax_client.complete_trial(trial_index=trial_index, raw_data=res)
        best_parameters, values = self.ax_client.get_best_parameters()
        logger.info(f"best_parameters: {best_parameters}")
        logger.info(self.ax_client.get_trace())
        logger.info(f"**** {self.pname} EXPERIMENT COMPLETE *******")
                    
if __name__ == "__main__":
    event_queue = asyncio.Queue()
    event_loop = asyncio.get_event_loop()
    event_source = GRPCServer(oqueue=event_queue, sport=DEFAULT_PORT)
    boflink = BayOptFlink(oqueue=event_queue)
    
    event_loop.create_task(event_source.grpcloop())
    try:
        event_loop.run_until_complete(boflink.bloop(60))
    finally:
        event_loop.close()
