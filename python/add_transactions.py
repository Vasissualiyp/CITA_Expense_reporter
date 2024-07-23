import os
import csv
import sys
import re
import subprocess
from datetime import datetime, timedelta
from PyPDF2 import PdfReader
from python.full_reimbursement import define_categories, category_to_row
from python.define_table import define_reimbursement_table

class Transaction:
    def __init__(self, date, filepath, page, amount, subcategory=None):
        self.date = date
        self.filepath = filepath
        self.page = page
        self.amount = amount
        self.subcategory = subcategory

    def to_csv_row(self):
        return {
            'date': self.date,
            'file': self.filepath,
            'page': self.page,
            'amount': self.amount,
            'subcategory': self.subcategory  # Save subcategory as a number
        }

    @property
    def month(self):
        return datetime.strptime(self.date, "%m-%d").strftime("%m")

    @property
    def day(self):
        return datetime.strptime(self.date, "%m-%d").strftime("%d")

class TransactionFinder:
    def __init__(self, estatements_dir, debug=False):
        self.estatements_dir = estatements_dir
        self.debug = debug

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
            if self.debug:
                print(f"Searching for dates: {date_range}", file=sys.stderr)
            search_terms = date_range
        else:
            if self.debug:
                print(f"Searching for string: {search_term}", file=sys.stderr)
            search_terms = [search_term.upper()]

        for root, _, files in os.walk(self.estatements_dir):
            for file in files:
                if file.endswith('.pdf'):
                    file_path = os.path.join(root, file)
                    if self.debug:
                        print(f"Scanning file: {file_path}", file=sys.stderr)
                    file_transactions = self._scan_pdf(file_path, search_terms)
                    transactions.extend(file_transactions)
                    if self.debug:
                        print(f"Found {len(file_transactions)} transactions in this file", file=sys.stderr)

        if self.debug:
            print(f"Total transactions found: {len(transactions)}", file=sys.stderr)
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
                        if self.debug:
                            print(f"Found matching term in line: {line}", file=sys.stderr)
                        transaction = self._parse_transaction(lines, i)
                        if transaction:
                            transactions.append((file_path, page_num, transaction))
                            if self.debug:
                                print(f"Added transaction: {transaction}", file=sys.stderr)
                        else:
                            if self.debug:
                                print(f"Failed to parse transaction from line: {line}", file=sys.stderr)
        except Exception as e:
            print(f"Error processing {file_path}: {str(e)}", file=sys.stderr)
        return transactions

    def _parse_transaction(self, lines, start_index):
        transaction = lines[start_index].strip()
        i = start_index

        # Continue to the next lines until we find a line with a $
        while i + 1 < len(lines) and '$' not in lines[i]:
            i += 1
            transaction += ' ' + lines[i].strip()

        if self.debug:
            print("This is the transaction string:")
            print(transaction)
            print(f"Parsing transaction: {transaction}", file=sys.stderr)

        # Extract date
        date_match = re.search(r'\b([A-Z]{3})\s+(\d{2})\b', transaction)
        if date_match:
            date = f"{date_match.group(1)} {date_match.group(2)}"
            if self.debug:
                print(f"Found date: {date}", file=sys.stderr)
        else:
            print("Failed to extract date", file=sys.stderr)
            return None

        # Extract amount
        amount_match = re.search(r'(\d*\$\d+\.\d{2})', transaction)
        if amount_match:
            full_amount = amount_match.group(1)
            amount = full_amount.split('$')[-1]
            if self.debug:
                print(f"Found amount: ${amount}", file=sys.stderr)
        else:
            print("Failed to extract amount", file=sys.stderr)
            return None

        return f"{date} ${amount} - {transaction}"

class TransactionAdder:
    def __init__(self, csv_file):
        self.csv_file = csv_file

    def add_transaction(self, transaction):
        file_exists = os.path.isfile(self.csv_file)
        with open(self.csv_file, 'a', newline='') as file:
            writer = csv.DictWriter(file, fieldnames=['date', 'file', 'page', 'amount', 'subcategory'])
            if not file_exists:
                writer.writeheader()  # Write the header only if the file doesn't exist
            writer.writerow(transaction.to_csv_row())

def get_unique_file_page_pairs(csv_filename):
    unique_pairs = set()
    with open(csv_filename, 'r') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            unique_pairs.add((row['file'], row['page']))
    return unique_pairs

def format_date(date_str):
    date = datetime.strptime(date_str, "%b %d")
    return date.strftime("%m-%d")

def extract_amount(transaction_str):
    parts = transaction_str.split('$')
    if len(parts) > 1:
        return f"${parts[-1]}"
    return ""

def prompt_category(table_params):
    categories = define_categories(table_params)
    
    print("\nPlease select a category:")
    for i, category in enumerate(categories, 1):
        print(f"{i}. {category.name}")
    print("0. OTHER")
    
    category_selection = int(input("Enter the category number: ")) - 1
    
    if category_selection == -1:  # User selected 'OTHER'
        other_category_name = input("Please enter the name of the 'OTHER' category: ")
        return "OTHER", other_category_name
    
    selected_category = categories[category_selection]
    
    print(f"\nPlease select a subcategory for {selected_category.name}:")
    for i, option in enumerate(selected_category.options, 1):
        print(f"{i}. {option}")
    subcategory_selection = int(input("Enter the subcategory number: ")) - 1
    
    selected_subcategory = selected_category.options[subcategory_selection]
    
    # Return the subcategory number according to the category_to_row dictionary
    return selected_category.name, category_to_row[selected_subcategory]

def open_file_in_editor(state, file_path):
    subprocess.run([state.editor, file_path])

def add_transactions_from_estatements(state, estatements_dir, csv_file):
    finder = TransactionFinder(estatements_dir)
    adder = TransactionAdder(csv_file)

    table_params = define_reimbursement_table()

    if os.path.exists(csv_file):
        print("Existing transactions:")
        with open(csv_file, 'r') as file:
            print(file.read())
        while True:
            edit_csv = input("Review the above transactions. 'c' to continue or 'e' to make changes...").strip()
            if not edit_csv:
                edit_csv = 'c'
            if edit_csv.lower() == 'e':
                open_file_in_editor(state, csv_file)
                break
            elif edit_csv.lower() == 'c':
                break
            else:
                print("Sorry, your option is not available. Try again with 'c', 'e' or Enter")

    while True:
        search_term = input("Enter a transaction posting date (MM-DD) or a search string, or 'c' to continue: ")
        if not search_term:
            search_term = 'c'
        if search_term.lower() == 'c':
            break

        transactions = finder.find_transactions(search_term)
        if not transactions:
            print("No transactions found for the given search term.")
            continue

        print("Found transactions:")
        for i, (file, page, transaction) in enumerate(transactions, 1):
            print(f"{i}. {transaction}")

        selections = input("Enter the numbers of transactions to add (comma-separated), 'a' for all, or 'q' to cancel: ")
        if selections.lower() == 'a':
            selected_transactions = transactions
        elif selections.lower() == 'q':
            continue
        else:
            indices = [int(s.strip()) - 1 for s in selections.split(',')]
            selected_transactions = [transactions[i] for i in indices if 0 <= i < len(transactions)]

        for file, page, transaction_details in selected_transactions:
            parts = transaction_details.split(' - ', 1)
            if len(parts) == 2:
                date_amount, _ = parts
                date, amount = date_amount.rsplit('$', 1)
                date_formatted = format_date(date.strip())
                amount = amount.strip()

                change_amount = input(f"Would you like to change the amount for this transaction? (y/N): ")
                if change_amount.lower() == 'y':
                    current_amount = f"${amount}"
                    print(f"Current amount for this transaction is {current_amount}. Please, enter a new amount:")
                    amount = input("New amount: ").strip()

                _, subcategory_number = prompt_category(table_params)
                
                trans = Transaction(date_formatted, file, page, amount, subcategory_number)
                adder.add_transaction(trans)
                print(f"Added: {transaction_details} with subcategory number {subcategory_number}")
            else:
                print(f"Failed to parse transaction details: {transaction_details}")

    print("Transaction adding complete. Goodbye!")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python add_transactions.py <estatements_directory> <csv_file>", file=sys.stderr)
        sys.exit(1)
    
    estatements_dir = sys.argv[1]
    csv_file = sys.argv[2]
    add_transactions_from_estatements(None, estatements_dir, csv_file)
