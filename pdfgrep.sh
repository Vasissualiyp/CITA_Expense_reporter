#!/usr/bin/env bash

# Check if pdfgrep is installed
if ! command -v pdfgrep &> /dev/null
then
    echo "pdfgrep could not be found. Please install it and try again."
    exit
fi

# Check if the correct number of arguments is provided
if [ "$#" -ne 2 ]; then
    echo "Usage: $0 <DIRECTORY> <SEARCH_STRING>"
    exit 1
fi

DIRECTORY="$1"
SEARCH_STRING="$2"

# Create an array to hold search results
declare -a RESULTS

# Scan all PDF files in the directory
while IFS= read -r -d '' file; do
    while IFS= read -r line; do
        page=$(echo "$line" | awk -F: '{print $1}')
        snippet=$(echo "$line" | cut -d: -f2-)
        RESULTS+=("$file: Page $page: $snippet")
    done < <(pdfgrep -n "$SEARCH_STRING" "$file")
done < <(find "$DIRECTORY" -type f -name "*.pdf" -print0)

# Check if any results were found
if [ ${#RESULTS[@]} -eq 0 ]; then
    echo "No occurrences of '$SEARCH_STRING' found in any PDF files in '$DIRECTORY'."
    exit 0
fi

# Present results to the user
echo "Found the following occurrences of '$SEARCH_STRING':"
for i in "${!RESULTS[@]}"; do
    echo "[$i] ${RESULTS[$i]}"
done

# Prompt the user to choose a result
read -p "Enter the number of the occurrence you want to select: " selection

# Validate the user's selection
if ! [[ "$selection" =~ ^[0-9]+$ ]] || [ "$selection" -lt 0 ] || [ "$selection" -ge ${#RESULTS[@]} ]; then
    echo "Invalid selection."
    exit 1
fi

# Extract the selected result
selected_result="${RESULTS[$selection]}"
selected_file=$(echo "$selected_result" | cut -d: -f1)
selected_page=$(echo "$selected_result" | cut -d: -f2 | awk '{print $2}')

# Output the filename and page number
echo "Selected occurrence found in file '$selected_file' on page $selected_page."

