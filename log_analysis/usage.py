#!/usr/bin/env python2.7

import matplotlib
matplotlib.use('Agg')
from matplotlib import rcParams, cm
from matplotlib import pyplot as plt
import numpy as np
from time import strptime, time, mktime
import MySQLdb as sql

db = sql.connect(db='bird_watcher', user='snarayan')
cursor = db.cursor()

data = {} # dataset : access_volume
totals = {} # dataset : total_volume

cursor.execute('SELECT last_access FROM files ORDER BY last_access ASC LIMIT 1')
start = cursor.fetchall()[0][0]
end = int(time())
STEPS = 1000
times = np.linspace(start, end, STEPS)
step = times[1] - times[0]
sigma2 = np.power(10 * step, 2)
kernel = np.exp(-np.power(np.linspace(start-end, end-start, 2*STEPS), 2) / sigma2)

cursor.execute('SELECT path,last_access,mbytes FROM files')
for p,a,s in cursor:
    s /= 1e3
    ds = p.split('/')[-3]
    ds += '/'
    ds += p.split('/')[-2].split('+')[0]
    if ds not in data:
        data[ds] = np.zeros(times.shape)
        totals[ds] = 0
    totals[ds] += s
    arr = data[ds]
    shift = min(int((a - start) / step), STEPS)
    arr += (s * kernel[STEPS-shift:2*STEPS-shift])

ordered = sorted(totals.iteritems(), key=lambda x : x[1], reverse=True)
order = [x[0] for x in ordered[:10]] + ['Other']
sizes = [x[1] for x in ordered[:10]]
sizes.append(sum(totals.values()) - sum(sizes))
data['Other'] = np.zeros(times.shape)
for k,v in data.iteritems():
    if k in order:
        continue 
    data['Other'] += v 

s2h = 1./3600
times = s2h * (times - end)

fig, ax1 = plt.subplots()
for k,s in zip(order, sizes):
    ax1.plot(times, data[k], label='%s (%.2f GB)'%(k,s)) 
ax1.set_xlabel('Access time [H]')
ax1.set_ylabel('Volume [TB]')
#ax1.set_ylim(ymin=0)
ax1.set_yscale('symlog')
#ax1.set_xscale('symlog')
plt.legend(loc=0, fancybox=True, prop={'size':6})

fig.tight_layout()

out = '/home/snarayan/public_html/figs/thesis/access'
plt.savefig(out+'.png', dpi=200)
plt.savefig(out+'.pdf')
