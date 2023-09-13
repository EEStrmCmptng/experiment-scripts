#!/bin/bash

# set default to accept everything
sudo iptables -P INPUT ACCEPT
sudo iptables -P FORWARD ACCEPT
sudo iptables -P OUTPUT ACCEPT

# flush previous rules
sudo iptables -F # flush all rules
sudo iptables -X # delete all chains

# drops all packets with a bad state
sudo iptables -A INPUT -m conntrack --ctstate INVALID -j DROP

# Allowing Established and Related Incoming Connections
sudo iptables -A INPUT -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT

# Allowing Established Outgoing Connections
sudo iptables -A OUTPUT -m conntrack --ctstate ESTABLISHED -j ACCEPT

# accept any packets coming or going on localhost
sudo iptables -A INPUT -i lo -j ACCEPT
sudo iptables -A OUTPUT -o lo -j ACCEPT

# Allowing Internal Network enp5s0f0 to access External eno1
#sudo iptables -A FORWARD -i enp5s0f0 -o eno1 -j ACCEPT

# accept on specific IPs
#sudo iptables -A INPUT -s 128.197.29.0/24 -j ACCEPT
sudo iptables -A INPUT -s 10.10.1.1 -j ACCEPT
sudo iptables -A INPUT -s 10.10.1.2 -j ACCEPT
sudo iptables -A INPUT -s 10.10.1.3 -j ACCEPT

# allow all incoming ssh
sudo iptables -A INPUT -p tcp --dport 22 -m conntrack --ctstate NEW,ESTABLISHED -j ACCEPT
sudo iptables -A OUTPUT -p tcp --sport 22 -m conntrack --ctstate ESTABLISHED -j ACCEPT

# allow outgoing ssh
sudo iptables -A OUTPUT -p tcp --dport 22 -m conntrack --ctstate NEW,ESTABLISHED -j ACCEPT
sudo iptables -A INPUT -p tcp --sport 22 -m conntrack --ctstate ESTABLISHED -j ACCEPT

# allow incoming http, https
#sudo iptables -A INPUT -p tcp -s 10.10.1.0/24 -m multiport --dports 80,443 -m conntrack --ctstate NEW,ESTABLISHED -j ACCEPT
#sudo iptables -A OUTPUT -p tcp -m multiport --dports 80,443 -m conntrack --ctstate ESTABLISHED -j ACCEPT

# flink ports
#sudo iptables -A INPUT -p tcp -s 10.10.1.0/24 -m multiport --dports 6123,8081 -m conntrack --ctstate NEW,ESTABLISHED -j ACCEPT
#sudo iptables -A OUTPUT -p tcp -m multiport --dports 6123,8081 -m conntrack --ctstate ESTABLISHED -j ACCEPT

# set all packets not matching these rules to drop
sudo iptables -P INPUT DROP

# disable packet forward/routing
sudo iptables -P FORWARD DROP

# list current rules
sudo iptables --list-rules
