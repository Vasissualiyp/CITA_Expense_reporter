#!/usr/bin/env bash

year=2025
workdir="$HOME/Documents/Expenses/$year/Cosmolunch"

dirs=$(find $workdir -type d -name "[0-9][0-9]-[0-9][0-9]" | sort)
for dir in $dirs; do
	amount=$(cat "$dir/amount.txt")
	dir_end=$(echo $dir | awk -F'/' '{print $NF}')
	date="$year-$dir_end"
	echo "$date, $amount"
done
