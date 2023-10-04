import subprocess
from subprocess import Popen, PIPE, call
import time
import sys
import os
import signal

'''
Based on: 
https://github.com/amd/amd_energy
https://www.kernel.org/doc/html/v5.9/hwmon/amd_energy.html

hand32@server:~/bayop/rapl_service$ grep "" /sys/class/hwmon/hwmon2/*_{label,input}
/sys/class/hwmon/hwmon2/energy10_label:Ecore009
/sys/class/hwmon/hwmon2/energy11_label:Ecore010
/sys/class/hwmon/hwmon2/energy12_label:Ecore011
/sys/class/hwmon/hwmon2/energy13_label:Ecore012
/sys/class/hwmon/hwmon2/energy14_label:Ecore013
/sys/class/hwmon/hwmon2/energy15_label:Ecore014
/sys/class/hwmon/hwmon2/energy16_label:Ecore015
/sys/class/hwmon/hwmon2/energy17_label:Ecore016
/sys/class/hwmon/hwmon2/energy18_label:Ecore017
/sys/class/hwmon/hwmon2/energy19_label:Ecore018
/sys/class/hwmon/hwmon2/energy1_label:Ecore000
/sys/class/hwmon/hwmon2/energy20_label:Ecore019
/sys/class/hwmon/hwmon2/energy21_label:Ecore020
/sys/class/hwmon/hwmon2/energy22_label:Ecore021
/sys/class/hwmon/hwmon2/energy23_label:Ecore022
/sys/class/hwmon/hwmon2/energy24_label:Ecore023
/sys/class/hwmon/hwmon2/energy25_label:Ecore024
/sys/class/hwmon/hwmon2/energy26_label:Ecore025
/sys/class/hwmon/hwmon2/energy27_label:Ecore026
/sys/class/hwmon/hwmon2/energy28_label:Ecore027
/sys/class/hwmon/hwmon2/energy29_label:Ecore028
/sys/class/hwmon/hwmon2/energy2_label:Ecore001
/sys/class/hwmon/hwmon2/energy30_label:Ecore029
/sys/class/hwmon/hwmon2/energy31_label:Ecore030
/sys/class/hwmon/hwmon2/energy32_label:Ecore031
/sys/class/hwmon/hwmon2/energy33_label:Esocket0
/sys/class/hwmon/hwmon2/energy3_label:Ecore002
/sys/class/hwmon/hwmon2/energy4_label:Ecore003
/sys/class/hwmon/hwmon2/energy5_label:Ecore004
/sys/class/hwmon/hwmon2/energy6_label:Ecore005
/sys/class/hwmon/hwmon2/energy7_label:Ecore006
/sys/class/hwmon/hwmon2/energy8_label:Ecore007
/sys/class/hwmon/hwmon2/energy9_label:Ecore008
/sys/class/hwmon/hwmon2/energy10_input:48340026
/sys/class/hwmon/hwmon2/energy11_input:51727050
/sys/class/hwmon/hwmon2/energy12_input:51739791
/sys/class/hwmon/hwmon2/energy13_input:47502441
/sys/class/hwmon/hwmon2/energy14_input:61702819
/sys/class/hwmon/hwmon2/energy15_input:47778854
/sys/class/hwmon/hwmon2/energy16_input:65240692
/sys/class/hwmon/hwmon2/energy17_input:112769165
/sys/class/hwmon/hwmon2/energy18_input:50512054
/sys/class/hwmon/hwmon2/energy19_input:118792984
/sys/class/hwmon/hwmon2/energy1_input:152602874
/sys/class/hwmon/hwmon2/energy20_input:50243118
/sys/class/hwmon/hwmon2/energy21_input:59646118
/sys/class/hwmon/hwmon2/energy22_input:54683532
/sys/class/hwmon/hwmon2/energy23_input:48957321
/sys/class/hwmon/hwmon2/energy24_input:56657272
/sys/class/hwmon/hwmon2/energy25_input:49747650
/sys/class/hwmon/hwmon2/energy26_input:210032440
/sys/class/hwmon/hwmon2/energy27_input:56520034
/sys/class/hwmon/hwmon2/energy28_input:59389007
/sys/class/hwmon/hwmon2/energy29_input:49548583
/sys/class/hwmon/hwmon2/energy2_input:53702835
/sys/class/hwmon/hwmon2/energy30_input:105528564
/sys/class/hwmon/hwmon2/energy31_input:89304870
/sys/class/hwmon/hwmon2/energy32_input:63305313
/sys/class/hwmon/hwmon2/energy33_input:56804549301
/sys/class/hwmon/hwmon2/energy3_input:109954086
/sys/class/hwmon/hwmon2/energy4_input:50308013
/sys/class/hwmon/hwmon2/energy5_input:51979263
/sys/class/hwmon/hwmon2/energy6_input:114264663
/sys/class/hwmon/hwmon2/energy7_input:49363388
/sys/class/hwmon/hwmon2/energy8_input:137156768
/sys/class/hwmon/hwmon2/energy9_input:54914215

https://www.amd.com/system/files/TechDocs/24593.pdf

P-State Current Limit Register:
rdmsr -a 0xc0010061 -> 0x20
P-state max value == 2, P-state min value == 0

0xc0010062: P-State Control Register
0x0 = 2.35GHz
0x1 = 2.00GHz
0x2 = 1.50GHZ
wrmsr -a 0xc0010062 0x1
'''

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
        ## socket energy input is in micro Joules
        startJ = float(runLocalCommandGet("cat /sys/class/hwmon/hwmon2/energy33_input")) / 1000000.0

        #cores=[]
        #for i in range (1, 33):
        #    cores.append(float(runLocalCommandGet(f"cat /sys/class/hwmon/hwmon2/energy{i}_input")) / 1000000.0)
            
        time.sleep(1)
        endJ = float(runLocalCommandGet("cat /sys/class/hwmon/hwmon2/energy33_input")) / 1000000.0
        #for i in range (1, 33):
        #    cores[i-1] = (float(runLocalCommandGet(f"cat /sys/class/hwmon/hwmon2/energy{i}_input")) / 1000000.0) - cores[i-1]
        output = endJ-startJ
        ## check if energy value is a valid one
        if output > 0.0 and output < 1000.0:
            f.write(str(output)+"\n")
            f.flush()
        
        
except Exception as e:
    run = False
    print(e)
    ## make sure to close file
    if not f.closed:
        f.close()
