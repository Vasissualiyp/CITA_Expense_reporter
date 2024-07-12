#!/usr/bin/env bash

signed_reimbursement_form_path="/home/vasilii/Documents/Expenses/2024/Cosmolunch/Reimbursement_form_with_sign.pdf"
current_date=$(date +%Y-%m-%d)

# Global variables
declare -a results
selected_result=""
selected_file=""
selected_page=""
selected_month=""
selected_day=""
selected_amount=""

# Function to check if pdfgrep is installed
check_pdfgrep() {
    if ! command -v pdfgrep &> /dev/null; then
        echo "pdfgrep could not be found. Please install it and try again."
        exit 1
    fi
}

# Function to scan PDF files for a search string 
# (this is used to find transactions in credit cards)
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

# Function that does same thing as prompt_user_selection, except automatically based
# on a provided selection id
autoloop_selection() {
    local i="$1"

	if ! [[ "$i" =~ ^[0-9]+$ ]] || [ "$i" -lt 0 ] || [ "$(($i))" -ge ${#results[@]} ]; then
        echo 1
		echo "Checking the last one..."
		flag_to_stop_autoloop=1
        return
    fi

    selected_result="${results[$i]}"
    selected_file=$(echo "$selected_result" | cut -d: -f1)
    selected_page=$(echo "$selected_result" | cut -d: -f2 | awk '{print $2}')
    
    echo 0  # Success
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

	# Extract the dollar amount
    selected_amount=$(echo "$selected_result" | grep -oP '\$\d+(\.\d{2})?' | head -1)
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
    closest_date=""

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
    else
        echo "No date found after the given date."
		exit 1
    fi
}

# Function to convert PDF to JPEG
convert_pdfs_to_jpegs() {
    local output_dir="$1"
	local quality="$2"

    # Check if pdftoppm is installed
    if ! command -v pdftoppm &> /dev/null; then
        echo "pdftoppm could not be found. Please install it and try again."
        exit 1
    fi

    # Loop through each PDF file in the directory
    for pdf_file in "$output_dir"/*.pdf; do
        # Extract the base name (without extension) of the file
        base_name=$(basename "$pdf_file" .pdf)

        # Convert the PDF to JPEG
        pdftoppm -jpeg -r "$quality" "$pdf_file" "$output_dir/$base_name"

        # Rename the output file from *.jpg to the desired name
        mv "$output_dir/$base_name-1.jpg" "$output_dir/$base_name.jpg"
    done
}

get_date() {
  present_results
  prompt_user_selection
  extract_date_info

  # Print the transaction info
  echo "Selected occurrence found in file '$selected_file' on page $selected_page."
  echo "Transaction Month: $selected_month, Day: $selected_day"
  echo "Money amount: $selected_amount"
  
  # Get the first cosmolunch that happened after the transaction happened
  find_first_date_after "$year" "$selected_month" "$selected_day" "$expense_reports_directory"
  echo "Date of cosmolunch: $closest_date"
}
get_date_autoloop() {
  i="$1"
  autoloop_selection "$i"
  extract_date_info

  # Print the transaction info
  echo "Selected occurrence found in file '$selected_file' on page $selected_page."
  echo "Transaction Month: $selected_month, Day: $selected_day"
  echo "Money amount: $selected_amount"
  
  # Get the first cosmolunch that happened after the transaction happened
  find_first_date_after "$year" "$selected_month" "$selected_day" "$expense_reports_directory"
  echo "Date of cosmolunch: $closest_date"
}

censor_transactions() {
  # Now copy the transaction page to the expense reports directory
  jpg_quality=300
  creditcard_out_dir="$output_dir/creditcard"
  mkdir "$creditcard_out_dir"
  pdftk "$selected_file" cat "$selected_page" output "$creditcard_out_dir/1.pdf" # 1> /dev/null 2> /dev/null
  convert_pdfs_to_jpegs "$creditcard_out_dir" "$jpg_quality" # 1> /dev/null 2> /dev/null
  rm -rf "$creditcard_out_dir/*.pdf"
  echo ""
  echo ""
  echo "Now you have to only enable transaction for ${selected_month}-${selected_day}:"
  python "${python_dir}"/censor_transactions.py "$creditcard_out_dir/1.jpg"
  rm -rf "$creditcard_out_dir/[0-9].pdf" "$creditcard_out_dir/[0-9].jpg"
}

create_reimbursement_form() {
  local application_file="${output_dir}/application.pdf"
  local mode="$1"
  python "${python_dir}"/insert_into_pdf.py "$mode" "$selected_amount" "$current_date" "$signed_reimbursement_form_path" "$application_file"
  echo "Saved to: $application_file"
}

combine_pdfs() {
  local output_dir="$1" 
  local filename="$2" 

  mkdir tmpbin
  cd tmpbin # moving to bin directory to now pollute the current directory with latex build files
  
  pdflatex "../$output_dir/description.tex"
  mv ./description.pdf "../$output_dir"
  python "${python_dir}"/combine_docs.py "../$output_dir" "$filename"
  cd ..
  rm -rf ./tmpbin
}

run_python_scripts() {
  mode="$1"
  output_dir="$2"
  final_report_filename="$3"
  #censor_transactions
  create_reimbursement_form "$mode"
  combine_pdfs "$output_dir" "$final_report_filename"
}

# ------------------------
# ----- Main script ------
# ------------------------

if [ "$#" -ne 3 ]; then
    echo "Usage: $0 <ESTATEMENTS_DIRECTORY> <SEARCH_STRING> <EXPENSE_REPORTS_DIRECTORY>"
    exit 1
fi

estatements_directory="$1"
search_string="$2"
expense_reports_directory="$3"
final_report_filename="combined_application.pdf"
python_dir=$(pwd)/python
autoloop=1
year=2024

if [[ "$expense_reports_directory" == *"Cosmolunch"* ]]; then
    mode="cosmolunch"
else
    mode="other"
fi

check_pdfgrep
scan_pdfs "$estatements_directory" "$search_string"

if [ "$autoloop" -eq 0 ]; then # Case when we don't loop
  get_date
  output_dir="$expense_reports_directory/$closest_date"
  run_python_scripts "$mode" "$output_dir" "$final_report_filename"
else # Case when we do autoloop
  i=0
  flag_to_stop_autoloop=0
  while [ "$flag_to_stop_autoloop" -eq 0 ]; do
	echo "Looking at the case $i"
    get_date_autoloop "$i"
    output_dir="$expense_reports_directory/$closest_date"
    run_python_scripts "$mode" "$output_dir" "$final_report_filename"
	i=$((i+1))
	echo ""
	echo ""
  done
fi
