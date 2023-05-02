#!/bin/bash

for f in logs/cores16_frate12500*; do
for i in 0 1 2 3 4 5 6 7 8 9; do
	  python3 clean_flink.py $f $i
done
done

