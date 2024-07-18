import os
import sys
import subprocess
import argparse
from datetime import datetime
import re
from PyPDF2 import PdfReader, PdfWriter
from pdf2image import convert_from_path
from PIL import Image
import shutil

# Global variables
results = []
selected_result = ""
selected_file = ""
selected_page = ""
selected_month = ""
selected_day = ""
selected_amount = ""

def check_dependencies():
    try:
        import PyPDF2
        import pdf2image
    except ImportError:
        print("Required libraries not found. Please install PyPDF2 and pdf2image.")
        sys.exit(1)

def scan_pdfs(directory, search_string):
    global results
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith('.pdf'):
                file_path = os.path.join(root, file)
                try:
                    pdf = PdfReader(file_path)
                    for page_num, page in enumerate(pdf.pages, 1):
                        text = page.extract_text()
                        if search_string in text:
                            snippet = text[max(0, text.index(search_string) - 50):text.index(search_string) + 50]
                            results.append(f"{file_path}: Page {page_num}: {snippet}")
                except Exception as e:
                    print(f"Error processing {file_path}: {str(e)}")

def present_results(search_string):
    if not results:
        print(f"No occurrences of '{search_string}' found in any PDF files.")
        sys.exit(0)

    print(f"Found the following occurrences of '{search_string}':")
    for i, result in enumerate(results):
        print(f"[{i}] {result}")

def prompt_user_selection():
    global selected_result, selected_file, selected_page
    while True:
        try:
            selection = int(input("Enter the number of the occurrence you want to select: "))
            if 0 <= selection < len(results):
                selected_result = results[selection]
                selected_file, rest = selected_result.split(': Page ')
                selected_page = rest.split(':')[0]
                return
            else:
                print("Invalid selection. Please try again.")
        except ValueError:
            print("Invalid input. Please enter a number.")

def autoloop_selection(i):
    global selected_result, selected_file, selected_page
    if not (0 <= i < len(results)):
        print("Checking the last one...")
        return 1
    selected_result = results[i]
    selected_file, rest = selected_result.split(': Page ')
    selected_page = rest.split(':')[0]
    return 0

def extract_date_info():
    global selected_month, selected_day, selected_amount
    date_match = re.search(r'\b([A-Z]{3})\s+(\d{2})\b', selected_result)
    if date_match:
        month_abbr, selected_day = date_match.groups()
        month_dict = {'JAN': '01', 'FEB': '02', 'MAR': '03', 'APR': '04', 'MAY': '05', 'JUN': '06',
                      'JUL': '07', 'AUG': '08', 'SEP': '09', 'OCT': '10', 'NOV': '11', 'DEC': '12'}
        selected_month = month_dict.get(month_abbr, '??')
    
    amount_match = re.search(r'\$(\d+(\.\d{2})?)', selected_result)
    if amount_match:
        selected_amount = amount_match.group(1)

def find_first_date_after(year, month, day, directory):
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

def censor_transactions(output_dir, python_dir):
    creditcard_out_dir = os.path.join(output_dir, "creditcard")
    os.makedirs(creditcard_out_dir, exist_ok=True)

    # Extract the selected page
    pdf_writer = PdfWriter()
    pdf_reader = PdfReader(selected_file)
    pdf_writer.add_page(pdf_reader.pages[int(selected_page) - 1])
    with open(os.path.join(creditcard_out_dir, "1.pdf"), "wb") as output_pdf:
        pdf_writer.write(output_pdf)

    # Convert to JPEG
    convert_pdfs_to_jpegs(creditcard_out_dir, 300)

    print(f"\n\nNow you have to only enable transaction for {selected_month}-{selected_day}:")
    subprocess.run(["python", os.path.join(python_dir, "censor_transactions.py"), 
                    os.path.join(creditcard_out_dir, "1-1.jpg")])

    for file in os.listdir(creditcard_out_dir):
        if file.endswith((".pdf", ".jpg")) and not file.startswith("1-1"):
            os.remove(os.path.join(creditcard_out_dir, file))

def create_reimbursement_form(mode, output_dir, python_dir, signed_reimbursement_form_path):
    current_date = datetime.now().strftime("%Y-%m-%d")
    application_file = os.path.join(output_dir, "application.pdf")
    subprocess.run(["python", os.path.join(python_dir, "insert_into_pdf.py"), 
                    mode, selected_amount, current_date, signed_reimbursement_form_path, application_file])
    print(f"Saved to: {application_file}")

def combine_pdfs(output_dir, filename, python_dir):
    tmp_dir = "tmpbin"
    os.makedirs(tmp_dir, exist_ok=True)
    os.chdir(tmp_dir)

    subprocess.run(["pdflatex", f"../{output_dir}/description.tex"])
    shutil.move("description.pdf", f"../{output_dir}")
    
    subprocess.run(["python", os.path.join(python_dir, "combine_docs.py"), f"../{output_dir}", filename])
    
    os.chdir("..")
    shutil.rmtree(tmp_dir)

def run_python_scripts(mode, output_dir, final_report_filename, python_dir, signed_reimbursement_form_path):
    censor_transactions(output_dir, python_dir)
    create_reimbursement_form(mode, output_dir, python_dir, signed_reimbursement_form_path)
    combine_pdfs(output_dir, final_report_filename, python_dir)

def main():
    parser = argparse.ArgumentParser(description="Process PDF documents for expense reports.")
    parser.add_argument("estatements_directory", help="Directory containing eStatements PDFs")
    parser.add_argument("search_string", help="String to search for in PDFs")
    parser.add_argument("expense_reports_directory", help="Directory for expense reports")
    parser.add_argument("--autoloop", action="store_true", help="Enable autoloop mode")
    args = parser.parse_args()

    check_dependencies()
    scan_pdfs(args.estatements_directory, args.search_string)
    present_results(args.search_string)

    year = "2024"  # You might want to make this configurable
    final_report_filename = "combined_application.pdf"
    python_dir = os.path.join(os.getcwd(), "python")
    signed_reimbursement_form_path = "/home/vasilii/Documents/Expenses/2024/Cosmolunch/Reimbursement_form_with_sign.pdf"

    mode = "cosmolunch" if "Cosmolunch" in args.expense_reports_directory else "other"

    if not args.autoloop:
        prompt_user_selection()
        extract_date_info()
        print(f"Selected occurrence found in file '{selected_file}' on page {selected_page}.")
        print(f"Transaction Month: {selected_month}, Day: {selected_day}")
        print(f"Money amount: ${selected_amount}")
        closest_date = find_first_date_after(year, selected_month, selected_day, args.expense_reports_directory)
        print(f"Date of cosmolunch: {closest_date}")
        output_dir = os.path.join(args.expense_reports_directory, closest_date)
        run_python_scripts(mode, output_dir, final_report_filename, python_dir, signed_reimbursement_form_path)
    else:
        i = 0
        while True:
            print(f"Looking at the case {i}")
            if autoloop_selection(i) == 1:
                break
            extract_date_info()
            print(f"Selected occurrence found in file '{selected_file}' on page {selected_page}.")
            print(f"Transaction Month: {selected_month}, Day: {selected_day}")
            print(f"Money amount: ${selected_amount}")
            closest_date = find_first_date_after(year, selected_month, selected_day, args.expense_reports_directory)
            print(f"Date of cosmolunch: {closest_date}")
            output_dir = os.path.join(args.expense_reports_directory, closest_date)
            run_python_scripts(mode, output_dir, final_report_filename, python_dir, signed_reimbursement_form_path)
            i += 1
            print("\n")

if __name__ == "__main__":
    main()
