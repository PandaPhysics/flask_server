#!/bin/bash

# requires mysql2sqlite to be installed in $basedir

basedir=/home/snarayan/flask_server/condor/

cd $basedir

mysqldump --skip-extended-insert --compact -u snarayan bird_watcher > backup.sql
./mysql2sqlite backup.sql | sqlite3 backup.sqlite

mv backup.sqlite tasks.sqlite
ls -ltrh
rm backup.sql 

cd -
