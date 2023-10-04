#!/bin/bash

set -x

CWD=$(pwd)

cd $CWD/uarch-configure/rapl-read/ && make raplog && sudo setcap cap_sys_rawio=ep raplog && cd $CWD

cd /etc/systemd/system && sudo ln -s $CWD/rapl_service/rapl_log.service rapl_log.service && cd $CWD
