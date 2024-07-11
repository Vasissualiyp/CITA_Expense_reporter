from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import PyPDF2
import io

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

money_spent = "$"+ str(100)
date = "June 11, 2024"
input_file = "/home/vasilii/Documents/Expenses/2024/Cosmolunch/Reimbursement_form_with_sign.pdf"
output_file = "./output.pdf"

student_name = "Vasilii Pustovoit"
student_lastname = "Pustovoit"
student_initials = "V. I."

student_address = "Address, Toronto, ON, Canada"
personnel_number = "1234567"

signature_path = "./config/signature.png"

texts = [
    (20, 38, personnel_number, "Helvetica-Bold", 2.5), # x, y, string, font, size
    (51, 44.5, student_initials, "Helvetica-Bold", 2.5),
    (20, 44.5, student_lastname, "Helvetica-Bold", 2.5),
    (20, 52, student_address, "Helvetica-Bold", 2.5),
    (20, 116, student_name, "Helvetica-Bold", 2.5),
    (20, 90, date, "Helvetica-Bold", 2.5),
    (140, 122.5, money_spent, "Helvetica-Bold", 2),
    (140, 139,   money_spent, "Helvetica-Bold", 2),
    (140, 144.2, money_spent, "Helvetica-Bold", 2)
]
images = [
    (20, 90, "./config/signature.png", 30, 6),  # x, y, path, width, height
]


# Example usage
insert_texts_and_images_to_pdf(input_file, output_file, texts, images)
