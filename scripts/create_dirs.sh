#!/usr/bin/env bash

DIRS="dirs.txt"
CHECKLIST_TEMPLATE="checklist_template.txt"

DIRS_NO=$(wc -l "$DIRS" | awk '{print $1}')
i=1
while [[ "$i" -le "$DIRS_NO" ]]; do
	DIRNAME=$(sed "${i}q;d" "$DIRS")
	mkdir -p "$DIRNAME"
	echo "Created directory $DIRNAME"
	cp "$CHECKLIST_TEMPLATE" "$DIRNAME/checklist.txt"
	i=$((i+1))
done
