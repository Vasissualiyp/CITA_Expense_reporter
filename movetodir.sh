#!/usr/bin/env bash

# Iterate over all jpg files with the specific pattern
for file in Cosmolunch_2024-*.jpg; do
  # Extract the month and day part from the filename
  # Ensure we are extracting correctly by checking the file format
  if [[ $file =~ Cosmolunch_2024-([0-9]{2})-([0-9]{2}).jpg ]]; then
    # Bash regex capture groups are stored in BASH_REMATCH array
    month="${BASH_REMATCH[1]}"
    day="${BASH_REMATCH[2]}"
    dir="${month}-${day}"

    # Create the directory if it does not exist
    mkdir -p "$dir"
    
    # Move the file into the corresponding directory
    mv "$file" "$dir/"
  else
    echo "Filename format unexpected: $file"
  fi
done
