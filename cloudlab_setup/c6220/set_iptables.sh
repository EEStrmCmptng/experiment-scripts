#!/bin/bash

# list current rules
sudo iptables --list-rules

# set default to accept everything
sudo iptables -P INPUT ACCEPT
sudo iptables -P FORWARD ACCEPT
sudo iptables -P OUTPUT ACCEPT

# flush previous rules
sudo iptables -F # flush all rules
sudo iptables -X # delete all chains

# drops all packets with a bad state
sudo iptables -A INPUT -m state --state INVALID -j DROP

# accept any packets that have something to do with ones we've sent on outbound
sudo iptables -A INPUT -m state --state RELATED,ESTABLISHED -j ACCEPT

# accept any packets coming or going on localhost
sudo iptables -A INPUT -i lo -j ACCEPT

# accept on specific IPs
sudo iptables -A INPUT -s 128.197.29.0/24 -j ACCEPT
sudo iptables -A INPUT -s 10.10.1.1 -j ACCEPT
sudo iptables -A INPUT -s 10.10.1.2 -j ACCEPT
sudo iptables -A INPUT -s 10.10.1.3 -j ACCEPT

# set all packets not matching these rules to drop
sudo iptables -P INPUT DROP                                            

# disable packet forward/routing
sudo iptables -P FORWARD DROP
