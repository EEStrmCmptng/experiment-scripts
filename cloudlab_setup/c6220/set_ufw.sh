#!/bin/bash

# list current status
sudo ufw status

# allow ssh
sudo ufw allow ssh

# allow connections from the following IP
sudo ufw allow from 141.154.48.0/24
sudo ufw allow from 10.10.1.1
sudo ufw allow from 10.10.1.2
sudo ufw allow from 10.10.1.3

# flink required ports
# clear current ports just in case
sudo ufw delete allow 8081
sudo ufw delete allow 6123

# only allow our testing nodes IP to use Flink ports
sudo ufw allow from 10.10.1.1 to any port 8081 proto tcp
sudo ufw allow from 10.10.1.2 to any port 8081 proto tcp
sudo ufw allow from 10.10.1.3 to any port 8081 proto tcp

sudo ufw allow from 10.10.1.1 to any port 6123 proto tcp
sudo ufw allow from 10.10.1.2 to any port 6123 proto tcp
sudo ufw allow from 10.10.1.3 to any port 6123 proto tcp
 
# deny everything else
sudo ufw default allow outgoing
sudo ufw default deny incoming

# output should look like bottom
sudo ufw status

# Status: active

# To                         Action      From
# --                         ------      ----
# 22/tcp                     ALLOW       Anywhere                  
# Anywhere                   ALLOW       141.154.48.0/24           
# Anywhere                   ALLOW       10.10.1.1                 
# Anywhere                   ALLOW       10.10.1.2                 
# Anywhere                   ALLOW       10.10.1.3                 
# 8081/tcp                   ALLOW       10.10.1.0/24              
# 6123/tcp                   ALLOW       10.10.1.0/24              
# 22/tcp (v6)                ALLOW       Anywhere (v6)     

