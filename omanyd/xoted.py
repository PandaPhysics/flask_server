#!/usr/bin/env python

import os 
from os import remove
import MySQLdb as sql 
from time import time, strftime, gmtime
from re import sub
import logging

THRESHOLD = 10e6 # (5x2 = 10 TB / user) in units of MB 
VERBOSITY = 20
NOW = time()

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
        self._p2p = {}
        self._paths = set([])
        self._total_size = 0
    def has_file(self, path):
        return (path in self._paths)
    def add_file(self, path, size, last_access=NOW, insert=False):
        if not self.has_file(path):
            p = PFile(path, size, last_access)
            self._pfiles.append(p)
            self._p2p[path] = p
            self._paths.add(path)
            self._total_size += p.size
            if insert:
                logging.debug('user %s has file path=%s, size=%.2fGB, access=%s'%(
                                self.name,
                                path,
                                size / 1.e3,
                                strftime('%Y-%m-%d %H:%M:%S', gmtime(p.last_access))))
                cursor.execute('INSERT INTO files (path,last_access,mbytes) VALUES (%s,%s,%s)', \
                               (path, int(last_access), int(size)))
            return True
        else:
            p = self._p2p[path]
            if p.size != size:
                self._total_size -= p.size
                self._total_size += size
                p.size = size 
                if insert:
                    logging.debug('user %s has inconsistent file path=%s, size=%.2fGB, access=%s'%(
                                    self.name,
                                    path,
                                    size / 1.e3,
                                    strftime('%Y-%m-%d %H:%M:%S', gmtime(p.last_access))))
                    cursor.execute('UPDATE files SET mbytes = %s WHERE path = %s', (size, path))
                return True
        return False
    def _sort(self):
        self._pfiles.sort(key=lambda x : x.last_access)
    def _pop(self, cursor):
        p = self._pfiles.pop(0)
        self._total_size -= p.size 
        try:
            self._paths.remove(p.path)
        except KeyError:
            pass
        try:
            remove(p.path)
        except OSError:
            pass 
        cursor.execute('DELETE FROM files WHERE path = %s', (p.path,))
        logging.info('removed file path=%s, size=%.2fGB, access=%s'%(
                        p.path,
                        p.size / 1.e3,
                        strftime('%Y-%m-%d %H:%M:%S', gmtime(p.last_access))))
        return p.path 
    def clean(self, threshold_bytes, cursor):
        self._sort()
        removed = []
        if self._total_size > 0.99 * threshold_bytes:
            while self._total_size > 0.98 * threshold_bytes:
                removed.append(self._pop(cursor))
        return removed 
    @property
    def total_size(self):
        return self._total_size
    @property
    def n_files(self):
        return len(self._pfiles)

if __name__ == '__main__':

    db = sql.connect(db='bird_watcher', user='snarayan')
    cursor = db.cursor()

    users = {}
    logging.info('querying database for all known files')
    cursor.execute('SELECT path,mbytes,last_access FROM files WHERE mbytes>0')
    for row in cursor.fetchall():
        uname = sub('.*/store/user/','',row[0]).split('/')[0]
        user = users
        if uname not in users:
            users[uname] = User(uname)
        user = users[uname]
        user.add_file(*row)

    logging.info('checking filesystem for inconsistencies')
    for _,user in users.iteritems():
        N = 0; mb = 0
        for root,_,files in os.walk('/mnt/hadoop/cms/store/user/%s/pandaf/'%user.name):
            for f in files:
                fullpath = root + '/' + f
                if not user.has_file(fullpath):
                    size = int(os.stat(fullpath).st_size * 1e-6)
                    if user.add_file(fullpath, size, NOW, True):
                        N += 1
                        mb += size
        if N > 0:
            logging.warning('user %s has inconsistent volume %.2fGB with %i files'%(
                user.name,
                mb / 1.e3,
                N))

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
