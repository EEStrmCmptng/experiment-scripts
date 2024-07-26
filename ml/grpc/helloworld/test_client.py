import grpc
import helloworld_pb2
import helloworld_pb2_grpc

DEFAULT_IP = 'localhost'
DEFAULT_PORT = 10000

with grpc.insecure_channel(f'{DEFAULT_IP}:{DEFAULT_PORT}') as channel:
    stub = helloworld_pb2_grpc.GreeterStub(channel)
    ret = stub.SayHello(helloworld_pb2.HelloRequest(name="you"))
    print(f"Got retcode {ret}")
