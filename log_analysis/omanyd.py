#!/usr/bin/env python2.7

import matplotlib
matplotlib.use('Agg')
from matplotlib import rcParams, cm
from matplotlib import pyplot as plt
import numpy as np
from time import strptime, time, mktime
from math import floor 
from re import sub 

print 'open file'
flog =  open('/local/snarayan/logs/xoted.log','r')

s2h = 1./3600

data = {'v':[],
        'd':[],
        't':[],
        'x':[],
        }

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
        if 'threshold' not in line:
            continue
        x = mktime(strptime(line.split(',')[0], '%Y-%m-%d %H:%M:%S'))
        t = float(line.split()[-1].replace('GB','')) / 1e3
        line = next(get)
        line = next(get)
        v = float(sub('GB.*', '', sub('.*volume ', '', line))) / 1e3
        while True:
            line = next(get)
            if 'removed' not in line:
                break
        d = int(sub(' files.*','',sub('.*cleaning ','', line)))

        data['v'].append(v)
        data['x'].append(x)
        data['t'].append(t)
        data['d'].append(d)
except StopIteration as e :
    pass

for k,v in data.iteritems():
    data[k] = np.array(v)

data['x'] -= time()
data['x'] *= s2h 

fig, ax1 = plt.subplots()
ax1.plot(data['x'], data['t'], label='Threshold')
ax1.plot(data['x'], data['v'], label='Used')
ax1.set_xlabel('Time [H]')
ax1.set_ylabel('Volume [TB]')
ax1.set_ylim(ymin=0)
ax1.set_xscale('symlog')
plt.legend(loc=3, fancybox=True, framealpha=0.5)

ax2 = ax1.twinx()
ax2.plot(data['x'], data['d'], 'm-', label='Files deleted')
ax2.set_ylabel('Number of files', color='m')
ax2.tick_params('y', colors='m')
plt.legend(loc=4, fancybox=True, framealpha=0.5)

fig.tight_layout()

out = '/home/snarayan/public_html/figs/thesis/omanyd'
plt.savefig(out+'.png', dpi=200)
plt.savefig(out+'.pdf')
