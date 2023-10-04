import subprocess
from subprocess import Popen, PIPE, call
import time
import sys
import os
import signal

f = open("/data/rapl_log.log", "w")
run = True
def handler_stop_signals(signum, frame):
    global run
    run = False
    ## make sure to close file
    if not f.closed:
        f.close()

signal.signal(signal.SIGINT, handler_stop_signals)
signal.signal(signal.SIGTERM, handler_stop_signals)

def runLocalCommandGet(com):
    #p1 = Popen(com, shell=True, stdout=PIPE, stderr=PIPE)
    p1 = Popen(list(filter(None, com.strip().split(' '))), stdout=PIPE)
    return p1.communicate()[0].strip()

output = 0.0

try:
    ## run forever?
    while run:        
        output = float(runLocalCommandGet("/users/hand32/experiment-scripts/cloudlab_setup/c6220/uarch-configure/rapl-read/raplog -m"))
        ## check if energy value is a valid one
        if output > 0.0 and output < 1000.0:
            f.write(str(output)+"\n")
            f.flush()
        else:
            time.sleep(1)
except Exception as e:
    run = False
    print(e)
    ## make sure to close file
    if not f.closed:
        f.close()
