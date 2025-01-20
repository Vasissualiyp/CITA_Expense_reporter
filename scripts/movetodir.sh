#!/usr/bin/env bash

# This script is used to move the cosmolunch sign-in sheets

#workdir='../2024/Cosmolunch'
workdir="$HOME/Pictures/Office-Lens"
year=2024
format="pdf"
movetodir="$HOME/Documents/Expenses/$year/Cosmolunch"

files=$(find "$workdir" -name "Cosmolunch_$year-*.$format")

# Iterate over all pdf/jpg files with the specific pattern
for file in $files; do
  # Extract the month and day part from the filename
  # Ensure we are extracting correctly by checking the file format
  if [[ $file =~ Cosmolunch_$year-([0-9]{2})-([0-9]{2}).$format ]]; then
    # Bash regex capture groups are stored in BASH_REMATCH array
    month="${BASH_REMATCH[1]}"
    day="${BASH_REMATCH[2]}"
    dir="$movetodir/${month}-${day}"

    # Create the directory if it does not exist
    # mkdir -p "$dir"
    
    # Move the file into the corresponding directory
    mv "$file" "$dir/Signup_sheet.$format" || { echo "Directory $dir doesn't exist"; }
  else
    echo "Filename format unexpected: $file"
  fi
done
