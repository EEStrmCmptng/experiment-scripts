import subprocess
from subprocess import Popen, PIPE, call
import time
import sys
import os
import signal

'''
Based on: https://docs.kernel.org/hwmon/xgene-hwmon.html

[handong@abeast1-sesa rapl_service]$ grep "" /sys/class/hwmon/hwmon*/*_{label,input}
/sys/class/hwmon/hwmon0/temp1_label:loc1
/sys/class/hwmon/hwmon1/power1_label:CPU power
/sys/class/hwmon/hwmon1/power2_label:IO power
/sys/class/hwmon/hwmon1/temp1_label:SoC Temperature
/sys/class/hwmon/hwmon0/temp1_input:34000
/sys/class/hwmon/hwmon1/power1_input:7178000
/sys/class/hwmon/hwmon1/power2_input:12141000
/sys/class/hwmon/hwmon1/temp1_input:32000

"powersave" governor
  current policy: frequency should be within 2.00 GHz and 3.00 GHz.
                  The governor "powersave" may decide which speed to use
                  within this range.
  current CPU frequency: Unable to call hardware
  current CPU frequency: 2.00 GHz (asserted by call to kernel)

40.112 + 16.918 = 57.03 J
40.279 + 16.92 = 57.199000000000005 J
40.447 + 16.827 = 57.274 J
40.517 + 16.888 = 57.405 J

"performance" governor
  current policy: frequency should be within 2.00 GHz and 3.00 GHz.
                  The governor "performance" may decide which speed to use
                  within this range.
  current CPU frequency: Unable to call hardware
  current CPU frequency: 3.00 GHz (asserted by call to kernel)
90.45 + 17.011 = 107.461 J
90.21 + 16.981 = 107.191 J
90.225 + 16.9 = 107.125 J
90.09 + 16.917 = 107.007 J
90.055 + 16.921 = 106.976 J
90.245 + 16.869 = 107.114 J
90.3 + 16.947 = 107.247 J
90.445 + 16.873 = 107.318 J


"userspace" governor
[handong@abeast1-sesa ~]$ sudo cpupower frequency-set -f 2.49GHz
[handong@abeast1-sesa ~]$ cpupower frequency-info
current policy: frequency should be within 2.00 GHz and 3.00 GHz.
                  The governor "userspace" may decide which speed to use
                  within this range.
  current CPU frequency: Unable to call hardware
  current CPU frequency: 2.49 GHz (asserted by call to kernel)
47.864 + 16.76 = 64.624 J
47.617 + 16.858 = 64.475 J
47.622 + 16.707 = 64.32900000000001 J
47.764 + 16.888 = 64.652 J
47.704 + 16.896 = 64.6 J
48.042 + 16.838 = 64.88 J

'''

#f = open("/data/rapl_log.log", "w")
run = True
def handler_stop_signals(signum, frame):
    global run
    run = False
    ## make sure to close file
    #if not f.closed:
    #    f.close()

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
        power1UW = float(runLocalCommandGet("cat /sys/class/hwmon/hwmon1/power1_input")) / 1000000.0
        #print(power1UW)
        power2UW = float(runLocalCommandGet("cat /sys/class/hwmon/hwmon1/power2_input")) / 1000000.0
        #print(power2UW)
        print(f"{power1UW} + {power2UW} = {power1UW+power2UW} J")
        time.sleep(1)
        #output = float(runLocalCommandGet("/users/hand32/bayop/uarch-configure/rapl-read/raplog -m"))
        ## check if energy value is a valid one
        #if output > 0.0 and output < 1000.0:
        #    f.write(str(output)+"\n")
        #    f.flush()
        #else:
        #    time.sleep(1)
except Exception as e:
    run = False
    print(e)
    ## make sure to close file
    #if not f.closed:
    #    f.close()
