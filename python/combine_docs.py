import os
import sys
import logging
import subprocess
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
        if os.path.exists(temp_path):
            os.remove(temp_path)
        logging.info(f"Successfully added {file_path} to merger")
    except Exception as e:
        logging.error(f"Error processing {file_path}: {str(e)}")
        raise

def combine_files_to_pdf(directory, output_filename):
    required_files = [
        "description.pdf",
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
    for file in ["description.pdf", "application.pdf", "announcement.pdf", "receipt.pdf"]:
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

def combine_files_to_pdf_with_exceptions(directory, output_filename):
    try:
        combine_files_to_pdf(directory, output_filename)
    except Exception as e:
        logging.error(f"An error occurred: {str(e)}")
        sys.exit(1)

#--------------------------

def compile_tex(tex_path):
    # Get the directory of the tex file and the base filename
    tex_dir = os.path.dirname(tex_path)
    base_name = os.path.basename(tex_path)
    file_name, _ = os.path.splitext(base_name)

    # Specify the directory for temporary files
    temp_dir = os.path.join(tex_dir, 'tmpdir')
    os.makedirs(temp_dir, exist_ok=True)  # Create temp_dir if it doesn't exist

    # Command to compile the TeX document
    command = [
        'pdflatex',
        '-output-directory', temp_dir,  # Output all auxiliary files to temp_dir
        '-jobname', file_name,          # Ensure the output PDF has the correct name
        tex_path                        # Path to the .tex source file
    ]

    # Execute the command
    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

    # Check if the compilation was successful
    if result.returncode != 0:
        print("Error compiling the document:")
        print(result.stdout)
        print(result.stderr)
    else:
        # Move the PDF back to the original directory if compilation is successful
        pdf_path = os.path.join(temp_dir, file_name + '.pdf')
        final_pdf_path = os.path.join(tex_dir, file_name + '.pdf')
        os.rename(pdf_path, final_pdf_path)
        print(f"Document compiled successfully. PDF saved to: {final_pdf_path}")

def create_combined_pdf(output_dir, tmpfiles):
    ordering_and_descriptions_file = tmpfiles.ordering_and_descriptions_file
    descriptions_file = tmpfiles.descriptions_file
    application_file = tmpfiles.application_file
    transactions_file = tmpfiles.combined_creditcards_filename 

    # Ensure output directories exist
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    parameters_dir = os.path.join(output_dir, "parameters")
    if not os.path.exists(parameters_dir):
        os.makedirs(parameters_dir)
    results_dir = os.path.normpath( os.path.join(output_dir, "../results") )
    if not os.path.exists(results_dir):
        os.makedirs(results_dir)
    
    # Initialize paths
    pdf_ordering_path = os.path.join(parameters_dir, "pdf_ordering.txt")
    descriptions_file = os.path.join(output_dir, descriptions_file)
    application_file = os.path.join(output_dir, application_file)
    transactions_file = os.path.join(output_dir, 'creditcards', transactions_file)
    # Paths for the final document
    output_pdf_name = os.path.basename(os.path.normpath(output_dir)) + ".pdf"
    output_pdf_path = os.path.join(results_dir, output_pdf_name)

    # Read ordering_and_descriptions_file and split its content
    with open(ordering_and_descriptions_file, 'r') as file:
        lines = file.readlines()

    # Separate parts before and after the beginning of the tex file
    before_document = []
    after_document = []
    document_started = False
    
    for line in lines:
        stripped_line = line.strip()
        
        # Check for the beginning of the actual LaTeX document
        if stripped_line.startswith(r"%Latex Begin"):
            document_started = True
            # Ensure the before document section ends here, including this line
            before_document.append(line)
            continue
        
        # Handle lines based on whether the document has started
        if not document_started:
            # Exclude full comment lines from the before_document
            if not stripped_line.startswith('%'):
                before_document.append(line)
        else:
            # All lines after the LaTeX document begins are part of after_document
            after_document.append(line)
    
    # Write the before_document content to pdf_ordering.txt, excluding comments and empty lines
    with open(pdf_ordering_path, 'w') as file:
        for line in before_document:
            if line.strip() and not line.strip().startswith('%'):
                file.write(line)

    # Write the after_document content to descriptions_file
    with open(descriptions_file, 'w') as file:
        for line in after_document:
            file.write(line)

    # Step 3: Compile the descriptions tex file (pseudocode)
    compile_tex(descriptions_file)
    descriptions_pdf = descriptions_file.replace('.tex', '.pdf')

    # Step 4: Combine the PDF files
    pdf_writer = PdfWriter()

    # Add descriptions.pdf
    add_pdf_to_writer(descriptions_pdf, pdf_writer)

    # Add application_file
    page_width = 612
    page_height = 792
    add_page_to_writer(pdf_writer, application_file, page_width, page_height, rotate=False)

    # Add PDF files from pdf_ordering.txt
    with open(pdf_ordering_path, 'r') as file:
        for line in file:
            pdf_path = line.strip()
            if pdf_path.lower().endswith('.pdf'):
                add_pdf_to_writer(os.path.join(output_dir, pdf_path), pdf_writer)

    # Add transactions_file
    add_pdf_to_writer(transactions_file, pdf_writer)

    # Save the resulting combined file
    if os.path.exists(output_pdf_path):
        os.remove(output_pdf_path) # Avoid duplicates
    with open(output_pdf_path, 'wb') as output_file:
        pdf_writer.write(output_file)

    print(f"Combined PDF saved to: {output_pdf_path}")

# Special function that is only used for application file
def add_page_to_writer(writer, file_path, width, height, rotate=False):
    logging.info(f"Processing file: {file_path}")
    try:
        reader = PdfReader(file_path)
        for page_num in range(len(reader.pages)):
            page = reader.pages[page_num]
            resize_and_rotate_page(page, width, height, rotate)
            writer.add_page(page)
        logging.info(f"Successfully added {file_path} to writer")
    except Exception as e:
        logging.error(f"Error processing {file_path}: {str(e)}")
        raise

def add_pdf_to_writer(pdf_path, pdf_writer):
    try:
        pdf_reader = PdfReader(pdf_path)
        for page in pdf_reader.pages:
            pdf_writer.add_page(page)
        print(f"Added {pdf_path} to the writer.")
    except Exception as e:
        print(f"Error adding {pdf_path}: {e}")

#--------------------------

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python combine_files_to_pdf.py <directory> <output_filename>")
        sys.exit(1)
    directory = sys.argv[1]
    output_filename = sys.argv[2]
    combine_files_to_pdf_with_exceptions(directory, output_filename)
