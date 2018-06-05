#!/bin/bash

BASE_DIR=$1 
REPO=$2
GITURL=$3

WD=$PWD
cd $BASE_DIR/doxygen/repos/

while [[ 1 == 1 ]] ; do
    if [[ -f keyfile ]]; then # file exists, good to go
        rm keyfile
        if [[ -d "$REPO" ]] ; then 
            cd $REPO
            git pull origin master
            cd ..
        else 
            git lfs clone $GITURL $REPO
        fi
        doxygen ../doxy.cfg 
        date > keyfile 
        exit 0
    else 
        echo "Waiting for key to be replaced..."
        sleep 10 # sleep 10s, try again
    fi 
done

cd $WD
