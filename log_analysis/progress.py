#!/usr/bin/env python2.7

import matplotlib
matplotlib.use('Agg')
from matplotlib import rcParams, cm
from matplotlib import pyplot as plt
import numpy as np
from time import strptime, time, mktime
from math import floor 

print 'open file'
flog =  open('/local/snarayan/logs/flask.log','r')

BIN = 3600
s2h = 1./3600
apis = ['start', 'done', 'query', 'clean']
data = {'N':[],
        't':[]}
for a in apis:
    data[a] = []

def get_line():
    i = 0
    while True:
#        if i == 100:
#            raise StopIteration 
        line = next(flog).strip()
        i += 1
        yield line

get = get_line()

t = None 
print 'loop'
try:
    while True:
        line = next(get)
        if not any([line.startswith('condor_'+a) for a in apis]):
            continue 
        line2 = next(get)
        try:
            line2 = line2.split('[')[1].split(' ')[0]
            t_ = mktime(strptime(line2, '%d/%b/%Y:%H:%M:%S'))
        except:
            print line
            print line2
            t_ = t 
        if t is None or t_ > t + BIN:
            t = t_
            data['t'].append(t)
            data['N'].append(0)
            for a in apis:
                data[a].append(0)
        data['N'][-1] += 1
        a = line.split(' ')[0].replace('condor_','')
        data[a][-1] += float(line.split(' ')[2])
except StopIteration as e :
    pass

for k,v in data.iteritems():
    data[k] = np.array(v)

data['t'] -= time()
data['t'] *= s2h 
for a in apis:
    data[a] /= data['N']

fig, ax1 = plt.subplots()
ax1.plot(data['t'], data['N'], 'm-')
ax1.set_xlabel('Time [H]')
ax1.set_ylabel('Number of queries / Hour', color='m')
ax1.tick_params('y', colors='m')

ax2 = ax1.twinx()
for a in apis:
    ax2.plot(data['t'], data[a], label=a)
ax2.set_ylabel('Average query time [s]')

plt.legend(loc=0)
fig.tight_layout()

out = '/home/snarayan/public_html/figs/thesis/bird_watcher'
plt.savefig(out+'.png', dpi=200)
plt.savefig(out+'.pdf')
