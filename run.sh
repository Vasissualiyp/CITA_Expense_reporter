#!/usr/bin/env bash

ESTATEMENTS_DIR="../eStatements"
SEARCH_STRING="PIZZAIOLO"
#OUTPUT_DIR="../tests/Cosmolunch"
OUTPUT_DIR="../tests/NYC_Trip"

python create_expense.py "$ESTATEMENTS_DIR" "$SEARCH_STRING" "$OUTPUT_DIR"
