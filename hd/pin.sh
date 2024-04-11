#!/bin/bash

# Resets state by allowing threads to migrate across all cores
function reset
{
    while read line; do
	taskset -cp 0-$( expr $(nproc) - 1 ) ${line##*,}
    done < $1
}

# Pin all tids on CPU Package 0, hardcoded cores 0-7 for now
function C1
{
    while read line; do
	taskset -cp 0-7 ${line##*,}
    done < $1
}

# Pin all tids on CPU Package 1, hardcoded cores 8-15 for now
function C2
{
    while read line; do
	taskset -cp 8-15 ${line##*,}
    done < $1
}

# Pin all Netty tids to CPU $nproc-1, passed in via argument
function C3
{
    while read line; do
	case $line in
	    *"Netty"* )
		taskset -cp $(($(nproc) - 1)) ${line##*,}
	    ;;
	esac	
    done < $1
}

# Pin all Mapper tids to CPU Package 0, all other tids to Package 1
function C4
{
    while read line; do
	case $line in
	    *"Mapper"* )
		taskset -cp 0-7 ${line##*,}
		;;
	    *)
		taskset -cp 8-15 ${line##*,}
		;;
	esac	
    done < $1
}

# Pin all Mapper tids to CPU Package 0, all other tids to CPU via argument
function pinMappers0_2
{
    while read line; do
	case $line in
	    *"Mapper"* )
		taskset -cp 0-7 ${line##*,}
		;;
	    *)
		taskset -cp $2 ${line##*,}
		;;
	esac	
    done < $1
}

# Pin all Mapper tids to CPU Package 1, all other tids to Package 0
function C5
{
    while read line; do
	case $line in
	    *"Mapper"* )
		taskset -cp 8-15 ${line##*,}
		;;
	    *)
		taskset -cp 0-7 ${line##*,}
		;;
	esac	
    done < $1
}

# Pin all non-Mapper threads to core $nproc-1
function C6
{
    while read line; do
	case $line in
	    *"Mapper"* )
		# do nothing
		echo "*** Skipping Mapper tid ${line##*,} ***"
		;;
	    *)
		echo "taskset -cp $(($(nproc) - 1)) ${line##*,}"
		taskset -cp $(($(nproc) - 1)) ${line##*,}
		;;
	esac	
    done < $1
}

# Pin all Mapper tids to CPU Package 1, all other tids to CPU via argument
function pinMappers1_2
{
    while read line; do
	case $line in
	    *"Mapper"* )
		taskset -cp 8-15 ${line##*,}
		;;
	    *)
		taskset -cp $2 ${line##*,}
		;;
	esac	
    done < $1
}

function pin4
{
    core=0
    while read line; do
	case $line in
	    *"Mapper"* )
		pcore=$(($(nproc) - (core % 4) - 1))
		taskset -cp ${pcore} ${line##*,}
		core=$((core+1))
		;;
	esac	
    done < $1
}

function pin16
{
    core=0
    while read line; do
	case $line in
	    *"Mapper"* )
		pcore=$(($(nproc) - (core % 16) - 1))
		taskset -cp ${pcore} ${line##*,}
		core=$((core+1))
		;;
	esac	
    done < $1
}


"$@"
