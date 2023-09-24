#!/bin/bash

set -x

function static_r320
{
    sudo setcap cap_net_admin+ep /usr/sbin/ethtool

    ieth=$(ifconfig | grep -B1 192.168.1 | grep -o "^\w*")
    ethtool -c ${ieth}
    
    # disable dynamic ITR
    ethtool -C ${ieth} adaptive-rx off
    ethtool -C ${ieth} rx-usecs 2
    
    echo ""
    ethtool -c ${ieth}
    
}

function static_mlnx
{
    sudo setcap cap_net_admin+ep /usr/sbin/ethtool

    ieth=$(ifconfig | grep -B1 192.168.1 | grep -o "^\w*")
    ethtool -c ${ieth}
    
    # disable dynamic ITR
    ethtool -C ${ieth} adaptive-rx off adaptive-tx off
    ethtool -C ${ieth} rx-usecs 2 tx-usecs 2
    
    echo ""
    ethtool -c ${ieth}
}

function dynamic_xl170
{
    sudo setcap cap_net_admin+ep /usr/sbin/ethtool
    
    ieth=$(ifconfig | grep -B1 192.168.1 | grep -o "^\w*")
    ethtool -c ${ieth}
    
    # enable dynamic ITR
    ethtool -C ${ieth} rx-usecs 8 tx-usecs 8 rx-frames 128 tx-frames 128 
    ethtool -C ${ieth} adaptive-rx on adaptive-tx on
    
    echo ""
    ethtool -c ${ieth}
}

function dynamic_d6515
{
    sudo setcap cap_net_admin+ep /usr/sbin/ethtool
    
    ieth=$(ifconfig | grep -B1 192.168.1 | grep -o "^\w*")
    ethtool -c ${ieth}
    
    # enable dynamic ITR
    ethtool -C ${ieth} rx-usecs 8 tx-usecs 8 rx-frames 128 tx-frames 128 
    ethtool -C ${ieth} adaptive-rx on adaptive-tx on
    
    echo ""
    ethtool -c ${ieth}
}

function dynamic_rs620
{
    sudo setcap cap_net_admin+ep /usr/sbin/ethtool
    
    ieth=$(ifconfig | grep -B1 192.168.1 | grep -o "^\w*")
    ethtool -c ${ieth}
    
    # enable dynamic ITR
    ethtool -C ${ieth} rx-usecs 60 rx-usecs-irq 60
    ethtool -C ${ieth} adaptive-rx on
    
    echo ""
    ethtool -c ${ieth}
}

function static_rs620
{
    sudo setcap cap_net_admin+ep /usr/sbin/ethtool
    
    ieth=$(ifconfig | grep -B1 192.168.1 | grep -o "^\w*")
    ethtool -c ${ieth}
    
    # enable static ITR
    ethtool -C ${ieth} adaptive-rx off
    ethtool -C ${ieth} rx-usecs 2 rx-usecs-irq 2
    
    echo ""
    ethtool -c ${ieth}
}

"$@"
