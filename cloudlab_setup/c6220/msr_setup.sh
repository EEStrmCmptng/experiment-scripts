#!/bin/bash

set -x

# creates msr group and lets user rdmsr, wrmsr without sudo
sudo groupadd msr
sudo chgrp msr /dev/cpu/*/msr
sudo ls -l /dev/cpu/*/msr
sudo chmod g+rw /dev/cpu/*/msr
sudo usermod -aG msr $(whoami)

echo "Re-login for msr group changes to take effect"
sudo newgrp msr

