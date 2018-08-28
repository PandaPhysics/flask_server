#!/bin/bash 

export FLASK_BASE_DIR="/home/${USER}/flask_server/"

# see if a process exists already
if [[ $(ps U snarayan | grep "gunicorn" | wc -l) > 1 ]]; then
    pid=$(ps U snarayan f | grep "gunicorn" | grep -v grep | awk '{ print $1 }' | head -n1)
    echo -n "Stopping gunicorn process $pid..."
    kill $pid
    echo " Done"
    sleep 5
fi

if [[ $(ps U snarayan | grep "python.*flask" | wc -l) > 1 ]]; then
    pid=$(ps U snarayan f | grep "python.*flask" | grep -v grep | awk '{ print $1 }' | head -n1)
    echo -n "Stopping python.*flask process $pid..."
    kill $pid
    echo " Done"
    sleep 5
fi

echo -n "Starting server..."
# need python>=2.7.9
cd /cvmfs/cms.cern.ch/slc6_amd64_gcc630/cms/cmssw/CMSSW_9_4_6/; eval `scramv1 runtime -sh`
cd $FLASK_BASE_DIR
export PYTHONPATH=${PYTHONPATH}:/usr/lib64/python2.7/site-packages/
export FLASK_APP=server2.py
date > ${FLASK_BASE_DIR}/keyfile
which gunicorn

# using builtin synchronous processes
#gunicorn server:app -w 4 --access-logfile - --timeout 120 -b 0.0.0.0:5000 > /local/${USER}/logs/flask.log 2>&1 & disown
# using coroutines from gevent
gunicorn server:app -w 4 --access-logfile - --timeout 120 -k gevent --worker-connections 500 -b 0.0.0.0:5000 > /local/${USER}/logs/flask.log 2>&1 & disown
# using bare flask = not recommended! 
#python -m flask run --host=0.0.0.0 > /local/${USER}/logs/flask.log 2>&1 & disown

echo " Done"
