#!/usr/bin/env bash

name="announcement.pdf"
workdir="$HOME/Documents/Expenses/2024/Cosmolunch"
cd $workdir

files=$(find . -name "$name")
for file in $files; do
	pages=$(pdftk "$file" dump_data | grep PageMediaNumber | wc -l)
	#echo "$pages"
	echo "Pages for $file: $pages"
done
