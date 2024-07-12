import os
import sys
from PyPDF2 import PdfMerger, PdfReader, PdfWriter
from PIL import Image

def resize_and_rotate_page(page, width, height, rotate=False):
    page.cropbox.lower_left = (0, 0)
    page.cropbox.upper_right = (width, height)
    page.mediabox.lower_left = (0, 0)
    page.mediabox.upper_right = (width, height)
    if rotate:
        page.rotate(90)

def add_pdf_to_merger(merger, file_path, width, height, rotate=False):
    reader = PdfReader(file_path)
    writer = PdfWriter()
    for page_num in range(len(reader.pages)):
        page = reader.pages[page_num]
        resize_and_rotate_page(page, width, height, rotate)
        writer.add_page(page)
    temp_path = file_path.replace(".pdf", "_resized.pdf")
    with open(temp_path, "wb") as temp_file:
        writer.write(temp_file)
    merger.append(temp_path)
    os.remove(temp_path)

def combine_files_to_pdf(directory, output_filename):
    required_files = [
        "application.pdf",
        "announcement.pdf",
        "Signup_sheet.jpg",
        "receipt.pdf",
        "creditcard/1-censored.jpg"
    ]

    # Check for the existence of required files
    for file in required_files:
        if not os.path.exists(os.path.join(directory, file)):
            print(f"Missing file: {file}")
            return

    # Create a PdfMerger object
    merger = PdfMerger()

    # Define standard page size (e.g., letter size 8.5 x 11 inches)
    page_width, page_height = 612, 792  # Points (1 inch = 72 points)

    # Add the PDF files
    for file in ["application.pdf", "announcement.pdf", "receipt.pdf"]:
        file_path = os.path.join(directory, file)
        rotate = (file == "application.pdf")
        add_pdf_to_merger(merger, file_path, page_width, page_height, rotate)

    # Convert JPG to PDF and add
    for file in ["Signup_sheet.jpg", "creditcard/1-censored.jpg"]:
        file_path = os.path.join(directory, file)
        image = Image.open(file_path)
        image = image.convert("RGB")
        pdf_path = file_path.replace(".jpg", ".pdf")
        image = image.resize((int(page_width), int(page_height)), Image.LANCZOS)
        image.save(pdf_path)
        add_pdf_to_merger(merger, pdf_path, page_width, page_height)
        os.remove(pdf_path)  # Remove the temporary PDF file

    # Write the combined PDF to the output file
    output_path = os.path.join(directory, output_filename)
    merger.write(output_path)
    merger.close()

    print(f"Combined PDF saved as: {output_path}")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python combine_files_to_pdf.py <directory> <output_filename>")
        sys.exit(1)

    directory = sys.argv[1]
    output_filename = sys.argv[2]

    combine_files_to_pdf(directory, output_filename)
