#!/usr/bin/env bash

year=2025
workdir="$HOME/Documents/Expenses/$year/Cosmolunch"
cd "$workdir"
output_dir="$workdir/output"

mkdir -p "$output_dir"

combine_with_name() {
  name="$1"
  
  # Gather all matching PDFs into an array
  mapfile -t target_files < <(find . -name "$name.pdf" | sort)
  
  # If nothing found, quit
  if [ ${#target_files[@]} -eq 0 ]; then
    echo "No $name.pdf files found."
    exit 1
  fi
  
  # Finally, call pdfunite with all inputs + output last
  pdftk "${target_files[@]}" cat output "$output_dir/all_${name}s.pdf"
}

combine_with_name "receipt"
combine_with_name "announcement"
combine_with_name "Signup_sheet"
