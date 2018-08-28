from werkzeug.exceptions import HTTPException
from flask import request, Flask, abort, g
from os import system, path, getenv
from subprocess import check_output
import json
import MySQLdb as sql 
from time import time 

basedir = getenv('FLASK_BASE_DIR') 
app = Flask('')

class BadInput(HTTPException):
    code = 400
    description = '<p>Malformed input.</p>'

class DBError(HTTPException):
    code = 500
    description = '<p>DB Error.</p>'

def timed(fn):
    def _f():
        start = time()
        x = fn()
        print fn.func_name,':',time()-start,'s'
        return x
    _f.func_name = fn.func_name
    return _f

# actions to be taken on push to Panda* repositories
# called through GitHub webhook
@app.route('/push', methods=['POST'])
@timed
def push():
    doxy_basedir = basedir + '/doxygen/repos/'
    data = request.get_json()
    repo = data['repository']['git_url'].split('/')[-1].replace('.git','')
    giturl = data['repository']['clone_url']
    # actual process is off-loaded to bash script to run asynchronously
    cmd = 'bash %s/doxygen/run.sh %s %s %s'%(basedir, basedir, repo, giturl)
    print cmd 
    system(cmd + ' &')
    return 'Success!\n'


# manage condor tasks through MySQLdb 
def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sql.connect(db='bird_watcher', user='snarayan')
    return db

def get_cursor():
    return get_db().cursor()

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def query(cmd, args=()):
    try:
        cur = get_cursor()
        cur.execute(cmd, args)
        rv = cur.fetchall()
        cur.close()
        return rv
    except Exception as e:
        print str(e)
        raise DBError

def geo(hostname):
    try:
        if hostname.endswith('mit.edu'):
            if hostname.startswith('t3'):
                return (42.364601,-71.102798)
            elif 'bat' in hostname:
                return (42.364601,-71.102798)
        cmd = ['geoiplookup', hostname]
        lines = check_output(cmd, shell=False).strip().split('\n')
        if len(lines) == 0 or "can't resolve" in lines[0] or 'not found' in lines[0]:
            return None, None 
        ll = lines[1].replace(',','').split()
        return float(ll[-4]), float(ll[-3])
    except:
        print hostname
        print lines 
        return 0,0

def get_host_id(hostname):
    r = query('SELECT `id` FROM nodes WHERE host = %s', (hostname,))
    if len(r) == 0:
        lat,lon = geo(hostname)
        get_cursor().execute('INSERT INTO nodes (host,lat,lon) VALUES (%s,%s,%s)', [hostname, lat, lon])
        get_db().commit()
        r = query('SELECT `id` FROM nodes WHERE host = %s', (hostname,))
    return r[0][0]

def insert_missing_hosts():
    hosts = list(set(query('SELECT `host` FROM jobs')))
    for h in hosts:
        if h is not None:
            get_host_id(h)


@app.route('/condor/query', methods=['GET'])
@timed
def condor_query():
    # query db and return
    task = request.args.get('task')
    if not task:
        raise BadInput
    where = 'task = %s'
    args=[task]
    jid = request.args.get('job_id')
    if jid:
        where += ' AND job_id = %s'
        args.append(jid)
    payload = query('SELECT `arg`, `job_id`, `timestamp`, `starttime`, `host`, `exit_code` FROM jobs WHERE %s;'%where, args)
    return json.dumps(payload)

@app.route('/condor/done', methods=['POST'])
@timed
def condor_done():
    # use JSON payload to fill table
    data = request.get_json()
    try:
        task = data['task']
        timestamp = data['timestamp']
        job_id = data['job_id']
        exit_code = data.get('exit_code', 0)
        # see if we know the job
        if len(query('SELECT `job_id` FROM jobs WHERE task = %s AND job_id = %s', (task, job_id))):
            for arg in data['args']:
                get_cursor().execute('UPDATE jobs SET timestamp = %s, exit_code = %s WHERE task = %s AND job_id = %s AND arg = %s', 
                                 (timestamp, exit_code, task, job_id, arg))
            get_db().commit()
            return str(len(data['args'])) + '\n'
        else:
            records = [(task, arg, job_id, timestamp, None, None, exit_code) for arg in data['args']]
            get_cursor().executemany('INSERT INTO jobs (task,arg,job_id,timestamp,starttime,host_id,exit_code) VALUES (%s,%s,%s,%s,%s,%s,%s)', records)
            get_db().commit()
            return str(len(records))+'\n'
    except KeyError:
        raise BadInput
    except sql.Error as e:
        print str(e)
        raise DBError

@app.route('/condor/start', methods=['POST'])
@timed
def condor_start():
    # use JSON payload to fill table
    data = request.get_json()
    try:
        task = data['task']
        starttime = data['starttime']
        host = data['host']
        host_id = get_host_id(host)
        job_id = data['job_id']
        # see if we know the job, i.e. something that got pre-empted and restarted
        if False: # len(query('SELECT `job_id` FROM jobs WHERE task = %s AND job_id = %s', (task, job_id))):
            for arg in data['args']:
                get_cursor().execute(
                        'UPDATE jobs SET starttime = %s, host_id = %s WHERE task = %s AND job_id = %s AND arg = %s', 
                         (starttime, host_id, task, job_id, arg)
                    )
            get_db().commit()
            return str(len(data['args'])) + '\n'
        else:
            records = [(task, arg, job_id, None, starttime, host_id) for arg in data['args']]
            get_cursor().executemany(
                    'INSERT INTO jobs (task,arg,job_id,timestamp,starttime,host_id) VALUES (%s,%s,%s,%s,%s,%s)', 
                    records)
            get_db().commit()
            return str(len(records))+'\n'
        get_latlon(host)
    except KeyError:
        raise BadInput
    except sql.Error as e:
        print str(e)
        raise DBError

@app.route('/condor/clean', methods=['POST'])
@timed
def condor_clean():
    # use JSON payload to fill table
    data = request.get_json()
    try:
        task = data['task']
        if 'job_id' in data:
            job_id = data['job_id']
            get_cursor().execute('DELETE FROM jobs WHERE task=%s AND job_id=%s', (task,job_id))
        else:
            get_cursor().execute('DELETE FROM jobs WHERE task=%s', (task,))
        get_db().commit()
        return 'Cleaned\n'
    except KeyError:
        raise BadInput
    except sql.Error:
        print str(e)
        raise DBError
