import os
import logging
import requests
from pathlib import Path
import fitz  # PyMuPDF
import tempfile

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Directory to save extracted images
IMAGE_DIRECTORY = Path(r"YOUR_DIRECTORY_PATH_FOR_IMAGE_SAVING")  # Update this to your desired folder

# Ensure the image directory exists
IMAGE_DIRECTORY.mkdir(parents=True, exist_ok=True)

def download_pdf(pdf_url):
    """
    Downloads the PDF from the given URL and saves it to a temporary file.
    Returns the path to the temporary PDF file and its bytes.
    """
    logger.info("Downloading PDF from URL...")
    response = requests.get(pdf_url)
    if response.status_code == 200:
        pdf_bytes = response.content
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_pdf:
            tmp_pdf.write(pdf_bytes)
            tmp_pdf_path = tmp_pdf.name
        logger.info(f"PDF downloaded and saved to temporary file: {tmp_pdf_path}")
        return tmp_pdf_path, pdf_bytes
    else:
        raise Exception(f"Failed to download PDF, status code {response.status_code}")

def extract_images_from_pdf_bytes(pdf_bytes, output_dir):
    """
    Extracts images from the PDF bytes using PyMuPDF and saves them to the output directory.
    Returns a list of image file paths.
    """
    logger.info("Extracting images from PDF...")
    if not output_dir.exists():
        output_dir.mkdir(parents=True, exist_ok=True)

    pdf_document = fitz.open(stream=pdf_bytes, filetype="pdf")
    image_paths = []

    for page_num in range(len(pdf_document)):
        page = pdf_document[page_num]
        image_list = page.get_images(full=True)
        logger.debug(f"Found {len(image_list)} images on page {page_num + 1}.")

        xref_seen = set()

        for img_index, img_info in enumerate(image_list):
            xref = img_info[0]
            if xref in xref_seen:
                continue  # Skip duplicate images
            xref_seen.add(xref)

            pix = fitz.Pixmap(pdf_document, xref)

            # Handle transparency
            if pix.alpha:
                pix = fitz.Pixmap(fitz.csRGB, pix)

            # Convert to RGB if necessary
            if pix.colorspace.n > 3:
                pix = fitz.Pixmap(fitz.csRGB, pix)

            image_filename = output_dir / f"page_{page_num + 1}_image_{img_index + 1}.png"
            pix.save(str(image_filename))
            image_paths.append(str(image_filename))
            pix = None  # Free memory
            logger.debug(f"Saved image: {image_filename}")

    pdf_document.close()
    logger.info(f"Extracted and saved {len(image_paths)} images.")
    return image_paths

if __name__ == "__main__":
    # Example cloud PDF URL
    pdf_url = "https://drive.usercontent.google.com/download?id=122VZMTBRCEawh3mdvwypda5RZqTRDJeM&authuser=0&acrobatPromotionSource=GoogleDriveNativeView"  # Replace with your actual URL

    try:
        # Step 1: Download PDF from URL
        tmp_pdf_path, pdf_bytes = download_pdf(pdf_url)

        # Step 2: Extract images and save to local directory
        image_paths = extract_images_from_pdf_bytes(pdf_bytes, IMAGE_DIRECTORY)
        logger.info(f"Images successfully extracted and saved: {image_paths}")
    finally:
        # Cleanup temporary file
        if os.path.exists(tmp_pdf_path):
            os.remove(tmp_pdf_path)
            logger.info(f"Temporary PDF file {tmp_pdf_path} removed.")
