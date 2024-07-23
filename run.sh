#!/usr/bin/env bash

ESTATEMENTS_DIR="../eStatements"
SEARCH_STRING="PIZZAIOLO"
OUTPUT_DIR="../2024/CASCA_Membership"
#OUTPUT_DIR="../tests/testmode/"
MODE="custom"
#OUTPUT_DIR="../tests/NYC_Trip"

python create_expense.py "$ESTATEMENTS_DIR" "$OUTPUT_DIR" "$MODE" "$SEARCH_STRING" 
