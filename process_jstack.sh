#!/bin/bash

# Loop through each line in the file
while IFS= read -r line; do
    # Extract the desired values from the line
    name=$(echo "$line" | grep -oE '"[^"]+"' | head -n1)
    cpu=$(echo "$line" | grep -o 'cpu=[0-9.]*' | sed 's/cpu=//')
    elapsed=$(echo "$line" | grep -o 'elapsed=[0-9.]*' | sed 's/elapsed=//')
    tid=$(echo "$line" | grep -oP 'nid=\K[^ ]+')
    
    # If elapsed is not empty, multiply it by 1000, convert from seconds to milliseconds
    if [ -n "$elapsed" ]; then
        elapsed=$(echo "$elapsed * 1000" | bc)
    fi
    
    # Print the extracted values separated by a comma if both name and cpu are not empty
    if [ -n "$name" ] && [ -n "$cpu" ] && [ -n "$elapsed" ] && [ -n "$tid" ]; then
        printf "%s, %s, %s, %d\n" "$name" "$cpu" "$elapsed" "$tid"
    fi
done < $1

##!/bin/bash

#while read line; do
#    taskset -cp 14 ${line##*,}
#done < jstack1140.sorted
