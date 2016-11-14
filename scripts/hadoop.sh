#!/bin/bash

boldecho() {
    echo -e "\033[01;31m$1\033[00m"
}

startstop() {
    # anything that simply needs start or stop goes in here

    #upper="$(tr '[:lower:]' '[:upper:]' <<< ${1:0:1})${1:1}ing"

    if [ "$1" == "start" ]; then
        upper="Starting"
    else
        upper="Stopping"
    fi

    boldecho "$upper Hadoop"
    /usr/local/hadoop/sbin/$1-dfs.sh
    boldecho "$upper Yarn"
    /usr/local/hadoop/sbin/$1-yarn.sh
#    boldecho "$upper Zookeeper"
#    /usr/local/zookeeper/bin/zkServer.sh $1
    boldecho "$upper HBase"
    /usr/local/hbase/bin/$1-hbase.sh

    boldecho "$upper Phoenix"
    /usr/local/phoenix/bin/queryserver.py $1
}

start() {
    startstop start
}

stop() {
    startstop stop
}

case $1 in
    start)
        start
        ;;
    stop)
        stop
        ;;
    restart)
        stop
        start
        ;;
esac
