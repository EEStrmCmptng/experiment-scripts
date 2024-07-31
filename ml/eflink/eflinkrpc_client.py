import argparse
import grpc
import eflinkrpc_pb2
import eflinkrpc_pb2_grpc
import logging
import time
import os
import subprocess
from subprocess import Popen, PIPE, call

DEFAULT_IP = 'localhost'
DEFAULT_PORT = 10000

#logging.basicConfig(level=logging.INFO,
#                    format='%(asctime)s | %(levelname)-6s | %(name)-40s || %(message)s',
#                    datefmt='%m-%d %H:%M:%S')

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
# create file handler which logs even debug messages
fh = logging.FileHandler(f"client.log")
fh.setLevel(logging.INFO)
# create console handler with a higher log level
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)

# create formatter and add it to the handlers
formatter = logging.Formatter('%(asctime)s | %(levelname)-6s | %(name)-40s || %(message)s',
                            datefmt='%m-%d %H:%M:%S')
fh.setFormatter(formatter)
ch.setFormatter(formatter)
# add the handlers to the logger
logger.addHandler(fh)
logger.addHandler(ch)

def runGetCmd(cmd):
    #print('------------------------------------------------------------')
    #print(cmd)
    res=os.popen(cmd).read()
    return res
    #print('------------------------------------------------------------')

def parseargs():
    parser = argparse.ArgumentParser(description='FLINK grpc server')
    parser.add_argument('--log', '-l', type=str, help='log location')
    parser.add_argument('--mapper', '-n', type=str, default="10.10.1.3", help='ip of mapper node')
    args = parser.parse_args()
    return args

def run_client(args):
    logger.info(f"args: {args}")
    while True:
        try:
            ## get data
            s = float(runGetCmd(f"tail -n 1 {args.log}/SourceRecordsOutAvg.log"))
            p = float(runGetCmd(f"ssh {args.mapper} tail -n 1 /tmp/rapl.log").split(" ")[0])
            logger.info(f"{s}, {p}")
        except Exception as e:
            logger.info(f"{str(e)}")
            break
        
        with grpc.insecure_channel(f'{DEFAULT_IP}:{DEFAULT_PORT}') as channel:
            stub = eflinkrpc_pb2_grpc.UtilityMessagingStub(channel)
            ret = stub.PublishUtility(eflinkrpc_pb2.UtilityMessage(srcrps=s, power=p))
        logger.info(f"Got retcode {ret}")
        time.sleep(1)

if __name__ == '__main__':
    args = parseargs()
    run_client(args)
