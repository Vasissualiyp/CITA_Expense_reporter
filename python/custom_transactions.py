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
from python.add_transactions import add_transactions_from_estatements
from python.insert_into_pdf import insert_into_pdf
from python.censor_transactions import censor_transactions_mainloop
#from create_expense import create_reimbursement_form

def process_transactions_custom(state, year, args, mode, final_report_filename, python_dir, signed_reimbursement_form_path):
    print("We are doing custom transactions now")
    # Step 1: Use add_transactions_from_estatements to select transactions and save to CSV
    csv_filename = 'selected_transactions.csv'
    combined_creditcards_filename = 'combined_creditcards.pdf'
    csv_file = os.path.join(args.estatements_directory, csv_filename)
    add_transactions_from_estatements(args.estatements_directory, csv_file)

    # Step 2: Get unique file+page pairs from CSV
    unique_pairs = get_unique_file_page_pairs(csv_file)

    # Step 3: Copy unique pairs to creditcards directory
    output_dir = create_output_directory(args.expense_reports_directory)
    output_dir = os.path.abspath(output_dir)
    creditcards_dir = os.path.join(output_dir, 'creditcards')
    os.makedirs(creditcards_dir, exist_ok=True)
    copy_unique_pairs_to_directory(unique_pairs, creditcards_dir)

    # Step 4: User interaction for uncensoring transactions
    transactions = read_transactions_from_csv(csv_file)
    transactions_to_uncensor = get_transactions_to_uncensor(transactions)
    #convert_pdfs_to_jpegs(creditcards_dir, 300)
    #run_transaction_censorer(creditcards_dir, transactions_to_uncensor)
    clean_and_combine_pdfs_in_creditcards_dir(creditcards_dir, combined_creditcards_filename)

    # Edit the files ordering in editor of choice
    editor = 'vim'
    output_file = 'pdfs_order.txt'
    pdf_files = list_pdf_files(output_dir)
    write_pdf_list_to_file(pdf_files, output_file)
    open_file_in_editor(editor, output_file)

    # Step 5: Generate list of files to include
    #all_files = get_all_files_recursively(output_dir)
    #selected_files = user_select_and_order_files(all_files)

    # Step 6: Create reimbursement form
    create_reimbursement_form(state, mode, output_dir, python_dir, signed_reimbursement_form_path)

    # Step 7: Combine selected files into final report
    combine_selected_files(selected_files, output_dir, final_report_filename)

def list_pdf_files(directory):
    # Check if directory exists
    if not os.path.exists(directory):
        raise FileNotFoundError(f"Directory does not exist: {directory}")

    # Get the list of all files in the specified directory
    all_files = os.listdir(directory)

    # Filter the list to include only .pdf files and remove the directory path
    pdf_files = [file for file in all_files if file.lower().endswith('.pdf')]

    return pdf_files

def write_pdf_list_to_file(pdf_files, output_file):
    with open(output_file, 'w') as f:
        for pdf in pdf_files:
            f.write(f"{pdf}\n")
    print(f"List of PDF files written to {output_file}")

def open_file_in_editor(editor, file_path):
    subprocess.run([editor, file_path])

def clean_and_combine_pdfs_in_creditcards_dir(directory, output_pdf_name, debug=False):
    # Get the absolute path of the directory
    abs_directory = os.path.abspath(directory)
    if debug:
        print(f"Absolute path of the directory: {abs_directory}")
        print(f"Directory exists before changing: {os.path.exists(abs_directory)}")
    
    # Change to the specified directory
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
    
    ## Step 2: Convert .jpg files to .pdf
    #for filename in os.listdir('.'):
    #    if filename.lower().endswith('.jpg'):
    #        image_path = filename
    #        pdf_path = image_path.rsplit('.', 1)[0] + '.pdf'
    #        with Image.open(image_path) as img:
    #            img.convert('RGB').save(pdf_path)
    #        os.remove(image_path)
    #        print(f"Converted {filename} to PDF and removed the original .jpg file.")
    
    # Step 3: Combine all .pdf files into a single PDF using PdfWriter
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

    # Step 4: Remove censored files
    for filename in os.listdir('.'):
        if os.path.isfile(filename) and 'censored' in filename:
            os.remove(filename)
            if debug:
                print(f"Removed: {filename}")
    
    print(f"All PDFs combined into {output_pdf_name}")

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

def get_all_files_recursively(directory):
    all_files = []
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith('.pdf'):
                all_files.append(os.path.join(root, file))
    return all_files

def user_select_and_order_files(all_files):
    print("Available files:")
    for i, file in enumerate(all_files):
        print(f"[{i}] {file}")
    
    # Pseudocode: Open vim for user to edit and reorder files
    # selected_files = open_vim_for_user_to_edit(all_files)
    
    # For now, we'll use a simple input method
    selections = input("Enter the numbers of files to include (comma-separated): ")
    selected_files = [all_files[int(i)] for i in selections.split(',')]
    return selected_files

def combine_selected_files(selected_files, output_dir, final_report_filename):
    pdf_writer = PdfWriter()
    for file in selected_files:
        pdf_reader = PdfReader(file)
        for page in pdf_reader.pages:
            pdf_writer.add_page(page)
    
    output_path = os.path.join(output_dir, final_report_filename)
    with open(output_path, "wb") as output_pdf:
        pdf_writer.write(output_pdf)
    print(f"Combined PDF saved to: {output_path}")
