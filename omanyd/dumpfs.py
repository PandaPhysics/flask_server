#!/usr/bin/env python

import os
import MySQLdb as sql 
from time import time
from glob import glob 
import logging

VERBOSITY = 10
NOW = int(time())
USER = 'snarayan'
BASE = '/mnt/hadoop/cms/store/user/%s/pandaf/'%USER

def crawl(path):
    if os.path.isdir(path):
        to_insert = []
        children = glob(path + '/*')
        for c in children:
            to_insert += crawl(c)
        return to_insert
    else:
        return [(path, os.path.getsize(path) / 1e6, NOW)]


db = sql.connect(db='bird_watcher', user='snarayan')
cursor = db.cursor()

all_files = crawl(BASE)
print all_files[:5]
cursor.executemany('INSERT INTO files (path,mbytes,last_access) VALUES (%s,%s,%s)', all_files)
db.commit()
