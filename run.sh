#!/usr/bin/env bash

ESTATEMENTS_DIR="../eStatements"
SEARCH_STRING="PIZZAIOLO"
OUTPUT_DIR="../tests/Cosmolunch"

python create_expense.py "$ESTATEMENTS_DIR" "$SEARCH_STRING" "$OUTPUT_DIR"
