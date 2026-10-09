import os
import pdfplumber
from PIL import Image
from config import EXTRACTED_FOLDER


def process_pdf(pdf_path, lecture_id):
    """
    Extract text and images from a PDF file.

    Returns:
        tuple: (extracted_text, list of image paths)
    """
    all_text = []
    image_paths = []

    # Create folder for this lecture's images
    lecture_images_folder = os.path.join(EXTRACTED_FOLDER, str(lecture_id))
    os.makedirs(lecture_images_folder, exist_ok=True)

    with pdfplumber.open(pdf_path) as pdf:
        for page_num, page in enumerate(pdf.pages):
            # Extract text
            text = page.extract_text()
            if text and text.strip():
                all_text.append(f"--- Page {page_num + 1} ---\n{text}")

            # Extract images from the page
            if page.images:
                for img_index, img in enumerate(page.images):
                    try:
                        # Get the image bbox and crop from page
                        x0 = img['x0']
                        y0 = img['top']
                        x1 = img['x1']
                        y1 = img['bottom']

                        # Crop the image from the page
                        cropped = page.crop((x0, y0, x1, y1))
                        pil_image = cropped.to_image(resolution=150).original

                        # Save image
                        image_filename = f"page{page_num + 1}_img{img_index + 1}.png"
                        image_path = os.path.join(lecture_images_folder, image_filename)
                        pil_image.save(image_path)

                        # Store relative path for web serving
                        relative_path = f"uploads/extracted/{lecture_id}/{image_filename}"
                        image_paths.append({
                            'path': relative_path,
                            'page': page_num + 1
                        })

                    except Exception as e:
                        print(f"Error extracting image on page {page_num + 1}: {e}")
                        continue

            # If no embedded images found, save page as image (useful for slide decks)
            if not page.images:
                try:
                    pil_image = page.to_image(resolution=150).original

                    image_filename = f"page{page_num + 1}.png"
                    image_path = os.path.join(lecture_images_folder, image_filename)
                    pil_image.save(image_path)

                    relative_path = f"uploads/extracted/{lecture_id}/{image_filename}"
                    image_paths.append({
                        'path': relative_path,
                        'page': page_num + 1
                    })

                except Exception as e:
                    print(f"Error converting page {page_num + 1} to image: {e}")

    combined_text = "\n\n".join(all_text)
    return combined_text, image_paths


def extract_text_only(pdf_path):
    """Extract only text from a PDF file."""
    all_text = []

    with pdfplumber.open(pdf_path) as pdf:
        for page_num, page in enumerate(pdf.pages):
            text = page.extract_text()
            if text and text.strip():
                all_text.append(f"--- Page {page_num + 1} ---\n{text}")

    return "\n\n".join(all_text)
