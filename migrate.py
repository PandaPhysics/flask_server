from os import system, path, getenv
import json
import MySQLdb as sql 
import sqlite3

basedir = getenv('FLASK_BASE_DIR') 

# manage condor tasks through an sqlite3 db
litepath = basedir + '/condor/tasks.sqlite'
lite = sqlite3.connect(litepath, timeout=30) 

maria_conn = sql.connect(db='bird_watcher', user='snarayan')
maria = maria_conn.cursor()

select = 'SELECT host,lat,lon,id FROM nodes' 
cur = lite.execute(select)
insert = 'INSERT INTO nodes (host,lat,lon,id) VALUES (%s,%s,%s,%s)'
values = cur.fetchall()
print values[0]
for v in values:
    maria.execute(insert, v)

maria_conn.commit()

select = 'SELECT task,arg,job_id,timestamp,starttime,host,host_id,exit_code FROM jobs' 
cur = lite.execute(select)
insert = 'INSERT INTO jobs (task,arg,job_id,timestamp,starttime,host,host_id,exit_code) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)'
values = cur.fetchall()
print values[0]
for v in values:
    maria.execute(insert, v)

maria_conn.commit()
