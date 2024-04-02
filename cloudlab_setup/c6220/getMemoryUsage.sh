#!/bin/bash
mem_swpd=0
mem_free=0
mem_buff=0
mem_cache=0

tmp=$(vmstat | tail -1)
mem_swpd=$(echo $tmp | awk -F ' ' '{ print $3 }')
mem_buff=$(echo $tmp | awk -F ' ' '{ print $4 }')
mem_cache=$(echo $tmp | awk -F ' ' '{ print $5 }')
echo $mem_swpd, $mem_buff, $mem_cache




#procs -----------memory---------- ---swap-- -----io---- -system-- ------cpu-----
# r  b   swpd   free   buff  cache   si   so    bi    bo   in   cs us sy id wa st
# 0  0      0 38095832 628224 22651108    0    0     0     4    2    1  0  0 100  0  0

