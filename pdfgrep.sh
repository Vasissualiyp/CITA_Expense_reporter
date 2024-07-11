#!/usr/bin/env bash

# Global variables
declare -a results
selected_result=""
selected_file=""
selected_page=""
selected_month=""
selected_day=""

# Function to check if pdfgrep is installed
check_pdfgrep() {
    if ! command -v pdfgrep &> /dev/null; then
        echo "pdfgrep could not be found. Please install it and try again."
        exit 1
    fi
}

# Function to scan PDF files for a search string
scan_pdfs() {
    local directory="$1"
    local search_string="$2"

    while IFS= read -r -d '' file; do
        while IFS= read -r line; do
            page=$(echo "$line" | awk -F: '{print $1}')
            snippet=$(echo "$line" | cut -d: -f2-)
            results+=("$file: Page $page: $snippet")
        done < <(pdfgrep -n "$search_string" "$file")
    done < <(find "$directory" -type f -name "*.pdf" -print0)
}

# Function to present results to the user
present_results() {
    if [ ${#results[@]} -eq 0 ]; then
        echo "No occurrences of '$search_string' found in any PDF files in '$directory'."
        exit 0
    fi

    echo "Found the following occurrences of '$search_string':"
    for i in "${!results[@]}"; do
        echo "[$i] ${results[$i]}"
    done
}

# Function to prompt the user to choose a result
prompt_user_selection() {
    read -p "Enter the number of the occurrence you want to select: " selection

    if ! [[ "$selection" =~ ^[0-9]+$ ]] || [ "$selection" -lt 0 ] || [ "$selection" -ge ${#results[@]} ]; then
        echo "Invalid selection."
        exit 1
    fi

    selected_result="${results[$selection]}"
    selected_file=$(echo "$selected_result" | cut -d: -f1)
    selected_page=$(echo "$selected_result" | cut -d: -f2 | awk '{print $2}')
}

# Function to extract and convert the month and day from the first date
extract_date_info() {
    local date_info=$(echo "$selected_result" | grep -oP '\b[A-Z]{3}\s+\d{2}\b' | head -1)
    selected_month=$(echo "$date_info" | awk '{print $1}')
    selected_day=$(echo "$date_info" | awk '{print $2}')

    # Convert month abbreviation to number
    case "$selected_month" in
        JAN) selected_month="01" ;;
        FEB) selected_month="02" ;;
        MAR) selected_month="03" ;;
        APR) selected_month="04" ;;
        MAY) selected_month="05" ;;
        JUN) selected_month="06" ;;
        JUL) selected_month="07" ;;
        AUG) selected_month="08" ;;
        SEP) selected_month="09" ;;
        OCT) selected_month="10" ;;
        NOV) selected_month="11" ;;
        DEC) selected_month="12" ;;
        *) selected_month="??" ;;
    esac
}


# Function to find the first date after the given date
find_first_date_after() {
    local year="$1"
    local month="$2"
    local day="$3"
    local directory="$4"

    # Convert the input month and day to a comparable format (MMDD)
    local input_date="${month}${day}"

    # Initialize a variable to hold the closest date
    local closest_date=""

    # Loop through each directory in the specified directory
    for dir in "$directory"/*/; do
        # Remove the trailing slash from the directory name
        dir="${dir%/}"
        
        # Extract the directory name
        dir_name=$(basename "$dir")
        
        # Extract the month and day from the directory name
        local dir_month="${dir_name%-*}"
        local dir_day="${dir_name#*-}"
        
        # Convert the directory month and day to a comparable format (MMDD)
        local dir_date="${dir_month}${dir_day}"
        
        # Check if the directory date is after the input date and if it is closer than the current closest date
        if [[ "$dir_date" -ge "$input_date" && ( -z "$closest_date" || "$dir_date" < "$closest_date" ) ]]; then
            closest_date="$dir_date"
        fi
    done

    # Format the closest date back to MM-DD
    if [ -n "$closest_date" ]; then
        closest_date="${closest_date:0:2}-${closest_date:2:2}"
        echo "$closest_date"
    else
        echo "No date found after the given date."
    fi
}


# Main script
if [ "$#" -ne 3 ]; then
    echo "Usage: $0 <ESTATEMENTS_DIRECTORY> <SEARCH_STRING> <FINAL_DIRECTORY>"
    exit 1
fi

directory="$1"
search_string="$2"
final_directory="$3"
year=2024

check_pdfgrep
scan_pdfs "$directory" "$search_string"
present_results
prompt_user_selection
extract_date_info

# Print the results
echo "Selected occurrence found in file '$selected_file' on page $selected_page."
echo "Month: $selected_month, Day: $selected_day"

find_first_date_after "$year" "$selected_month" "$selected_day" "$final_directory"
