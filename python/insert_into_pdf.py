from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from datetime import datetime
from python.full_reimbursement import define_table, getrow, generate_texts, manual_spending_insert, fill_expenses_from_csv
from python.define_table import define_reimbursement_table
from datetime import datetime
import PyPDF2
import io
import os
import sys
import json

# Function to read configuration from a JSON file
def read_config(config_file):
    with open(config_file, 'r') as file:
        config = json.load(file)
    return config

def insert_texts_and_images_to_pdf(input_pdf_path, output_pdf_path, texts, images):
    # Open the existing PDF
    existing_pdf = PyPDF2.PdfReader(open(input_pdf_path, "rb"))
    output_pdf = PyPDF2.PdfWriter()

    # Create a single PDF in memory to overlay texts and images on all pages
    packet = io.BytesIO()
    can = canvas.Canvas(packet, pagesize=letter)  # Ensure the canvas size matches your PDF page size

    # Add each text to the overlay PDF
    for text_details in texts:
        y, x, text, font_name, font_size = text_details
        can.saveState()  # Save the current graphical state
        can.translate(x, y)  # Move to the coordinate where the text will start
        can.rotate(90)
        can.setFont(font_name, font_size)
        can.drawString(0, 0, text)  # Draw the text at the new origin
        can.restoreState()  # Restore the graphical state

    # Add each image to the overlay PDF
    for image_details in images:
        y, x, image_path, width, height = image_details
        can.saveState()  # Save the current graphical state before rotating
        can.translate(x + width / 2, y + height / 2)  # Move the origin to the center of the image
        can.rotate(90)  # Rotate the canvas by 90 degrees
        can.drawImage(image_path, -width / 2, -height / 2, width=width, height=height, mask='auto')  # Draw the image centered on the new origin
        can.restoreState()

    can.save()

    # Move to the beginning of the StringIO buffer and create a PDF reader
    packet.seek(0)
    overlay_pdf = PyPDF2.PdfReader(packet)

    # Iterate over each page in the original PDF and merge the overlay
    for page_number in range(len(existing_pdf.pages)):
        page = existing_pdf.pages[page_number]
        page.merge_page(overlay_pdf.pages[0])
        output_pdf.add_page(page)

    # Write the modified PDF to a file
    with open(output_pdf_path, "wb") as outputStream:
        output_pdf.write(outputStream)

def convert_date_to_string(date_str):
    # Parse the input date string
    date_obj = datetime.strptime(date_str, '%Y-%m-%d')
    
    # Convert to the desired format
    formatted_date = date_obj.strftime('%B %d, %Y')
    
    return formatted_date

def sum_floats_from_pdf_array(pdf_array, x_transaction):
    total_sum = 0.0
    print(pdf_array)
    for item in pdf_array:
        x, y, value, font, size = item
        if x == x_transaction:
            print("success")
            try:
                value_float = float(value.replace('$', '').replace(',', ''))
                total_sum += value_float
            except ValueError:
                # Handle the case where value is not a float, continue to the next item
                continue
    total_sum_string = '$' + str(total_sum)
    return total_sum_string

def ask_for_travel_dates():
    def get_date_input(prompt):
        """ Helper function to get a valid date input from the user. """
        while True:
            date_input = input(prompt).strip()
            if not date_input:
                return None
            try:
                return datetime.strptime(date_input, "%Y-%m-%d")
            except ValueError:
                print("Invalid date format. Please use YYYY-MM-DD format.")

    # Ask user for the start date
    start_date = get_date_input("Enter the start date of your travel (YYYY-MM-DD): ")
    if start_date is None:
        return ""

    # Ask user for the end date
    end_date = get_date_input("Enter the end date of your travel (YYYY-MM-DD): ")
    if end_date is None:
        return ""

    # Formatting the date string based on whether the years are the same or different
    if start_date.year == end_date.year:
        if start_date.month == end_date.month:
            date_string = start_date.strftime('%b %d') + ' - ' + end_date.strftime('%d, %Y')
        else:
            date_string = start_date.strftime('%b %d') + ' - ' + end_date.strftime('%b %d, %Y')
    else:
        date_string = start_date.strftime('%b %d, %Y') + ' - ' + end_date.strftime('%b %d, %Y')
    
    return date_string

def split_string(s, max_chars):
    words = s.split()
    
    # Check if any word exceeds the maximum allowed characters
    if any(len(word) > max_chars for word in words):
        raise ValueError(f"One or more words are too long to fit within the limit of {max_chars} characters")
    
    # Attempt to split the string into two parts without exceeding max_chars
    first_part = ""
    second_part = ""
    
    for word in words:
        if len(first_part) + len(word) + (1 if first_part else 0) <= max_chars:
            first_part += (" " + word if first_part else word)
        elif len(second_part) + len(word) + (1 if second_part else 0) <= max_chars:
            second_part += (" " + word if second_part else word)
        else:
            raise ValueError("The string is too long to split into two parts.")
    
    return first_part.strip(), second_part.strip()

# Example of wrapping this function into user input handling
def ask_for_purpose(max_chars):
    while True:
        user_input = input("Enter a purpose of reimbursement (or type 'exit' to quit): ")
        if user_input.lower() == 'exit':
            print("Exiting the program.")
            break
        
        try:
            part1, part2 = split_string(user_input, max_chars)
            return part1, part2
        except ValueError as e:
            print(f"Error: {e}")

def insert_into_pdf(mode, money_spent, date_str, input_file, output_file, config_file, csv_file):
    
    def row(n):
        return getrow(n, table_params)

    # Put provided date into a nice format
    date = convert_date_to_string(date_str)

    # Read the configuration file
    config = read_config(config_file)
    
    # Access the configuration values
    student_name = config['student_name']
    student_lastname = config['student_lastname']
    student_initials = config['student_initials']
    font = config['font']
    student_address = config['student_address']
    personnel_number = config['personnel_number']
    dept_contact = config['department_contact']
    department = config['department']
    dept_telephone = config['dept_telephone']
    dept_fax = config['dept_fax']
    student_title = config['claimant_title']
    approver_name = config['authorized_approver_name']
    approver_title = config['authorized_approver_title']
    currency = config['currency']
    
    signature_path = "./config/signature.png"
    signature_path = os.path.abspath(signature_path)

    table_params, reimb_table_col, fontsizes, signature_params = define_reimbursement_table(mode)

    purpose1, purpose2 = ask_for_purpose(40)

    travel_dates = ask_for_travel_dates()
    travel_dates_col = (reimb_table_col[0] + 2 * reimb_table_col[1])/3

    student_info = [ 
        #x,                  y,       string,           font, size
        (reimb_table_col[0], row(-1), personnel_number, font, fontsizes[1]),
        (reimb_table_col[1], row(1 ), student_initials, font, fontsizes[1]),
        (reimb_table_col[0], row(1 ), student_lastname, font, fontsizes[1]),
        (reimb_table_col[0], row(3.5),student_address,  font, fontsizes[0]),
        (reimb_table_col[0], row(26.8), student_name,   font, fontsizes[1]),
        (reimb_table_col[0], row(10), dept_contact,     font, fontsizes[1]),
        (reimb_table_col[0], row(17), date,             font, fontsizes[1]),
        (travel_dates_col,   row(-1), travel_dates,     font, fontsizes[0]),
    ]
    other_info = [ 
        #x,                  y,       string,           font, size
        (reimb_table_col[0], row(13), department,       font, fontsizes[0]),
        (reimb_table_col[0], row(6.5),purpose1,         font, fontsizes[1]),
        (reimb_table_col[0], row(7.5),purpose2,         font, fontsizes[1]),
        (reimb_table_col[0], row(15), dept_telephone,   font, fontsizes[1]),
        (reimb_table_col[1], row(15), dept_fax,         font, fontsizes[1]),
        (reimb_table_col[1], row(26.8),student_title,   font, fontsizes[1]),
        (reimb_table_col[0], row(36), approver_name,    font, fontsizes[0]),
        (reimb_table_col[1], row(36), approver_title,   font, fontsizes[1]),
    ]
    images = [
        (reimb_table_col[0], row(signature_params[0]), signature_path, signature_params[1], signature_params[2]),  # x, y, path, width, height
    ]

    if currency == 'CAD':
        currency_row = -6.6
    elif currency == 'USD':
        currency_row = -5.6
    else:
        currency_row = -4.6

    currency = [
        (reimb_table_col[3]*0.82, row(currency_row), 'X', font, fontsizes[1]),  # x, y, path, width, height
    ]

    if mode == 'cosmolunch':
        texts = [
            (reimb_table_col[3], row(29), money_spent, font, fontsizes[0]),
        ]
    elif mode == 'test':
        texts = generate_texts(font, table_params) # For testing purposes
    elif mode == 'custom':
        texts = fill_expenses_from_csv(table_params, font, fontsizes[0], reimb_table_col[2], reimb_table_col[3], csv_file)
        texts+= other_info
    elif mode == 'manual':
        texts = manual_spending_insert(table_params, font, fontsizes[0] )

    money_spent = sum_floats_from_pdf_array(texts, reimb_table_col[3])
    # Add total spent
    texts += [
        (reimb_table_col[3], row(35), money_spent, font, fontsizes[0] ),
        (reimb_table_col[3], row(37), money_spent, font, fontsizes[0] )
    ]
    texts += student_info
    texts += currency
    
    insert_texts_and_images_to_pdf(input_file, output_file, texts, images)

def create_reimbursement_form(state, output_dir, config_file, csv_file=None):
    mode = state.mode 

    if mode == 'custom':
        reimbursement_form_path = state.unsigned_reimbursement_form_path
    else:
        reimbursement_form_path = state.signed_reimbursement_form_path

    current_date = datetime.now().strftime("%Y-%m-%d")
    application_file = os.path.join(output_dir, "application.pdf")
    insert_into_pdf(mode, state.selected_amount, current_date, reimbursement_form_path, 
                    application_file, config_file, csv_file)
    print(f"Saved to: {application_file}")

if __name__ == "__main__":
    if len(sys.argv) != 6:
        print("Usage: python insert_into_pdf.py <mode> <money_spent> <date> <input_pdf> <output_pdf>")
        sys.exit(1)

    mode = sys.argv[1] # cosmology, test or other
    money_spent = sys.argv[2] # How much money was spent (only relevant for cosmology)
    date = sys.argv[3] # Today's date
    input_file = sys.argv[4] # Base pdf which will be altered
    output_file = sys.argv[5] # Where to save the resulting pdf

    insert_into_pdf(mode, money_spent, date, input_file, output_file)
