#!/bin/bash 

export FLASK_BASE_DIR="/home/snarayan/flask_server/"

# see if a process exists already
if [[ $(ps U snarayan | grep "python.*flask" | wc -l) > 1 ]]; then
    pid=$(ps U snarayan | grep "python.*flask" | grep -v grep | awk '{ print $1 }')
    echo -n "Stopping process $pid..."
    kill $pid
    echo " Done"
    sleep 1
fi

echo -n "Starting server..."
wd=$PWD
cd /cvmfs/cms.cern.ch/slc6_amd64_gcc630/cms/cmssw/CMSSW_9_4_6/; eval `scramv1 runtime -sh`; cd $wd # need python>=2.7.9
export FLASK_APP=server.py
python -m flask run --host=0.0.0.0 > /local/snarayan/logs/flask.log 2>&1 & disown
echo " Done"
