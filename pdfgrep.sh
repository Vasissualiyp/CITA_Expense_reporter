#!/usr/bin/env bash

# Function to search for a string in all PDF files in a directory
search_string_in_pdfs() {
    local directory="$1"
    local search_string="$2"

    # Check if pdfgrep is installed
    if ! command -v pdfgrep &> /dev/null
    then
        echo "pdfgrep could not be found. Please install it and try again."
        return 1
    fi

    # Create an array to hold search results
    declare -a results

    # Scan all PDF files in the directory
    while IFS= read -r -d '' file; do
        while IFS= read -r line; do
            page=$(echo "$line" | awk -F: '{print $1}')
            snippet=$(echo "$line" | cut -d: -f2-)
            results+=("$file: Page $page: $snippet")
        done < <(pdfgrep -n "$search_string" "$file")
    done < <(find "$directory" -type f -name "*.pdf" -print0)

    # Check if any results were found
    if [ ${#results[@]} -eq 0 ]; then
        echo "No occurrences of '$search_string' found in any PDF files in '$directory'."
        return 0
    fi

    # Present results to the user
    echo "Found the following occurrences of '$search_string':"
    for i in "${!results[@]}"; do
        echo "[$i] ${results[$i]}"
    done

    # Prompt the user to choose a result
    read -p "Enter the number of the occurrence you want to select: " selection

    # Validate the user's selection
    if ! [[ "$selection" =~ ^[0-9]+$ ]] || [ "$selection" -lt 0 ] || [ "$selection" -ge ${#results[@]} ]; then
        echo "Invalid selection."
        return 1
    fi

    # Extract the selected result
    selected_result="${results[$selection]}"
    selected_file=$(echo "$selected_result" | cut -d: -f1)
    selected_page=$(echo "$selected_result" | cut -d: -f2 | awk '{print $2}')

}

# Wrapper script to call the function
if [ "$#" -ne 2 ]; then
    echo "Usage: $0 <DIRECTORY> <SEARCH_STRING>"
    exit 1
fi

search_string_in_pdfs "$1" "$2"

# Output the filename and page number
echo "Selected occurrence found in file '$selected_file' on page $selected_page."
