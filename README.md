# CITA Expense Report Generator

## Description
This project provides a set of scripts and tools to generate expense reports for CITA (Canadian Institute for Theoretical Astrophysics). It automates the process of extracting transaction data from PDF statements, censoring sensitive information, and generating a reimbursement form.

## Requirements
- `pdftoppm`
- `pdftk`
- Python 3 with the following packages:
  - `tkinter`
  - `Pillow`
  - `reportlab`
  - `PyPDF2`
  - `pdf2image`
- Nix (for setting up the development environment)

## Installation
1. **Clone the repository:**
    ```sh
    git clone https://github.com/Vasissualiyp/CITA_Expense_reporter.git
    cd CITA_Expense_reporter
    ```

2a. (If using Nix with flakes) **Set up the development environment using Nix:**
    ```sh
    nix develop
    ```
	
2b. (If not using Nix) **Install the dependencies**

    Set up your python environment with dependencies listed above.
    Also, make sure that pdftoppm and pdftk are installed.

## Configuration
Create a configuration file `config.json` in the `config` directory with the following structure:
```json
{
    "student_name": "Vasilii Pustovoit",
    "student_lastname": "Pustovoit",
    "student_initials": "V. P.",
    "font": "Helvetica-Bold",
    "student_address": "Address, City, ON, Canada",
    "personnel_number": "1234567",
    "department_contact": "Alice Smith"
}
```

## Usage
### Generate Expense Report (Cosmolunch)
Run the `python create_expense.py` script to generate an expense report. This script performs the following steps:
1. Searches PDF eStatements for a specified transaction.
2. Extracts transaction information (date, amount).
3. Finds the first cosmolunch date after the transaction date.
4. Censors the transaction details in the PDF.
5. Creates a reimbursement form and inserts the extracted information.

```sh
./create_expense.sh <ESTATEMENTS_DIRECTORY> <SEARCH_STRING> <EXPENSE_REPORTS_DIRECTORY>
```


### Example
```sh
./create_expense.sh /path/to/statements "PIZZAIOLO" /path/to/expense_reports
```

What is important is that the code is written for RBC (Royal Bank Canada) eStatements, 
and other banks' formats haven't been yet tested. 
Feel free to open a pull request and add yours!

Another very important thing is that the script will automatically choose a "cosmolunch" mode if 
your expense reports path contains a string "Cosmolunch". Otherwise it will default to "other".

### Scripts and Their Functions

#### `flake.nix`
Sets up the development environment using Nix, including the required dependencies.

#### `create_expense.sh/create_expense.py`
Main script to create the expense report.
- Checks for `pdfgrep` installation.
- Scans PDF files for a search string.
- Prompts the user to select a transaction.
- Extracts date and amount information from the selected transaction.
- Finds the first cosmolunch date after the transaction date.
- Converts the relevant PDF pages to JPEG for censorship.
- Calls Python scripts to censor transactions and create the reimbursement form.

#### `insert_into_pdf.py`
Inserts text and images into a PDF to create the reimbursement form.
- Reads configuration values from `config.json`.
- Inserts the extracted transaction information into the expense report PDF.

#### `censor_transactions.py`
Provides a GUI to censor sensitive information in the transaction images.
- Uses Tkinter for the GUI.
- Allows the user to draw black rectangles over sensitive information.
- Saves the censored image.

## License
This project is licensed under the MIT License.
