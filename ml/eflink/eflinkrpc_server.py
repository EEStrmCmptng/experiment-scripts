import time
import asyncio
from concurrent import futures
import logging

import grpc
import eflinkrpc_pb2
import eflinkrpc_pb2_grpc

DEFAULT_IP = 'localhost'
DEFAULT_PORT = 10000

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s | %(levelname)s | %(filename)-10s | %(funcName)-20s || %(message)s',
                    #format='%(asctime)s | %(levelname)-6s | %(filename)-10s | %(funcName)-20s || %(message)s',
                    datefmt='%m-%d %H:%M:%S')
logger = logging.getLogger(__name__)

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
        
    async def bloop(self):
        while True:
            logger.info(f"Waiting for event.")
            request = await self.oqueue.get()
            logger.info(f"{request.srcrps}, {request.power}")

if __name__ == "__main__":
    event_queue = asyncio.Queue()
    event_loop = asyncio.get_event_loop()
    event_source = GRPCServer(oqueue=event_queue, sport=DEFAULT_PORT)
    boflink = BayOptFlink(oqueue=event_queue)
    
    event_loop.create_task(event_source.grpcloop())
    try:
        event_loop.run_until_complete(boflink.bloop())
    finally:
        event_loop.close()

    
"""
class UtilityMessaging(eflinkrpc_pb2_grpc.UtilityMessagingServicer):
    def PublishUtility(self, request, context):
        logger.info(f"{request.srcrps}, {request.power}")
        return eflinkrpc_pb2.UtilityAck(retcode=0)

def serve():
    port = str(DEFAULT_PORT)
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    eflinkrpc_pb2_grpc.add_UtilityMessagingServicer_to_server(UtilityMessaging(), server)
    server.add_insecure_port("[::]:" + port)
    server.start()
    logger.info(f"Server started, listening on {port}")
    server.wait_for_termination()

"""
