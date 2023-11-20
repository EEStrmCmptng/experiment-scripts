#!/bin/bash

# list current status
sudo ufw status

# allow ssh
sudo ufw allow ssh

# allow connections from the following IP
#sudo ufw allow from 141.154.48.0/24
sudo ufw allow from 10.10.1.1
sudo ufw allow from 10.10.1.2
sudo ufw allow from 10.10.1.3
sudo ufw allow from 10.10.1.4
sudo ufw allow from 10.10.1.5

# clear current ports just in case
sudo ufw delete allow 11211
sudo ufw delete allow 8081
sudo ufw delete allow 6123
sudo ufw delete allow 80
sudo ufw delete allow 443

# mcd port
sudo ufw allow from 10.10.1.1 to any port 11211 proto tcp
sudo ufw allow from 10.10.1.2 to any port 11211 proto tcp
sudo ufw allow from 10.10.1.3 to any port 11211 proto tcp
sudo ufw allow from 10.10.1.4 to any port 11211 proto tcp
sudo ufw allow from 10.10.1.5 to any port 11211 proto tcp

# only allow our testing nodes IP to use Flink ports
sudo ufw allow from 10.10.1.1 to any port 8081 proto tcp
sudo ufw allow from 10.10.1.2 to any port 8081 proto tcp
sudo ufw allow from 10.10.1.3 to any port 8081 proto tcp
sudo ufw allow from 10.10.1.4 to any port 8081 proto tcp
sudo ufw allow from 10.10.1.5 to any port 8081 proto tcp

sudo ufw allow from 10.10.1.1 to any port 6123 proto tcp
sudo ufw allow from 10.10.1.2 to any port 6123 proto tcp
sudo ufw allow from 10.10.1.3 to any port 6123 proto tcp
sudo ufw allow from 10.10.1.4 to any port 6123 proto tcp
sudo ufw allow from 10.10.1.5 to any port 6123 proto tcp

sudo ufw allow from 10.10.1.1 to any port 80 proto tcp
sudo ufw allow from 10.10.1.2 to any port 80 proto tcp
sudo ufw allow from 10.10.1.3 to any port 80 proto tcp
sudo ufw allow from 10.10.1.4 to any port 80 proto tcp
sudo ufw allow from 10.10.1.5 to any port 80 proto tcp

sudo ufw allow from 10.10.1.1 to any port 443 proto tcp
sudo ufw allow from 10.10.1.2 to any port 443 proto tcp
sudo ufw allow from 10.10.1.3 to any port 443 proto tcp
sudo ufw allow from 10.10.1.4 to any port 443 proto tcp
sudo ufw allow from 10.10.1.5 to any port 443 proto tcp

# deny everything else
sudo ufw default allow outgoing
sudo ufw default deny incoming

# enable ufw
sudo ufw enable

# output should look like bottom
sudo ufw status
sudo ufw logging off

# Status: active

# To                         Action      From
# --                         ------      ----
# 22/tcp                     ALLOW       Anywhere                  
# Anywhere                   ALLOW       10.10.1.1                 
# Anywhere                   ALLOW       10.10.1.2                 
# Anywhere                   ALLOW       10.10.1.3                 
# 8081/tcp                   ALLOW       10.10.1.0/24              
# 6123/tcp                   ALLOW       10.10.1.0/24              
# 22/tcp (v6)                ALLOW       Anywhere (v6)     

