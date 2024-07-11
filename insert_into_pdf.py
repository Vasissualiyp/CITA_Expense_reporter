from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import PyPDF2
import io

def insert_text_to_pdf(input_pdf_path, output_pdf_path, text, x, y):
    # Read the existing PDF to determine the page size
    existing_pdf = PyPDF2.PdfReader(open(input_pdf_path, "rb"))
    output = PyPDF2.PdfWriter()

    for page in existing_pdf.pages:
        # Determine page dimensions
        page_width = page.mediabox.upper_right[0]
        page_height = page.mediabox.upper_right[1]

        # Rotate the page for proper text orientation (if necessary)
        page.rotate(270)  # Using the new rotate method

        # Create a new PDF to overlay text
        packet = io.BytesIO()
        can = canvas.Canvas(packet, pagesize=(page_width, page_height))
        can.saveState()  # Save the current state before making changes
        can.translate(x, y)
        can.rotate(90)
        can.drawString(0, 0, text)  # Draw the text at the new origin
        can.restoreState()  # Restore the canvas state
        can.save()

        # Move to the beginning of the StringIO buffer
        packet.seek(0)
        new_pdf = PyPDF2.PdfReader(packet)

        # Merge the text overlay onto the rotated page
        page.merge_page(new_pdf.pages[0])
        page.rotate(90)  # Rotate the page back to its original orientation

        # Add the processed page to the output PDF
        output.add_page(page)

    # Write the output PDF to file
    with open(output_pdf_path, "wb") as outputStream:
        output.write(outputStream)

# Example usage
insert_text_to_pdf("/home/vasilii/Documents/Expenses/2024/Cosmolunch/Reimbursement_form_with_sign.pdf", "./output.pdf", "Hello, this is some text", 100, 100)
