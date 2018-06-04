from flask import request, Flask, abort, g
from os import system, path, getenv
import sqlite3
import json

basedir = getenv('FLASK_BASE_DIR') 
app = Flask('')

# actions to be taken on push to Panda* repositories
# called through GitHub webhook
@app.route('/push', methods=['POST'])
def push():
    doxy_basedir = basedir + '/doxy/repos/'
    data = request.get_json()
    repo = data['repository']['git_url'].split('/')[-1].replace('.git','')
    if not path.isdir(doxy_basedir+repo):
        system('cd %s; git lfs clone %s %s'%(doxy_basedir, data['repository']['clone_url'], repo))
    system('cd %s/%s ; git lfs pull origin master'%(doxy_basedir,repo))
    system('cd %s ; doxygen ../doxy.cfg'%doxy_basedir)
    return 'Success!\n'


# manage condor tasks through an sqlite3 db
dbpath = basedir + '/condor/tasks.sqlite'
exists = path.isfile(dbpath)

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(dbpath)
        if not exists:
            cursor = db.cursor()
            cursor.execute('CREATE TABLE jobs (task TEXT, arg TEXT, job_id TEXT, timestamp INTEGER)')
            cursor.close()
    return db 

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def query(cmd, args=()):
    cur = get_db().execute(cmd, args)
    rv = cur.fetchall()
    cur.close()
    return rv

@app.route('/condor', methods=['GET', 'POST'])
def condor():
    if request.method == 'GET':
        # query db and return
        task = request.args.get('task')
        if not task:
            abort(402)
        where = 'task="%s"'%task
        jid = request.args.get('job_id')
        if jid:
            where += ', job_id=%i'%jid
        cursor = get_db().execute('SELECT `arg`, `job_id`, `timestamp` FROM jobs WHERE %s;'%where)
        payload = cursor.fetchall()
        cursor.close()
        return json.dumps(payload)
    else:
        # use JSON payload to fill table
        data = request.get_json()
        try:
            task = data['task']
            timestamp = data['timestamp']
            job_id = data['job_id']
            records = [(task, arg, job_id, timestamp) for arg in data['args']]
            get_db().executemany('INSERT INTO jobs VALUES (?,?,?,?)', records)
            get_db().commit()
            return str(len(records))+'\n'
        except KeyError:
            abort(402)
