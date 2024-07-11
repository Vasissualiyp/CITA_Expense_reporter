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
    can = canvas.Canvas(packet)

    # Add each text to the overlay PDF
    for text_details in texts:
        x, y, text, font_name, font_size = text_details
        can.setFont(font_name, font_size)
        can.drawString(x, y, text)

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

# Example usage
texts = [
    (100, 100, "Hello, this is some text", "Helvetica", 12),
    (20, 20, "Another line here", "Helvetica", 14),
    (50, 50, "Third line, different place", "Helvetica", 16)
]

# Example usage
scale = 0.5
insert_multiple_texts_to_pdf("/home/vasilii/Documents/Expenses/2024/Cosmolunch/Reimbursement_form_with_sign.pdf", "./output.pdf", texts)
