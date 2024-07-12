import os
import sys
import logging
from PyPDF2 import PdfMerger, PdfReader, PdfWriter
from PIL import Image

#logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')


def resize_and_rotate_page(page, target_width, target_height, rotate=False):
    logging.debug(f"Original page size: {page.mediabox.width} x {page.mediabox.height}")

    # A factor by which the application table is being scaled, to make sure that it fits
    # into the final pdf
    scale_nudge = 0.8

    # Rotation is not currently working!
    rotate = False
    
    # Get the original mediabox dimensions
    orig_left = float(page.mediabox.left)
    orig_bottom = float(page.mediabox.bottom)
    orig_right = float(page.mediabox.right)
    orig_top = float(page.mediabox.top)
    orig_width = orig_right - orig_left
    orig_height = orig_top - orig_bottom

    if rotate:
        page.rotate(90)
        orig_width, orig_height = orig_height, orig_width
        target_width, target_height = target_height, target_width

    # Calculate scaling factors
    width_scale = target_width / orig_width
    height_scale = target_height / orig_height

    # Use the smaller scaling factor to ensure entire content fits
    scale = min(width_scale, height_scale)
    scale = scale_nudge * scale

    # Calculate new dimensions
    new_width = orig_width * scale
    new_height = orig_height * scale

    # Adjust target dimensions if necessary
    target_width = max(target_width, new_width)
    target_height = max(target_height, new_height)

    # Calculate centering offsets
    x_offset = 0 #(target_width - new_width) / 2
    y_offset = 0 #(target_height - new_height) / 2

    # Create a new transformation matrix
    ctm = [scale, 0, 0, scale, x_offset, y_offset]

    # Apply the transformation matrix
    page.add_transformation(ctm)

    # Update mediabox and cropbox to the new target size
    page.mediabox.lower_left = (0, 0)
    page.mediabox.upper_right = (target_width, target_height)
    page.cropbox.lower_left = (0, 0)
    page.cropbox.upper_right = (target_width, target_height)

    logging.debug(f"New page size: {page.mediabox.width} x {page.mediabox.height}")
    logging.debug(f"Scale factor: {scale}")
    logging.debug(f"New content size: {new_width} x {new_height}")

    return target_width, target_height

def convert_images_to_pdf(file_path, pdf_path, page_width, page_height, dpi=100):
    image = Image.open(file_path)
    image = image.convert("RGB")
    # Calculate the new dimensions based on DPI
    width, height = image.size
    width_in_points = (width / dpi) * 72
    height_in_points = (height / dpi) * 72
    image = image.resize((int(width_in_points), int(height_in_points)), Image.LANCZOS)
    image.save(pdf_path, dpi=(dpi, dpi))

def add_pdf_to_merger(merger, file_path, width, height, rotate=False):
    logging.info(f"Processing file: {file_path}")
    try:
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
        logging.info(f"Successfully added {file_path} to merger")
    except Exception as e:
        logging.error(f"Error processing {file_path}: {str(e)}")
        raise

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
        file_path = os.path.join(directory, file)
        if not os.path.exists(file_path):
            logging.error(f"Missing file: {file_path}")
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
        pdf_path = file_path.replace(".jpg", ".pdf")
        convert_images_to_pdf(file_path, pdf_path, page_width, page_height)
        add_pdf_to_merger(merger, pdf_path, page_width, page_height)
        os.remove(pdf_path)  # Remove the temporary PDF file
    
    # Write the combined PDF to the output file
    output_path = os.path.join(directory, output_filename)
    merger.write(output_path)
    merger.close()
    logging.info(f"Combined PDF saved as: {output_path}")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python combine_files_to_pdf.py <directory> <output_filename>")
        sys.exit(1)
    directory = sys.argv[1]
    output_filename = sys.argv[2]
    try:
        combine_files_to_pdf(directory, output_filename)
    except Exception as e:
        logging.error(f"An error occurred: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python combine_files_to_pdf.py <directory> <output_filename>")
        sys.exit(1)
    directory = sys.argv[1]
    output_filename = sys.argv[2]
    try:
        combine_files_to_pdf(directory, output_filename)
    except Exception as e:
        logging.error(f"An error occurred: {str(e)}")
        sys.exit(1)
