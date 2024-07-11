from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import PyPDF2
import io

def insert_multiple_texts_to_pdf(input_pdf_path, output_pdf_path, texts):
    # Open the existing PDF
    existing_pdf = PyPDF2.PdfReader(open(input_pdf_path, "rb"))
    output_pdf = PyPDF2.PdfWriter()

    # Create a single PDF in memory to overlay text on all pages
    packet = io.BytesIO()
    can = canvas.Canvas(packet, pagesize=letter)  # Ensure the canvas size matches your PDF page size

    # Add each text to the overlay PDF
    for text_details in texts:
        x, y, text, font_name, font_size = text_details
        can.saveState()  # Save the current graphical state
        can.translate(x, y)  # Move to the coordinate where the text will start
        can.rotate(90)  # Rotate the canvas so the text will be horizontal
        can.setFont(font_name, font_size)
        can.drawString(0, 0, text)  # Draw the text at the new origin
        can.restoreState()  # Restore the graphical state

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

money_spent = "$"+ str(100)
date = "June 11, 2024"
input_file = "/home/vasilii/Documents/Expenses/2024/Cosmolunch/Reimbursement_form_with_sign.pdf"
output_file = "./output.pdf"

student_name = "Vasilii Pustovoit"
student_lastname = "Pustovoit"
student_initials = "V. I."

student_address = "Address, Toronto, ON, Canada"
personnel_number = "1234567"

texts = [
    (38, 20, personnel_number, "Helvetica-Bold", 2.5),
    (44.5, 51, student_initials, "Helvetica-Bold", 2.5),
    (44.5, 20, student_lastname, "Helvetica-Bold", 2.5),
    (52, 20, student_address, "Helvetica-Bold", 2.5),
    (116, 20, student_name, "Helvetica-Bold", 2.5),
    (90, 20, date, "Helvetica-Bold", 2.5),
    (122.5, 140, money_spent, "Helvetica-Bold", 2),
    (139,   140, money_spent, "Helvetica-Bold", 2),
    (144.2, 140, money_spent, "Helvetica-Bold", 2)
]

# Example usage
scale = 0.5
insert_multiple_texts_to_pdf(input_file, output_file, texts)
