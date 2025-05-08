#!/usr/bin/env bash

# This program opens receipt and allows user to save amount
# on the receipt to a file amount.txt

year=2025
workdir="$HOME/Documents/Expenses/$year/Cosmolunch"

dirs=$(find $workdir -type d -name "[0-9][0-9]-[0-9][0-9]")
for dir in $dirs; do
	noreceipt=0
	zathura "$dir/receipt.pdf" || { echo "No receipt found" ; noreceipt=1; }
	if [[ $noreceipt -ne 1 ]]; then
		read -p "What is the amount on the receipt? " amount
		echo "$amount" > "$dir/amount.txt"
	fi
done
