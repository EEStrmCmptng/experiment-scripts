import os
import pandas as pd
import sys

flinklogdir = sys.argv[1]


def parseFinkMetrics(flinklogdir):
    fnames=os.listdir(flinklogdir)
    explist=[]
    for fn in fnames:
        if('Operator_' in fn):
            kwlist={'numRecordsInPerSecond':[], 'numRecordsOutPerSecond':[], 'busyTimeMsPerSecond':[], 'backPressuredTimeMsPerSecond':[]}
            ff=open(flinklogdir+'/'+fn, 'r').readlines()
            fcnt=0
            for _ll, _lc in enumerate(ff):
                for lc in _lc.split('; '):
                    for kw in kwlist.keys():
                        if(kw in lc):
                            ldict=eval(lc.replace('[','').replace(']',''))
                            kwlist[kw].append(float(ldict['value']))
                            fcnt+=1
            print(fn,fcnt)
            exp=dict()
            exp['name']=fn
            for kw in kwlist.keys():
                exp[kw+'_avg']=np.average(np.nan_to_num(np.array(kwlist[kw])))
                print(kw, kwlist[kw])
            explist.append(exp)
    expdf=pd.DataFrame(explist).fillna(0)
    # expdf['true_input_rate']=expdf['numRecordsInPerSecond_avg']/(expdf['busyTimeMsPerSecond_avg']/1000)
    # expdf=expdf.sort_values(by = ['numRecordsOutPerSecond_avg', 'latency_avg', 'latency_max'], ascending = [True, True, True])
    print(expdf)



