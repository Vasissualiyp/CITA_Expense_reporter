import os
import csv
import sys
import re
from datetime import datetime, timedelta
from PyPDF2 import PdfReader

class Transaction:
    def __init__(self, date, filepath, page, amount, category=None, subcategory=None):
        self.date = date
        self.filepath = filepath
        self.page = page
        self.amount = amount
        self.category = category
        self.subcategory = subcategory

    def to_csv_row(self):
        return {
            'date': self.date,
            'file': self.filepath,
            'page': self.page,
            'amount': self.amount,
            'category': self.category,
            'subcategory': self.subcategory
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
            print(f"Searching for dates: {date_range}", file=sys.stderr)
            search_terms = date_range
        else:
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
                        print(f"Found matching term in line: {line}", file=sys.stderr)
                        transaction = self._parse_transaction(lines, i)
                        if transaction:
                            transactions.append((file_path, page_num, transaction))
                            print(f"Added transaction: {transaction}", file=sys.stderr)
                        else:
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

        print("This is the transaction string:")
        print(transaction)

        print(f"Parsing transaction: {transaction}", file=sys.stderr)

        # Extract date
        date_match = re.search(r'\b([A-Z]{3})\s+(\d{2})\b', transaction)
        if date_match:
            date = f"{date_match.group(1)} {date_match.group(2)}"
            print(f"Found date: {date}", file=sys.stderr)
        else:
            print("Failed to extract date", file=sys.stderr)
            return None

        # Extract amount
        amount_match = re.search(r'(\d*\$\d+\.\d{2})', transaction)
        if amount_match:
            full_amount = amount_match.group(1)
            amount = full_amount.split('$')[-1]
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
            writer = csv.DictWriter(file, fieldnames=['date', 'file', 'page', 'amount', 'category', 'subcategory'])
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

def prompt_category():
    categories = [
        "Travel within Canada (Economy)", "Travel to USA from Ontario (Economy)", "All other Airfare (Economy)",
        "Travel within Canada (Above-Economy)", "Travel to USA from Ontario (Above-Economy)", "All other Airfare (Above-Economy)",
        "ON (13%HST)", "PEI, NS, NF, NB (15%HST)", "All other provinces / territories", "USA / International",
        "Per Diem: Canada", "Per Diem: USA / International", "KMS x 57 cents/km",
        "Travel within Canada (Rail/Bus)", "Travel outside Canada (Rail/Bus)", "Travel within or outside Canada (Public Transit)",
        "ON (13%HST) (Car Rental)", "PEI, NS, NF, NB (15%HST) (Car Rental)", "All other provinces / territories (Car Rental)", "USA / International (Car Rental)",
        "ON (13%HST) (Meals)", "PEI, NS, NF, NB (15%HST) (Meals)", "All other provinces / territories (Meals)", "USA / International (Meals)",
        "ON (13%HST) (Taxi)", "PEI, NS, NF, NB (15%HST) (Taxi)", "All other provinces / territories (Taxi)", "USA / International (Taxi)"
    ]
    print("\nPlease select a category:")
    for i, category in enumerate(categories, 1):
        print(f"{i}. {category}")
    selection = int(input("Enter the category number: ")) - 1
    return categories[selection]

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
            parts = transaction_details.split(' - ', 1)
            if len(parts) == 2:
                date_amount, _ = parts
                date, amount = date_amount.rsplit('$', 1)
                date_formatted = format_date(date.strip())
                amount = amount.strip()
                category = prompt_category()
                subcategory = category  # For now, category and subcategory are the same
                trans = Transaction(date_formatted, file, page, amount, category, subcategory)
                adder.add_transaction(trans)
                print(f"Added: {transaction_details} under category {category} and subcategory {subcategory}")
            else:
                print(f"Failed to parse transaction details: {transaction_details}")

    print("Transaction adding complete. Goodbye!")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python add_transactions.py <estatements_directory> <csv_file>", file=sys.stderr)
        sys.exit(1)
    
    estatements_dir = sys.argv[1]
    csv_file = sys.argv[2]
    add_transactions_from_estatements(estatements_dir, csv_file)
