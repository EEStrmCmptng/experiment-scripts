#!/bin/bash

for f in logs/cores16_frate200000_420000*; do
for i in 0 1 2; do
	  python3 clean_flink.py $f $i
done
done

