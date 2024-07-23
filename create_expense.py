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
from python.insert_into_pdf import create_reimbursement_form
from python.censor_transactions import censor_transactions_mainloop
from python.custom_transactions import process_transactions_custom

class ScriptState:
    def __init__(self):
        self.results = []
        self.selected_result = ""
        self.selected_file = ""
        self.selected_page = ""
        self.selected_month = ""
        self.selected_day = ""
        self.selected_amount = ""
        self.final_report_filename = ""
        self.year = "2024"
        self.editor = "vim"
        self.mode = ""
        self.signed_reimbursement_form_path = "/home/vasilii/Documents/Expenses/2024/Cosmolunch/Reimbursement_form_with_sign.pdf"
        self.unsigned_reimbursement_form_path = "/home/vasilii/Documents/Expenses/Expense_form_empty.pdf"

def check_dependencies():
    try:
        import PyPDF2
        import pdf2image
    except ImportError:
        print("Required libraries not found. Please install PyPDF2 and pdf2image.")
        sys.exit(1)

def scan_pdfs(state, directory, search_string):
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith('.pdf'):
                file_path = os.path.join(root, file)
                try:
                    pdf = PdfReader(file_path)
                    for page_num, page in enumerate(pdf.pages, 1):
                        text = page.extract_text()
                        lines = text.split('\n')
                        for i, line in enumerate(lines):
                            if search_string in line:
                                # Get the full transaction line
                                transaction_line = line.strip()
                                # Get the next line for the amount if it exists
                                amount_line = lines[i+1].strip() if i+1 < len(lines) else ""
                                # Combine the transaction line and amount line
                                full_transaction = f"{transaction_line} {amount_line}"
                                state.results.append(f"{file_path}: Page {page_num}: {full_transaction}")
                except Exception as e:
                    print(f"Error processing {file_path}: {str(e)}")

def present_results(state, search_string):
    if not state.results:
        print(f"No occurrences of '{search_string}' found in any PDF files.")
        sys.exit(0)

    print(f"Found the following occurrences of '{search_string}':")
    for i, result in enumerate(state.results):
        print(f"[{i}] {result}")

def prompt_user_selection(state):
    while True:
        try:
            selection = int(input("Enter the number of the occurrence you want to select: "))
            if 0 <= selection < len(state.results):
                state.selected_result = state.results[selection]
                state.selected_file, rest = state.selected_result.split(': Page ')
                state.selected_page = rest.split(':')[0]
                return
            else:
                print("Invalid selection. Please try again.")
        except ValueError:
            print("Invalid input. Please enter a number.")

def autoloop_selection(state, i):
    if not (0 <= i < len(state.results)):
        print("Checking the last one...")
        return 1
    state.selected_result = state.results[i]
    state.selected_file, rest = state.selected_result.split(': Page ')
    state.selected_page = rest.split(':')[0]
    return 0

def extract_date_info(state):
    date_match = re.search(r'\b([A-Z]{3})\s+(\d{2})\b', state.selected_result)
    if date_match:
        month_abbr, state.selected_day = date_match.groups()
        month_dict = {'JAN': '01', 'FEB': '02', 'MAR': '03', 'APR': '04', 'MAY': '05', 'JUN': '06',
                      'JUL': '07', 'AUG': '08', 'SEP': '09', 'OCT': '10', 'NOV': '11', 'DEC': '12'}
        state.selected_month = month_dict.get(month_abbr, '??')
    
    amount_match = re.search(r'\$(\d+(\.\d{2})?)', state.selected_result)
    if amount_match:
        state.selected_amount = amount_match.group(1)
        print(f"Here is the amount found: {state.selected_amount}")

def find_first_date_after(year, month, day, directory):
    """
    Finds date for cosmolunch occurence in <directory>, given the date of the transaction, related 
    to the cosmolunch on <year>-<month>-<day>
    """
    input_date = datetime(int(year), int(month), int(day))
    closest_date = None

    for dir_name in os.listdir(directory):
        dir_path = os.path.join(directory, dir_name)
        if os.path.isdir(dir_path):
            try:
                dir_date = datetime.strptime(f"{year}-{dir_name}", "%Y-%m-%d")
                if dir_date >= input_date and (closest_date is None or dir_date < closest_date):
                    closest_date = dir_date
            except ValueError:
                continue

    if closest_date:
        return closest_date.strftime("%m-%d")
    else:
        print("No date found after the given date.")
        sys.exit(1)

def convert_pdfs_to_jpegs(output_dir, quality):
    for pdf_file in os.listdir(output_dir):
        if pdf_file.endswith('.pdf'):
            pdf_path = os.path.join(output_dir, pdf_file)
            base_name = os.path.splitext(pdf_file)[0]
            images = convert_from_path(pdf_path, dpi=quality)
            for i, image in enumerate(images):
                image.save(os.path.join(output_dir, f"{base_name}-{i+1}.jpg"), 'JPEG')
            os.remove(pdf_path)

def censor_single_transaction(state, output_dir):
    """
    Runs the transactions censorer for a single transaction
    """
    creditcard_out_dir = os.path.join(output_dir, "creditcard")
    os.makedirs(creditcard_out_dir, exist_ok=True)

    # Extract the selected page
    pdf_writer = PdfWriter()
    pdf_reader = PdfReader(state.selected_file)
    pdf_writer.add_page(pdf_reader.pages[int(state.selected_page) - 1])
    with open(os.path.join(creditcard_out_dir, "1.pdf"), "wb") as output_pdf:
        pdf_writer.write(output_pdf)

    # Convert to JPEG
    convert_pdfs_to_jpegs(creditcard_out_dir, 300)

    print(f"\n\nNow you have to only enable transaction for {state.selected_month}-{state.selected_day}:")
    image_name = "1-1"
    image_name_full = image_name + ".jpg"
    image_path = os.path.join(creditcard_out_dir, image_name_full)
    print("Keep in mind that censor_transactions_mainloop now only accepts pdfs!")
    print("Current implementation that we have here uses jpgs.") 
    print("You will have to edit the source to change this.")
    sys.exit(1)
    censor_transactions_mainloop(image_path)

    for file in os.listdir(creditcard_out_dir):
        if file.endswith((".pdf", ".jpg")) and not file.startswith(image_name):
            os.remove(os.path.join(creditcard_out_dir, file))

def combine_pdfs(output_dir, filename):
    tmp_dir = "tmpbin"
    os.makedirs(tmp_dir, exist_ok=True)
    os.chdir(tmp_dir)

    subprocess.run(["pdflatex", f"../{output_dir}/description.tex"])
    shutil.move("description.pdf", f"../{output_dir}")
    
    combine_files_to_pdf_with_exceptions(f"../{output_dir}", filename)
    
    os.chdir("..")
    shutil.rmtree(tmp_dir)

def run_python_scripts(state, mode, output_dir, final_report_filename, 
                       reimbursement_form_path, config_file):
    censor_single_transaction(state, output_dir)
    create_reimbursement_form(state, output_dir, reimbursement_form_path, config_file)
    combine_pdfs(output_dir, final_report_filename)

def process_transactions_cosmolunch(state, args, config_file):
    year = state.year
    mode = state.mode
    final_report_filename = state.final_report_filename 
    reimbursement_form_path = state.signed_reimbursement_form_path
    if not args.autoloop:
        prompt_user_selection(state)
        extract_date_info(state)
        print(f"Selected occurrence found in file '{state.selected_file}' on page {state.selected_page}.")
        print(f"Transaction Month: {state.selected_month}, Day: {state.selected_day}")
        print(f"Money amount: ${state.selected_amount}")
        closest_date = find_first_date_after(year, state.selected_month, state.selected_day, args.expense_reports_directory)
        print(f"Date of cosmolunch: {closest_date}")
        output_dir = os.path.join(args.expense_reports_directory, closest_date)
        run_python_scripts(state, mode, output_dir, final_report_filename, reimbursement_form_path, config_file)
    else:
        i = 0
        while True:
            print(f"Looking at the case {i}")
            if autoloop_selection(state, i) == 1:
                break
            extract_date_info(state)
            print(f"Selected occurrence found in file '{state.selected_file}' on page {state.selected_page}.")
            print(f"Transaction Month: {state.selected_month}, Day: {state.selected_day}")
            print(f"Money amount: ${state.selected_amount}")
            closest_date = find_first_date_after(year, state.selected_month, state.selected_day, args.expense_reports_directory)
            print(f"Date of cosmolunch: {closest_date}")
            output_dir = os.path.join(args.expense_reports_directory, closest_date)
            run_python_scripts(state, mode, output_dir, final_report_filename, reimbursement_form_path, config_file)
            i += 1
            print("\n")

def parse_arguments():
    parser = argparse.ArgumentParser(description="Process PDF documents for expense reports.")
    parser.add_argument("estatements_directory", help="Directory containing eStatements PDFs")
    parser.add_argument("expense_reports_directory", help="Directory for expense reports")
    parser.add_argument("mode", help="Program mode")
    parser.add_argument("search_string", help="String to search for in PDFs")
    parser.add_argument("--autoloop", action="store_true", help="Enable autoloop mode")
    args = parser.parse_args()
    args.estatements_directory = os.path.abspath(args.estatements_directory)
    args.expense_reports_directory = os.path.abspath(args.expense_reports_directory)
    return args

def create_expense_main():

    args = parse_arguments()

    check_dependencies()
    
    state = ScriptState()

    state.final_report_filename = "combined_application.pdf"
    config_file = './config/config.json'
    config_file = os.path.abspath(config_file)

    state.mode = args.mode
    #state.mode = "cosmolunch" if "Cosmolunch" in args.expense_reports_directory else "other"
    #state.mode = "test"
    #state.mode = "custom"

    if state.mode == "cosmolunch": 
        print("Cosmolunch mode")
        scan_pdfs(state, args.estatements_directory, args.search_string)
        present_results(state, args.search_string)
        process_transactions_cosmolunch(state, args, config_file)
    elif state.mode == "custom": # Enter transactions from the receipts, and generate the report based on the eStatements
        print("Custom mode")
        process_transactions_custom(state, args, config_file)
    elif state.mode == "test": 
        print("Test mode")
        scan_pdfs(state, args.estatements_directory, args.search_string)
        present_results(state, args.search_string)
        process_transactions_cosmolunch(state, args, config_file)
    else:
        print("Mode not supported")

if __name__ == "__main__":
    create_expense_main()
