import os
import csv
import sys
import re
from datetime import datetime, timedelta
from PyPDF2 import PdfReader

class Transaction:
    def __init__(self, date, filepath, page, amount):
        self.date = date
        self.filepath = filepath
        self.page = page
        self.amount = amount

    def to_csv_row(self):
        return [self.date, self.filepath, self.page, self.amount]

class TransactionFinder:
    def __init__(self, estatements_dir):
        self.estatements_dir = estatements_dir

    def find_transactions(self, search_term):
        transactions = []
        is_date = re.match(r"\d{2}-\d{2}", search_term)

        if is_date:
            target_date = datetime.strptime(search_term, "%m-%d")
            date_range = [
                (target_date - timedelta(days=1)).strftime("%b %d").upper(),
                target_date.strftime("%b %d").upper(),
                (target_date + timedelta(days=1)).strftime("%b %d").upper()
            ]
            print(f"Searching for dates: {date_range}", file=sys.stderr)
            search_terms = date_range
        else:
            print(f"Searching for string: {search_term}", file=sys.stderr)
            search_terms = [search_term.upper()]

        for root, _, files in os.walk(self.estatements_dir):
            for file in files:
                if file.endswith('.pdf'):
                    file_path = os.path.join(root, file)
                    print(f"Scanning file: {file_path}", file=sys.stderr)
                    transactions.extend(self._scan_pdf(file_path, search_terms))

        return transactions

    def _scan_pdf(self, file_path, search_terms):
        transactions = []
        try:
            pdf = PdfReader(file_path)
            for page_num, page in enumerate(pdf.pages, 1):
                text = page.extract_text()
                lines = text.split('\n')
                for i, line in enumerate(lines):
                    if any(term in line.upper() for term in search_terms):
                        print(f"Found matching term in line: {line}", file=sys.stderr)
                        transaction = self._parse_transaction(line, lines[i+1] if i+1 < len(lines) else "")
                        if transaction:
                            transactions.append((file_path, page_num, transaction))
                            print(f"Added transaction: {transaction}", file=sys.stderr)
        except Exception as e:
            print(f"Error processing {file_path}: {str(e)}", file=sys.stderr)
        return transactions

    def _parse_transaction(self, line, next_line):
        if '$' in line:
            return line.strip()
        elif '$' in next_line:
            return f"{line.strip()} {next_line.strip()}"
        return None

class TransactionAdder:
    def __init__(self, csv_file):
        self.csv_file = csv_file

    def add_transaction(self, transaction):
        with open(self.csv_file, 'a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(transaction.to_csv_row())

def format_date(date_str):
    date = datetime.strptime(date_str, "%b %d")
    return date.strftime("%m-%d")

def extract_amount(transaction_str):
    parts = transaction_str.split('$')
    if len(parts) > 1:
        return f"${parts[-1]}"
    return ""

def add_transactions_from_estatements(estatements_dir, csv_file):
    finder = TransactionFinder(estatements_dir)
    adder = TransactionAdder(csv_file)

    while True:
        search_term = input("Enter a transaction posting date (MM-DD) or a search string, or 'q' to quit: ")
        if search_term.lower() == 'q':
            break

        transactions = finder.find_transactions(search_term)
        if not transactions:
            print("No transactions found for the given search term.")
            continue

        print("Found transactions:")
        for i, (file, page, transaction) in enumerate(transactions, 1):
            print(f"{i}. {transaction}")

        selections = input("Enter the numbers of transactions to add (comma-separated) or 'a' for all: ")
        if selections.lower() == 'a':
            selected_transactions = transactions
        else:
            indices = [int(s.strip()) - 1 for s in selections.split(',')]
            selected_transactions = [transactions[i] for i in indices if 0 <= i < len(transactions)]

        for file, page, transaction_details in selected_transactions:
            parts = transaction_details.split()
            date_formatted = format_date(parts[0] + " " + parts[1])
            amount = extract_amount(transaction_details)
            trans = Transaction(date_formatted, file, page, amount)
            adder.add_transaction(trans)
            print(f"Added: {transaction_details}")

    print("Transaction adding complete. Goodbye!")
if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python add_transactions.py <estatements_directory> <csv_file>", file=sys.stderr)
        sys.exit(1)
    
    estatements_dir = sys.argv[1]
    csv_file = sys.argv[2]
    add_transactions_from_estatements(estatements_dir, csv_file)
