#!/bin/bash 

export FLASK_BASE_DIR="/home/${USER}/flask_server/"

# see if a process exists already
if [[ $(ps U snarayan | grep "gunicorn" | wc -l) > 1 ]]; then
    pid=$(ps U snarayan | grep "gunicorn" | grep -v grep | awk '{ print $1 }')
    echo -n "Stopping process $pid..."
    kill $pid
    echo " Done"
    sleep 1
fi

echo -n "Starting server..."
# need python>=2.7.9
cd /cvmfs/cms.cern.ch/slc6_amd64_gcc630/cms/cmssw/CMSSW_9_4_6/; eval `scramv1 runtime -sh`
cd $FLASK_BASE_DIR
export FLASK_APP=server.py
date > ${FLASK_BASE_DIR}/keyfile
gunicorn server:app -w 4 --access-logfile - --timeout 120 -b 0.0.0.0:5000 > /local/${USER}/logs/flask.log 2>&1 & disown
#gunicorn server:app -w 4 --access-logfile - --timeout 120 -k gevent --worker-connections 100 -b 0.0.0.0:5000 > /local/${USER}/logs/flask.log 2>&1 & disown
#gunicorn server:app -k gevent --worker-connections 100 > /local/${USER}/logs/flask.log 2>&1 & disown
#python -m flask run --host=0.0.0.0 > /local/${USER}/logs/flask.log 2>&1 & disown
echo " Done"
