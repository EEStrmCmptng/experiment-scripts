#!/bin/bash

cat /proc/$(pgrep java)/status | grep -i Threads > ~/before_flink_java_threads.txt
cat /proc/$(pgrep flink)/status | grep -i Threads > ~/before_flink_flink_threads.txt
ps aux > ~/before_flink_processes.txt

./run_total.sh & cat /proc/$(pgrep java)/status | grep -i Threads > ~/during_flink_java_threads.txt & cat /proc/$(pgrep flink)/status | grep -i Threads > ~/during_flink_flink_threads.txt & ps aux > ~/during_flink_processes


cat /proc/$(pgrep java)/status | grep -i Threads > ~/after_flink_java_threads.txt
cat /proc/$(pgrep flink)/status | grep -i Threads > ~/after_flink_flink_threads.txt
ps aux > ~/after_flink_processes.txt



