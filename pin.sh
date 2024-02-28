#!/bin/bash

# Resets state by allowing threads to migrate across all cores
function reset
{
    while read line; do
	taskset -cp 0-$( expr $(nproc) - 1 ) ${line##*,}
    done < $1
}

# Pin all tids on CPU Package 0, hardcoded cores 0-7 for now
function pin0
{
    while read line; do
	taskset -cp 0-7 ${line##*,}
    done < $1
}

# Pin all tids on CPU Package 1, hardcoded cores 8-15 for now
function pin1
{
    while read line; do
	taskset -cp 8-15 ${line##*,}
    done < $1
}

# Pin all Netty tids to one CPU, passed in via argument
function pinNetty
{
    while read line; do
	case $line in
	    *"Netty"* )
		taskset -cp $2 ${line##*,}
	    ;;
	esac	
    done < $1
}

# Pin all Mapper tids to CPU Package 0, all other tids to Package 1
function pinMappers0
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
function pinMappers1
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

"$@"
