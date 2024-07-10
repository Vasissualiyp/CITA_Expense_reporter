#!/usr/bin/env bash

# Check if pdfgrep is installed
if ! command -v pdfgrep &> /dev/null
then
    echo "pdfgrep could not be found. Please install it and try again."
    exit
fi

# Check if the correct number of arguments is provided
if [ "$#" -ne 2 ]; then
    echo "Usage: $0 <PDF_FILE> <SEARCH_STRING>"
    exit 1
fi

PDF_FILE="$1"
SEARCH_STRING="$2"

# Use pdfgrep to find the string and extract the page numbers
pdfgrep -n "$SEARCH_STRING" "$PDF_FILE" | awk -F: '{print $1}' 
