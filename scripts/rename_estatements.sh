
#!/usr/bin/env bash

# Change directory to the one containing your files, if necessary
dir='../eStatements/2024/8681'
cd "$dir"

# Iterate over files matching the pattern and handle spaces properly
for file in "Chequing Statement-8681 2024-"*.pdf; do
    echo "Processing file: $file"
    # Use awk with a field separator to correctly extract the date
    newname=$(echo "$file" | awk -F'2024-' '{ print $2 }' | awk -F'.pdf' '{ print $1 ".pdf" }')
    echo "New name would be: $newname"

    # Rename the file if newname is successfully extracted
    if [[ -n "$newname" ]]; then
        mv "$file" "$newname"
        echo "File renamed to: $newname"
    else
        echo "No match found for renaming."
    fi
done
