from werkzeug.exceptions import HTTPException
from flask import request, Flask, abort, g
from os import system, path, getenv
from subprocess import check_output
import sqlite3
import json

basedir = getenv('FLASK_BASE_DIR') 
app = Flask('')

class BadInput(HTTPException):
    code = 400
    description = '<p>Malformed input.</p>'

class DBError(HTTPException):
    code = 500
    description = '<p>DB Error.</p>'

# actions to be taken on push to Panda* repositories
# called through GitHub webhook
@app.route('/push', methods=['POST'])
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


# manage condor tasks through an sqlite3 db
dbpath = basedir + '/condor/tasks.sqlite'
exists = path.isfile(dbpath)

def get_db():
    global exists
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(dbpath, timeout=30) # sometimes we need long concurrency
        if not exists:
            schema = str(open(basedir+'/condor/schema.sql').read()).strip()
            cursor = db.cursor()
            cursor.execute(schema)
            cursor.close()
            exists = True
    return db 

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def query(cmd, args=()):
    try:
        cur = get_db().execute(cmd, args)
        rv = cur.fetchall()
        cur.close()
        return rv
    except:
        raise DBError

def geo(hostname):
    try:
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
    r = query('SELECT `id` FROM nodes WHERE host = ?', (hostname,))
    if len(r) == 0:
        lat,lon = geo(hostname)
        get_db().execute('INSERT INTO nodes (host,lat,lon) VALUES (?,?,?)', [hostname, lat, lon])
        get_db().commit()
        r = query('SELECT `id` FROM nodes WHERE host = ?', (hostname,))
    return r[0][0]

def insert_missing_hosts():
    hosts = list(set(query('SELECT `host` FROM jobs')))
    for h in hosts:
        if h is not None:
            get_host_id(h)


@app.route('/condor/query', methods=['GET'])
def condor_query():
    # query db and return
    task = request.args.get('task')
    if not task:
        raise BadInput
    where = 'task = ?'
    args=[task]
    jid = request.args.get('job_id')
    if jid:
        where += ' AND job_id = ?'
        args.append(jid)
    payload = query('SELECT `arg`, `job_id`, `timestamp`, `starttime`, `host` FROM jobs WHERE %s;'%where, args)
    return json.dumps(payload)

@app.route('/condor/done', methods=['POST'])
def condor_done():
    # use JSON payload to fill table
    data = request.get_json()
    try:
        task = data['task']
        timestamp = data['timestamp']
        job_id = data['job_id']
        # see if we know the job
        if len(query('SELECT `job_id` FROM jobs WHERE task = ? AND job_id = ?', (task, job_id))):
            for arg in data['args']:
                get_db().execute('UPDATE jobs SET timestamp = ? WHERE task = ? AND job_id = ? AND arg = ?', 
                                 (timestamp, task, job_id, arg))
            get_db().commit()
            return str(len(data['args'])) + '\n'
        else:
            records = [(task, arg, job_id, timestamp, None, None) for arg in data['args']]
            get_db().executemany('INSERT INTO jobs VALUES (?,?,?,?,?,?)', records)
            get_db().commit()
            return str(len(records))+'\n'
    except KeyError:
        raise BadInput
    except sqlite3.OperationalError as e:
        print str(e)
        raise DBError

@app.route('/condor/start', methods=['POST'])
def condor_start():
    # use JSON payload to fill table
    data = request.get_json()
    try:
        task = data['task']
        starttime = data['starttime']
        host = data['host']
        host_id = get_host_id(host)
        job_id = data['job_id']
        # see if we know the job
        if len(query('SELECT `job_id` FROM jobs WHERE task = ? AND job_id = ?', (task, job_id))):
            for arg in data['args']:
                get_db().execute(
                        'UPDATE jobs SET starttime = ?, host_id = ? WHERE task = ? AND job_id = ? AND arg = ?', 
                         (starttime, host_id, task, job_id, arg)
                    )
            get_db().commit()
            return str(len(data['args'])) + '\n'
        else:
            records = [(task, arg, job_id, None, starttime, host_id) for arg in data['args']]
            get_db().executemany(
                    'INSERT INTO jobs (task,arg,job_id,timestamp,starttime,host_id) VALUES (?,?,?,?,?,?)', 
                    records)
            get_db().commit()
            return str(len(records))+'\n'
        get_latlon(host)
    except KeyError:
        raise BadInput
    except sqlite3.OperationalError as e:
        print str(e)
        raise DBError

@app.route('/condor/clean', methods=['POST'])
def condor_clean():
    # use JSON payload to fill table
    data = request.get_json()
    try:
        task = data['task']
        if 'job_id' in data:
            job_id = data['job_id']
            get_db().execute('DELETE FROM jobs WHERE task=? AND job_id=?', (task,job_id))
        else:
            get_db().execute('DELETE FROM jobs WHERE task=?', (task,))
        get_db().commit()
        return 'Cleaned\n'
    except KeyError:
        raise BadInput
    except sqlite3.OperationalError:
        raise DBError
