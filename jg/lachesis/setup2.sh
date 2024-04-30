#!/bin/bash

newgrp docker
docker run hello-world
sudo apt-get install docker-compose -y
sudo apt-get install cgroup-tools -y
mkdir lachesis-experiments
cd lachesis-experiments
git clone https://github.com/dmpalyvos/lachesis-evaluation scheduling-queries
cd ~/lachesis-experiments/scheduling-queries
./update_paths.sh $(eval echo "~/lachesis-experiments")
pip install -r requirements.txt
