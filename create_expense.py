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

class ScriptState:
    def __init__(self):
        self.results = []
        self.selected_result = ""
        self.selected_file = ""
        self.selected_page = ""
        self.selected_month = ""
        self.selected_day = ""
        self.selected_amount = ""

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

def censor_single_transaction(state, output_dir, python_dir):
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
    censor_transactions_mainloop(image_path)

    for file in os.listdir(creditcard_out_dir):
        if file.endswith((".pdf", ".jpg")) and not file.startswith(image_name):
            os.remove(os.path.join(creditcard_out_dir, file))

def create_reimbursement_form(state, mode, output_dir, python_dir, signed_reimbursement_form_path):
    current_date = datetime.now().strftime("%Y-%m-%d")
    application_file = os.path.join(output_dir, "application.pdf")
    insert_into_pdf(mode, state.selected_amount, current_date, signed_reimbursement_form_path, application_file)
    print(f"Saved to: {application_file}")

def combine_pdfs(output_dir, filename, python_dir):
    tmp_dir = "tmpbin"
    os.makedirs(tmp_dir, exist_ok=True)
    os.chdir(tmp_dir)

    subprocess.run(["pdflatex", f"../{output_dir}/description.tex"])
    shutil.move("description.pdf", f"../{output_dir}")
    
    combine_files_to_pdf_with_exceptions(f"../{output_dir}", filename)
    
    os.chdir("..")
    shutil.rmtree(tmp_dir)

def run_python_scripts(state, mode, output_dir, final_report_filename, python_dir, signed_reimbursement_form_path):
    censor_single_transaction(state, output_dir, python_dir)
    create_reimbursement_form(state, mode, output_dir, python_dir, signed_reimbursement_form_path)
    combine_pdfs(output_dir, final_report_filename, python_dir)

def process_transactions_cosmolunch(state, year, args, mode, final_report_filename, python_dir, signed_reimbursement_form_path):
    if not args.autoloop:
        prompt_user_selection(state)
        extract_date_info(state)
        print(f"Selected occurrence found in file '{state.selected_file}' on page {state.selected_page}.")
        print(f"Transaction Month: {state.selected_month}, Day: {state.selected_day}")
        print(f"Money amount: ${state.selected_amount}")
        closest_date = find_first_date_after(year, state.selected_month, state.selected_day, args.expense_reports_directory)
        print(f"Date of cosmolunch: {closest_date}")
        output_dir = os.path.join(args.expense_reports_directory, closest_date)
        run_python_scripts(state, mode, output_dir, final_report_filename, python_dir, signed_reimbursement_form_path)
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
            run_python_scripts(state, mode, output_dir, final_report_filename, python_dir, signed_reimbursement_form_path)
            i += 1
            print("\n")

#----------------------------------------------

def process_transactions_custom(state, year, args, mode, final_report_filename, python_dir, signed_reimbursement_form_path):
    # Step 1: Use add_transactions_from_estatements to select transactions and save to CSV
    csv_filename = 'selected_transactions.csv'
    combined_creditcards_filename = 'combined_creditcards.pdf'
    csv_file = os.path.join(args.estatements_directory, csv_filename)
    add_transactions_from_estatements(args.estatements_directory, csv_file)

    # Step 2: Get unique file+page pairs from CSV
    unique_pairs = get_unique_file_page_pairs(csv_file)

    # Step 3: Copy unique pairs to creditcards directory
    output_dir = create_output_directory(args.expense_reports_directory)
    creditcards_dir = os.path.join(output_dir, 'creditcards')
    os.makedirs(creditcards_dir, exist_ok=True)
    copy_unique_pairs_to_directory(unique_pairs, creditcards_dir)

    # Step 4: User interaction for uncensoring transactions
    transactions = read_transactions_from_csv(csv_file)
    transactions_to_uncensor = get_transactions_to_uncensor(transactions)
    #convert_pdfs_to_jpegs(creditcards_dir, 300)
    #run_transaction_censorer(creditcards_dir, transactions_to_uncensor)
    clean_and_combine_pdfs_in_creditcards_dir(creditcards_dir, combined_creditcards_filename)

    # Step 5: Generate list of files to include
    all_files = get_all_files_recursively(output_dir)
    selected_files = user_select_and_order_files(all_files)

    # Step 6: Create reimbursement form
    create_reimbursement_form(state, mode, output_dir, python_dir, signed_reimbursement_form_path)

    # Step 7: Combine selected files into final report
    combine_selected_files(selected_files, output_dir, final_report_filename)

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

#----------------------------------------------

def parse_arguments():
    parser = argparse.ArgumentParser(description="Process PDF documents for expense reports.")
    parser.add_argument("estatements_directory", help="Directory containing eStatements PDFs")
    parser.add_argument("search_string", help="String to search for in PDFs")
    parser.add_argument("expense_reports_directory", help="Directory for expense reports")
    parser.add_argument("--autoloop", action="store_true", help="Enable autoloop mode")
    args = parser.parse_args()
    return args

def create_expense_main():

    args = parse_arguments()

    check_dependencies()
    
    state = ScriptState()

    year = "2024"  # You might want to make this configurable
    final_report_filename = "combined_application.pdf"
    python_dir = os.path.join(os.getcwd(), "python")
    signed_reimbursement_form_path = "/home/vasilii/Documents/Expenses/2024/Cosmolunch/Reimbursement_form_with_sign.pdf"

    mode = "cosmolunch" if "Cosmolunch" in args.expense_reports_directory else "other"
    #mode = "test"
    mode = "custom"

    if mode == "cosmolunch": 
        print("Cosmolunch mode")
        scan_pdfs(state, args.estatements_directory, args.search_string)
        present_results(state, args.search_string)
        process_transactions_cosmolunch(state, year, args, mode, final_report_filename, 
                                        python_dir, signed_reimbursement_form_path)
    elif mode == "custom": # Enter transactions from the receipts, and generate the report based on the eStatements
        print("Custom mode")
        process_transactions_custom(state, year, args, mode, final_report_filename, 
                                        python_dir, signed_reimbursement_form_path)


if __name__ == "__main__":
    create_expense_main()
