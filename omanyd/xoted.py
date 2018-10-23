#!/usr/bin/env python

from os import remove
import MySQLdb as sql 
from time import time, strftime, gmtime
from re import sub
import logging

THRESHOLD = 20e6 # (5x2 = 10 TB / user) in units of MB 
VERBOSITY = 20

logging.basicConfig(level=VERBOSITY, format='%(asctime)-15s %(message)s')

logging.info('threshold is set at %.2fGB'%(THRESHOLD / 1.e3))

class PFile(object):
    __slots__ = ['path', 'size', 'last_access']
    def __init__(self, path, size, last_access):
        self.path = path
        self.size = size
        self.last_access = last_access

class User(object):
    def __init__(self, user):
        self.name = user 
        self._pfiles = []
        self._total_size = 0
    def add_file(self, path, size, last_access):
        p = PFile(path, size, last_access)
        self._total_size += p.size
        self._pfiles.append(p)
        logging.debug('user %s has file path=%s, size=%.2fGB, access=%s'%(
                        self.name,
                        path,
                        size / 1.e3,
                        strftime('%Y-%m-%d %H:%M:%S', gmtime(p.last_access))))
    def _sort(self):
        self._pfiles.sort(key=lambda x : x.last_access)
    def _pop(self, cursor):
        p = self._pfiles.pop(0)
        self._total_size -= p.size 
        remove(p.path)
        cursor.execute('DELETE FROM files WHERE path = %s', (p.path,))
        logging.info('removed file path=%s, size=%.2fGB, access=%s'%(
                        p.path,
                        p.size / 1.e3,
                        strftime('%Y-%m-%d %H:%M:%S', gmtime(p.last_access))))
        return p.path 
    def clean(self, threshold_bytes, cursor):
        self._sort()
        removed = []
        while self._total_size > threshold_bytes:
            removed.append(self._pop(cursor))
        return removed 
    @property
    def total_size(self):
        return self._total_size
    @property
    def n_files(self):
        return len(self._pfiles)


db = sql.connect(db='bird_watcher', user='snarayan')
cursor = db.cursor()

users = {}
logging.info('querying database for all known files')
cursor.execute('SELECT path,mbytes,last_access FROM files')
for row in cursor.fetchall():
    uname = sub('.*/store/user/','',row[0]).split('/')[0]
    user = users
    if uname not in users:
        users[uname] = User(uname)
    user = users[uname]
    user.add_file(*row)

for _,user in users.iteritems():
    logging.info('user %s has total volume %.2fGB with %i files. cleaning up...'%(
        user.name,
        user.total_size / 1.e3,
        user.n_files))
    removed = user.clean(THRESHOLD, cursor)
    logging.info('user %s has total volume %.2fGB after cleaning %i files'%(
        user.name,
        user.total_size / 1.e3,
        len(removed)))
                                  
db.commit() 
