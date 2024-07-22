from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from datetime import datetime
from python.full_reimbursement import define_table, getrow, generate_texts, manual_spending_insert, fill_expenses_from_csv
from python.define_table import define_reimbursement_table
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

def sum_floats_from_pdf_array(pdf_array):
    total_sum = 0.0
    for item in pdf_array:
        x, y, value, font, size = item
        if x == 140:
            print("success")
            try:
                value_float = float(value.replace('$', '').replace(',', ''))
                total_sum += value_float
            except ValueError:
                # Handle the case where value is not a float, continue to the next item
                continue
    total_sum_string = '$' + str(total_sum)
    return total_sum_string

def insert_into_pdf(mode, money_spent, date_str, input_file, output_file, config_file, csv_file):
    
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
    
    signature_path = "./config/signature.png"
    signature_path = os.path.abspath(signature_path)

    table_params = define_reimbursement_table()

    student_info = [
        (20,  38,   personnel_number, font, 2.5), # x, y, string, font, size
        (51,  44.5, student_initials, font, 2.5),
        (20,  44.5, student_lastname, font, 2.5),
        (20,  52,   student_address,  font, 2  ),
        (20,  116,  student_name,     font, 2.5),
        (20,  70,   dept_contact,     font, 2.5),
        (20,  90,   date,             font, 2.5),
    ]
    images = [
        (20, 90, signature_path, 30, 6),  # x, y, path, width, height
    ]

    fontsize = 2
    if mode == 'cosmolunch':
        texts = [
            (140, getrow(29, table_params), money_spent,      font, fontsize  ),
        ]
    elif mode == 'test':
        texts = generate_texts(font, table_params) # For testing purposes
    elif mode == 'custom':
        texts = fill_expenses_from_csv(table_params, font, fontsize, csv_file)
    elif mode == 'manual':
        texts = manual_spending_insert(table_params, font, fontsize)

    money_spent = sum_floats_from_pdf_array(texts)
    # Add total spent
    texts += [
        (140, getrow(35, table_params), money_spent,      font, 2  ),
        (140, getrow(37, table_params), money_spent,      font, 2  )
    ]
    texts += student_info
    
    insert_texts_and_images_to_pdf(input_file, output_file, texts, images)

def create_reimbursement_form(state, mode, output_dir, python_dir, signed_reimbursement_form_path, 
                              config_file, csv_file=None):
    current_date = datetime.now().strftime("%Y-%m-%d")
    application_file = os.path.join(output_dir, "application.pdf")
    insert_into_pdf(mode, state.selected_amount, current_date, signed_reimbursement_form_path, 
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
