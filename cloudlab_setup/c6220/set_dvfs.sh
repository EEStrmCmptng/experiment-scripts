#!/bin/bash

set -x

function userspace
{
    sudo ~/experiment-scripts/cloudlab_setup/c6220/cpufreq-set-all -g userspace
    sudo cpufreq-info
}

# conservative, ondemand, userspace, powersave, performance, schedutil 
function ondemand
{
    sudo ~/experiment-scripts/cloudlab_setup/c6220/cpufreq-set-all -g ondemand
    sudo cpufreq-info
}

function conservative
{
    sudo ~/experiment-scripts/cloudlab_setup/c6220/cpufreq-set-all -g conservative
    sudo cpufreq-info
}

function powersave
{
    sudo ~/experiment-scripts/cloudlab_setup/c6220/cpufreq-set-all -g powersave
    sudo cpufreq-info
}

function performance
{
    sudo ~/experiment-scripts/cloudlab_setup/c6220/cpufreq-set-all -g performance
    sudo cpufreq-info
}

function schedutil
{
    sudo ~/experiment-scripts/cloudlab_setup/c6220/cpufreq-set-all -g schedutil
    sudo cpufreq-info
}

"$@"
