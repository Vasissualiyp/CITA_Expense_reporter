#!/usr/bin/env bash

workdir="$HOME/Documents/Expenses/2024/Cosmolunch"
cd $workdir

combine_with_name() {
  name="$1"
  
  # Gather all matching PDFs into an array
  mapfile -t target_files < <(find . -name "$name.pdf")
  
  # If nothing found, quit
  if [ ${#target_files[@]} -eq 0 ]; then
    echo "No $name.pdf files found."
    exit 1
  fi
  
  # Finally, call pdfunite with all inputs + output last
  pdftk "${target_files[@]}" cat output "all_${name}s.pdf"
}

combine_with_name "receipt"
combine_with_name "announcement"
combine_with_name "Signup_sheet"
