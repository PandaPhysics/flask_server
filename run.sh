#!/bin/bash 

export FLASK_BASE_DIR="/home/${USER}/flask_server/"

# see if a process exists already
if [[ $(ps U snarayan | grep "python.*flask" | wc -l) > 1 ]]; then
    pid=$(ps U snarayan | grep "python.*flask" | grep -v grep | awk '{ print $1 }')
    echo -n "Stopping process $pid..."
    kill $pid
    echo " Done"
    sleep 1
fi

exit 0 

echo -n "Starting server..."
# need python>=2.7.9
cd /cvmfs/cms.cern.ch/slc6_amd64_gcc630/cms/cmssw/CMSSW_9_4_6/; eval `scramv1 runtime -sh`
cd $FLASK_BASE_DIR
export FLASK_APP=server.py
date > ${FLASK_BASE_DIR}/keyfile
python -m flask run --host=0.0.0.0 > /local/${USER}/logs/flask.log 2>&1 & disown
echo " Done"
