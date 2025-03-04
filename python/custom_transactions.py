import os
import csv
import sys
import subprocess
import argparse
from collections import defaultdict
from datetime import datetime
from pdf2image import convert_from_path
from PIL import Image
import shutil
import re
from PyPDF2 import PdfReader, PdfWriter, PdfMerger
from python.add_transactions import add_transactions_from_estatements, open_file_in_editor
from python.insert_into_pdf import insert_into_pdf
from python.censor_transactions import censor_transactions_mainloop
from python.insert_into_pdf import create_reimbursement_form
from python.combine_docs import create_combined_pdf

class TmpFiles:
    def __init__(self):
        self.ordering_and_descriptions_file = 'pdfs_order.tex' 
        self.descriptions_file = 'description.tex'
        self.descriptions_file_pdf = self._convert_to_pdf(self.descriptions_file)
        self.application_file = 'application.pdf'
        self.combined_creditcards_filename = 'combined_creditcards.pdf'

    def _convert_to_pdf(self, tex_file):
        return tex_file.replace('.tex', '.pdf')

def process_transactions_custom(state, args, config_file):
    year = state.year
    mode = state.mode
    tmpfiles = TmpFiles()

    # Step 1: Use add_transactions_from_estatements to select transactions and save to CSV
    csv_filename = 'selected_transactions.csv'
    csv_file = os.path.join(args.expense_reports_directory, csv_filename)
    add_transactions_from_estatements(state, args.estatements_directory, csv_file)

    # Step 2: Get unique file+page pairs from CSV
    unique_pairs = get_unique_file_page_pairs(csv_file)

    # Step 3: Copy unique pairs (file+page) to creditcards directory
    output_dir = create_output_directory(args.expense_reports_directory)
    output_dir = os.path.abspath(output_dir)
    creditcards_dir = os.path.join(output_dir, 'creditcards')
    os.makedirs(creditcards_dir, exist_ok=True)
    copy_unique_pairs_to_directory(unique_pairs, creditcards_dir)

    # Step 4: User interaction for uncensoring transactions
    transactions = read_transactions_from_csv(csv_file)
    transactions_to_uncensor = get_transactions_to_uncensor(transactions)
    run_censorer = ask_to_censor_when_file_is_present(creditcards_dir, tmpfiles)
    if run_censorer:
        run_transaction_censorer(creditcards_dir, transactions_to_uncensor)
        clean_and_combine_pdfs_in_creditcards_dir(creditcards_dir, tmpfiles.combined_creditcards_filename)

    # Step 5: Edit the ordering of files to include in the editor of choice
    pdf_files = list_pdf_files(output_dir, exclude_files = [ tmpfiles.descriptions_file_pdf, tmpfiles.application_file ])
    write_pdf_list_to_file(pdf_files, output_dir, tmpfiles)
    open_file_in_editor(state, tmpfiles.ordering_and_descriptions_file)

    # Step 6: Create reimbursement form
    create_reimbursement_form(state, output_dir, config_file, csv_file)

    # Step 7: Combine selected files into final report
    create_combined_pdf(output_dir, tmpfiles)

def list_pdf_files(directory, exclude_files=None):
    # Check if directory exists
    if not os.path.exists(directory):
        raise FileNotFoundError(f"Directory does not exist: {directory}")

    # Get the list of all files in the specified directory
    all_files = os.listdir(directory)

    # If exclude_files is not provided, use an empty list
    exclude_files = exclude_files or []

    # Convert the exclude_files to lowercase for case-insensitive comparison
    exclude_files_lower = [file.lower() for file in exclude_files]

    # Filter the list to include only .pdf files that are not in exclude_files
    pdf_files = [file for file in all_files if file.lower().endswith('.pdf') and file.lower() not in exclude_files_lower]

    return pdf_files

def write_pdf_list_to_file(pdf_files, output_dir, tmpfiles):
    latex_file = tmpfiles.descriptions_file
    output_file = tmpfiles.ordering_and_descriptions_file
    latex_file_path = os.path.join(output_dir, latex_file)
    with open(output_file, 'w') as f:
        # Write the PDF files list
        f.write("% Below is the list of pdf files in order that they will appear in the report. Feel free to reorder/delete/add extra files.\n")
        for pdf in pdf_files:
            f.write(f"{pdf}\n")
        
        # Write the LaTeX file contents
        f.write(f"\n% Below is the latex file {latex_file}. This will be a document, included at the start of your reimbursement. Add any extra information that you want, change the order of documents as they appear, etc.\n")
        f.write(f"\n%Latex Begin\n")
        with open(latex_file_path, 'r') as latex_f:
            f.write(latex_f.read())
    
    print(f"List of PDF files and LaTeX content written to {output_file}")

def clean_and_combine_pdfs_in_creditcards_dir(directory, output_pdf_name, debug=False):
    # Get the absolute path of the directory
    abs_directory = os.path.abspath(directory)
    if debug:
        print(f"Absolute path of the directory: {abs_directory}")
        print(f"Directory exists before changing: {os.path.exists(abs_directory)}")
    
    # Change to the specified directory
    script_dir=os.getcwd()
    os.chdir(abs_directory)
    if debug:
        print(f'We are in directory {os.getcwd()} now')
    
    # Verify the directory path again
        print(f"Directory exists after changing: {os.path.exists(abs_directory)}")
    
    # Step 1: Remove non-censored files
    for filename in os.listdir('.'):
        if debug:
            print(f'File found in directory: {filename}')
        if os.path.isfile(filename) and 'censored' not in filename:
            os.remove(filename)
            if debug:
                print(f"Removed: {filename}")
    
    # Step 2: Combine all .pdf files into a single PDF using PdfWriter
    writer = PdfWriter()
    for filename in sorted(os.listdir('.')):
        if filename.lower().endswith('.pdf'):
            file_path = os.path.join('.', filename)
            reader = PdfReader(file_path)
            for page in reader.pages:
                writer.add_page(page)
            if debug:
                print(f"Added {filename} to the writer.")

    output_path = os.path.join(abs_directory, output_pdf_name)
    with open(output_path, 'wb') as output_file:
        writer.write(output_file)
    if debug: 
        print(f"Combined PDF saved to: {output_path}")

    # Step 3: Remove censored files
    for filename in os.listdir('.'):
        if os.path.isfile(filename) and 'censored' in filename:
            os.remove(filename)
            if debug:
                print(f"Removed: {filename}")
    
    print(f"All PDFs combined into {output_pdf_name}")
    # Jump back to the script directory not to mess up relative paths
    os.chdir(script_dir)

def get_unique_file_page_pairs(csv_filename):
    unique_pairs = set()
    with open(csv_filename, 'r') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            unique_pairs.add((row['file'], row['page']))
    return unique_pairs

def create_output_directory(expense_reports_directory):
    output_dir = os.path.join(expense_reports_directory)
    os.makedirs(output_dir, exist_ok=True)
    return output_dir

def copy_unique_pairs_to_directory(unique_pairs, target_dir):
    for file_path, page_num in unique_pairs:
        pdf_reader = PdfReader(file_path)
        pdf_writer = PdfWriter()
        pdf_writer.add_page(pdf_reader.pages[int(page_num) - 1])
        output_filename = f"{os.path.basename(file_path)}_{page_num}.pdf"
        with open(os.path.join(target_dir, output_filename), "wb") as output_pdf:
            pdf_writer.write(output_pdf)

def read_transactions_from_csv(csv_filename):
    transactions = []
    with open(csv_filename, 'r') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            transactions.append(row)
    return transactions

def get_transactions_to_uncensor(transactions):
    #print("Select transactions to uncensor:")
    #for i, transaction in enumerate(transactions):
    #    print(f"[{i}] {transaction['date']}: ${transaction['amount']}")
    #selections = input("Enter the numbers of transactions to uncensor (comma-separated): ")
    #return [transactions[int(i)] for i in selections.split(',')]
    return transactions

def ask_to_censor_when_file_is_present(creditcards_dir, tmpfiles):
    """Checks if the censored transactions file exists and asks the user if they want to overwrite it"""
    run_censorer = True
    full_path = os.path.join( creditcards_dir, tmpfiles.combined_creditcards_filename)
    if os.path.exists(full_path):
        response = input("Censored transactions file was found. Would you like to use it (y) or redo censoring (n)? Default: y. ")
        if not response:
            response = 'y'
        if response.lower() == 'y':
            run_censorer = False
    return run_censorer



def run_transaction_censorer(creditcards_dir, transactions_to_uncensor):
    # Group transactions by file and page
    grouped_transactions = defaultdict(list)
    for transaction in transactions_to_uncensor:
        key = (transaction['file'], transaction['page'])
        grouped_transactions[key].append(transaction)

    # Iterate over each group and call the censor_transactions_mainloop function
    for (file, page), transactions in grouped_transactions.items():
        # Construct the PDF path
        pdf_name = f"{os.path.basename(file)}_{page}.pdf"
        pdf_path = os.path.join(creditcards_dir, pdf_name)

        # Display the transactions to the user
        print(f"Please uncensor the following transactions from {file} page {page}:")
        for transaction in transactions:
            print(f"- Date: {transaction['date']}, Amount: ${transaction['amount']}")

        # Call the censor_transactions_mainloop function
        censor_transactions_mainloop(pdf_path)
