#!/bin/bash

sudo apt-get update
sudo apt-get install -y maven openjdk-11-jdk-headless python3-pip

pip install numpy pandas flink-rest-client
